"""
Class to manage the arrivals times of tokes in the process.
"""

import numpy as np
from datetime import datetime, timedelta
from parameters import Parameters
from process import SimulationProcess


class InterTriggerTimer(object):

    def __init__(self, params: Parameters, process: SimulationProcess, start: datetime):
        self._process = process
        self._start_time = start
        self._type = params.INTER_TRIGGER['type']
        if self._type == 'distribution':
            """Define the distribution of token arrivals from specified in the file json"""
            self.name_distribution = params.INTER_TRIGGER['name']
            self.params = params.INTER_TRIGGER['parameters']

    def get_next_arrival(self, env, case):
        """Generate a new arrival from the distribution and check if the new token arrival is inside calendar,
        otherwise wait for a suitable time."""
        if self._type == 'distribution':
            resource = self._process.get_resource('TRIGGER_TIMER')
            parameters = list(self.params.values())
            arrival = getattr(np.random, self.name_distribution)(parameters, size=1)[0]
            if resource.get_calendar():
                stop = resource.to_time_schedule(self._start_time + timedelta(seconds=env.now + arrival))
                return stop + arrival
            else:
                return arrival
        elif self._type == 'custom':
            return self.custom_arrival(case)
        else:
            raise ValueError('ERROR: Invalid arrival times generator')

    def custom_arrival(self, case):
        return 0

