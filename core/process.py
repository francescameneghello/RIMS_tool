'''
Class to manage the resources shared by all the traces in the process.

(Aggiungere immagine delle risorse utilizzate: 1) quelle dei ruoli e delle sigole risorse
2) risorsa fittizzia per tracce e wip 2) risorsa fittizzia per attivita' e wip_activity
'''
import simpy
from resource import Resource
import math
from parameters import Parameters


class SimulationProcess(object):

    def __init__(self, env: simpy.Environment, params: Parameters):
        self._env = env
        self._params = params
        self._date_start = params.START_SIMULATION
        self._resource = self.define_single_role()
        self._resource_events = self._define_resource_events(env)
        self._resource_trace = simpy.Resource(env, math.inf)
        self._am_parallel = []

    def define_single_role(self):
        """
        Definition of a *Resource* object for each role in the process.
        """
        set_resource = list(self._params.ROLE_CAPACITY.keys())
        dict_role = dict()
        for res in set_resource:
            res_simpy = Resource(self._env, res, self._params.ROLE_CAPACITY[res][0], self._params.ROLE_CAPACITY[res][1], self._date_start)
            dict_role[res] = res_simpy
        print(dict_role)
        return dict_role

    def define_single_resource(self, role):
        dict_resources = dict()
        for resource in role[-1]:
            res_simpy = Resource(self._env, resource, 1, role[1],
                                 self._date_start)
            dict_resources[resource] = res_simpy
        return dict_resources

    def get_occupations_single_resource(self, resource):
        """
        Method to retrieve the occupation of resource as intercase feature:
        $\\frac{resources \: occupated \: in \:role}{total\:resources\:in\:role}$.
        """
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
