"""
Class to manage the arrivals times of tokes in the process.
"""

import numpy as np
from datetime import datetime, timedelta
from parameters import Parameters
from process import SimulationProcess
import custom_function as custom


class InterTriggerTimer(object):

    def __init__(self, params: Parameters, process: SimulationProcess, start: datetime):
        self._process = process
        self._start_time = start
        self._type = params.INTER_TRIGGER['type']
        self._previous = None
        if self._type == 'distribution':
            """Define the distribution of token arrivals from specified in the file json"""
            self.name_distribution = params.INTER_TRIGGER['name']
            self.params = params.INTER_TRIGGER['parameters']

    def get_next_arrival(self, env, case):
        """Generate a new arrival from the distribution and check if the new token arrival is inside calendar,
        otherwise wait for a suitable time."""
        next = 0
        if self._type == 'distribution':
            resource = self._process._get_resource('TRIGGER_TIMER')
            arrival = getattr(np.random, self.name_distribution)(**self.params, size=1)[0]
            if resource._get_calendar():
                stop = resource.to_time_schedule(self._start_time + timedelta(seconds=env.now + arrival))
                next = stop + arrival
            else:
                next = arrival
        elif self._type == 'custom':
            next = self.custom_arrival(case, self._previous)
        else:
            raise ValueError('ERROR: Invalid arrival times generator')
        self._previous = self._start_time + timedelta(seconds=env.now + next)
        return next

    def custom_arrival(self, case, previous):
        """
        Call to the custom functions in the file custom_function.py.
        """
        return custom.custom_arrivals_time(case, previous)

