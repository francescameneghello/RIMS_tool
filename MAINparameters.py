"""
    Define the main parameters of simulation:
    * SIM_TIME: total simulation duration in seconds (at the end of time the simulation will be stopped even if the execution of traces has not been completed).

"""
import json
import math
import os
from datetime import datetime


class Parameters(object):

    def __init__(self, path_parameters, traces):
        self.TRACES = traces
        """TRACES: number of traces to generate"""
        self.PATH_PARAMETERS = path_parameters
        """PATH_PARAMETERS: path of json file for others parameters. """
        self.read_metadata_file()

    def read_metadata_file(self):
        if os.path.exists(self.PATH_PARAMETERS):
            with open(self.PATH_PARAMETERS) as file:
                data = json.load(file)
                roles_table = data['roles_table']
                self.START_SIMULATION = datetime.strptime(data['start_timestamp'], '%Y-%m-%d %H:%M:%S')
                self.SIM_TIME = data['duration_simulation']
                self.ACTIVITIES = data['activities']
                self.PROBABILITY = data['probability']
                self.PROCESSING_TIME = data['processing_time']
                self.WAITING_TIME = data['waiting_time'] if 'waiting_time' in data.keys() else []
                self.INTER_TRIGGER = data["interTriggerTimer"]
                self.ROLE_ACTIVITY = dict()
                for elem in roles_table:
                    self.ROLE_ACTIVITY[elem['task']] = elem['role']

                if 'calendar' in data['interTriggerTimer'] and data['interTriggerTimer']['calendar']:
                    self.ROLE_CAPACITY = {'TRIGGER_TIMER': [math.inf, {'days': data['interTriggerTimer']['calendar']['days'], 'hour_min': data['interTriggerTimer']['calendar']['hour_min'], 'hour_max': data['interTriggerTimer']['calendar']['hour_max']}]}
                else:
                    self.ROLE_CAPACITY = {'TRIGGER_TIMER': [math.inf, []]}

                roles = data['roles']
                for idx, key in enumerate(roles):
                    self.ROLE_CAPACITY[key] = [len(roles[key]['resources']), {'days': roles[key]['calendar']['days'], 'hour_min': roles[key]['calendar']['hour_min'], 'hour_max': roles[key]['calendar']['hour_max']}]
        else:
            raise ValueError('Parameter file does not exist')
