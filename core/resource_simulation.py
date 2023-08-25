'''
Class to manage resources and comply with their calendars.

The calendar follows the following format:
calendar = {'days' = [0, 1, 2, 3, 4], 'hour_min' = 9, 'hour_max' = 17]}
'''
from datetime import datetime, timedelta
import simpy
import random
#capacity: float | list


class ResourceSim(object):

    def __init__(self, env: simpy.Environment, name: str, capacity, calendar: dict, start: datetime):
        self._env = env
        self._name = name
        self._resources_name = capacity
        self._capacity = capacity if type(capacity) == float else len(capacity)
        self._calendar = calendar
        self._resource_simpy = simpy.Resource(env, self._capacity)
        self._start = start
        self.queue = []

    def get_name(self):
        return self._name

    def get_capacity(self):
        return self._capacity

    def get_resource(self):
        return self._resource_simpy

    def get_calendar(self):
        return self._calendar

    def release(self, request):
        self._resource_simpy.release(request)

    def request(self):
        self.queue.append(self._resource_simpy.queue)
        return self._resource_simpy.request()

    def get_queue(self):
        return self.queue

    def check_day_work(self, timestamp):
        return True if (timestamp.weekday() in self._calendar['days']) else False

    def check_hour_work(self, timestamp):
        return True if (self._calendar['hour_min'] <= timestamp.hour < self._calendar['hour_max']) else False

    def define_stop_weekend(self, timestamp):
        ### se non e' in un giorno lavorativo o e' venerdi sera
        monday = 7 - timestamp.weekday()
        new_start = timestamp.replace(hour=self._calendar['hour_min'], minute=0, second=0) + timedelta(days=monday)
        return (new_start-timestamp).total_seconds()

    def define_stop_week(self, timestamp):
        if timestamp.hour < self._calendar['hour_min']:
            stop = timestamp.replace(hour=self._calendar['hour_min'], minute=0, second=0) - timestamp
        else:
            new_day = timestamp.replace(hour=self._calendar['hour_min'], minute=0, second=0) + timedelta(days=1)
            stop = new_day - timestamp
        return stop.total_seconds()

    def to_time_schedule(self, timestamp):
        ## check if day and hour is correct, otherwise fix it
        if not self.check_day_work(timestamp):
            stop = self.define_stop_weekend(timestamp)
        elif not self.check_hour_work(timestamp):
            stop = self.define_stop_week(timestamp)
        else:
            stop = 0
        return int(stop)

    def split_week(self, timestamp, duration):
        ## return before, stop, after
        before = (timestamp.replace(hour=self._calendar['hour_max'], minute=0, second=0) - timestamp).seconds
        stop = self.define_stop_week(timestamp.replace(hour=self._calendar['hour_max'], minute=0, second=0))
        if not self.check_day_work(timestamp + timedelta(seconds=before) + timedelta(seconds=stop)):
            stop += self.define_stop_weekend(timestamp + timedelta(seconds=before+stop))
        after = duration - before
        return before, stop, after

    def split_weekend(self, timestamp, duration):
        ## return before, stop, after
        before = (timestamp.replace(hour=self._calendar['hour_max'], minute=0, second=0) - timestamp).total_seconds
        stop = self.define_stop_weekend(timestamp.replace(hour=self._calendar['hour_max'], minute=0, second=0))
        after = duration - before
        return before, stop, after

    def check_duration(self, timestamp, duration):
        ## controllo se dentro settimana lavorativa
        time_to_complete = timestamp + timedelta(seconds=duration)
        before = duration ## se non ci sono problemi esegue tutto
        stop = after = 0
        if not self.check_hour_work(time_to_complete):
            if self.check_day_work(time_to_complete) in self._calendar['days']:
                before, stop, after = self.split_week(timestamp, duration) ## esegue fine hour_max e il resto il giorno dopo
            else:
                before, stop, after = self.split_weekend(timestamp, duration) ## esegue fine hour_max e il resto lunedi'
        return before, stop, after

    def define_timework(self, timestamp, duration):
        stop_pre = self.to_time_schedule(timestamp)
        before, stop, after = self.check_duration(timestamp + timedelta(seconds=stop_pre), duration)
        return stop_pre, before + stop + after

    def _get_resources_name(self):
        choiced = self._resources_name[0]
        self._resources_name.remove(choiced)
        return choiced

    def _release_resource_name(self, resource):
        self._resources_name.append(resource)