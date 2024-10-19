import simpy
from role_simulator import RoleSimulator
import math
from parameters import Parameters
from datetime import timedelta

class SimulationProcess(object):

    def __init__(self, env: simpy.Environment, params: Parameters):
        self._env = env
        self._params = params
        #self._date_start = params.START_SIMULATION
        self._resources = self.define_single_machines()
        self._intervals_resources = self._params.CALENDARS
        #self._resource_events = self._define_resource_events(env)
        #self._resource_trace = simpy.Resource(env, math.inf)
        #self._am_parallel = []

    def get_waiting_time_calendar(self, machine, time):
        intervals_m = self._intervals_resources[machine]
        calendar_time = False
        min_start = 0
        for start, stop in intervals_m:
            if start <= time <= stop:
                calendar_time = True
            if time < start and min_start == 0:
                min_start = start
        wait = 0 if calendar_time or (min_start-time)<0 else (min_start-time)
        return wait

    def define_single_machines(self):
        """
        Definition of a *RoleSimulator* object for each role in the process.
        """
        set_resource = self._params.MACHINES
        dict_role = dict()
        calendar = {'days': [0, 1, 2, 3, 4, 5, 6],
                    'hour_min': 0,
                    'hour_max': 23}
        for res in set_resource:
            if self._params.SCHEDULE:
                res_simpy = RoleSimulator(self._env, res, [1], calendar, self._params.SCHEDULE[res])
            else:
                res_simpy = RoleSimulator(self._env, res, [1], calendar)
            dict_role[res] = res_simpy
        return dict_role

    def get_occupations_single_role(self, resource):
        """
        Method to retrieve the specified role occupancy in percentage, as an intercase feature:
        $\\frac{resources \: occupated \: in \:role}{total\:resources\:in\:role}$.
        """
        occup = self._resources[resource]._get_resource().count / self._resources[resource]._capacity
        return round(occup, 2)

    def get_occupations_all_role(self):
        """
        Method to retrieve the occupancy in percentage of all roles, as an intercase feature.
        """
        list_occupations = []
        for res in self._resources:
            if res != 'TRIGGER_TIMER':
                occup = round(self._resources[res]._get_resource().count / self._resources[res]._capacity, 2)
                list_occupations.append(occup)
        return list_occupations

    def _get_resource(self, resource_label):
        return self._resources[resource_label]

    def _get_resource_event(self, task):
        return self._resource_events[task]

    def _get_resource_trace(self):
        return self._resource_trace

    def _define_resource_events(self, env):
        resources = dict()
        for key in self._params.PROCESSING_TIME.keys():
            resources[key] = simpy.Resource(env, math.inf)
        return resources

    def _set_single_resource(self, resource_task):
        return self._resources[resource_task]._get_resources_name()

    def _release_single_resource(self, role, resource):
        self._resources[role]._release_resource_name(resource)