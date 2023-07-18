'''
classe process che contiene risorse ed esegue task

'''
import simpy
from resource import Resource
import math
from MAINparameters import Parameters


class SimulationProcess(object):

    def __init__(self, env: simpy.Environment, params: Parameters):
        self._env = env
        self._params = params
        self._date_start = params.START_SIMULATION
        self._resource = self.define_single_resource()
        self._resource_events = self._define_resource_events(env)
        self._resource_trace = simpy.Resource(env, math.inf)
        self._am_parallel = []

    def define_single_resource(self):
        set_resource = list(self._params.ROLE_CAPACITY.keys())
        dict_res = dict()
        for res in set_resource:
            res_simpy = Resource(self._env, res, self._params.ROLE_CAPACITY[res][0], self._params.ROLE_CAPACITY[res][1], self._date_start)
            print(res, res_simpy.capacity)
            dict_res[res] = res_simpy
        return dict_res

    def get_occupations_single_resource(self, resource):
        occup = self._resource[resource].get_resource().count / self._resource[resource].capacity
        return round(occup, 2)

    def get_resource(self, resource_label):
        return self._resource[resource_label]

    def get_resource_event(self, task):
        return self._resource_events[task]

    def get_resource_trace(self):
        return self._resource_trace

    def _define_resource_events(self, env):
        resources = dict()
        for key in self._params.ACTIVITIES.keys():
            resources[key] = simpy.Resource(env, math.inf)
        return resources

    def _set_last_events(self, am):
        for token in am:
            self._am_parallel.append(token)

    def _get_last_events(self):
        return set(self._am_parallel)
