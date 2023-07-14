import numpy as np
from datetime import timedelta

class InterTriggerTimer(object):

    def __init__(self, params, process, start):
        if params['type'] == 'distribution':
            self.set_distribution_arrival(params)
        elif params['type'] == 'predictive':
            ##define methods to call your predictive model
            pass
        elif params['type'] == 'list':
            ##define methods to call the specific arrival time for each token or a particular function
            pass
        else:
            raise ValueError('ERROR: Invalid arrival times generator')
        self.process = process
        self.start_time = start

    def set_distribution_arrival(self, params):
        self.name_distribution = params['name']
        self.params = params['parameters']

    def get_next_arrival(self, env):
        resource = self.process.get_resource('TRIGGER_TIMER')
        parameters = list(self.params.values())
        arrival = getattr(np.random, self.name_distribution)(parameters, size=1)[0] ### genero arrivo
        if resource.get_calendar():
            stop = resource.to_time_schedule(self.start_time + timedelta(seconds=env.now + arrival)) ### check if arrival is inside calendar
            return stop + arrival
        else:
            return arrival

    def define_calendar(self, params):
        print(params['calendar'])
        #Resource(env: simpy.Environment, name: str, capacity: int, calendar: dict, start: datetime)