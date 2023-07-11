from datetime import timedelta
import simpy
import pm4py
import random
from checking_process import SimulationProcess
from pm4py.objects.petri_net import semantics
from event_parallel import Token_parallel
from simpy.events import AnyOf, AllOf, Event
import numpy as np


class InterTriggerTimer(object):

    def __init__(self, params):
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


    def set_distribution_arrival(self, params):
        self.name_distribution = params['name']
        del params['type']
        del params['name']
        self.params = params


    def get_next_arrival(self):
        parameters = list(self.params.values())
        return getattr(np.random, self.name_distribution)(parameters, size=1)[0]

