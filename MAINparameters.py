'''
Principal parameters to run the process

DA AGGIUNGERE: configurazione risorse, tempi per ogni attivita'
'''
import json
import math
import os
from datetime import datetime


class Parameters(object):

    '''
    Define the main parameters of simulation:
        -SIM_TIME: total simulation duration in seconds (at the end of time the simulation will be stopped even if the execution of traces has not been completed)
        -TRACES: number of traces to generate
        -PATH_PARAMTERS: path of json file for others parameters
    '''
    def __init__(self, path_parameters, traces):
        self.SIM_TIME = 86400
        self.TRACES = traces
        self.PATH_PARAMTERS = path_parameters
        self.read_metadata_file()

    def read_metadata_file(self):
        if os.path.exists(self.PATH_PARAMTERS):
            with open(self.PATH_PARAMTERS) as file:
                data = json.load(file)
                roles_table = data['roles_table']
                self.START_SIMULATION = datetime.strptime(data['start_timestamp'], '%Y-%m-%d %H:%M:%S')
                self.ACTIVITIES = data['activities']
                self.PROBABILITY = data['probability']
                self.INTER_TRIGGER = data["interTriggerTimer"]
                self.ROLE_ACTIVITY = dict()
                for elem in roles_table:
                    self.ROLE_ACTIVITY[elem['task']] = elem['role']

                if data['interTriggerTimer']['calendar']:
                    self.ROLE_CAPACITY = {'TRIGGER_TIMER': [math.inf, {'days': data['interTriggerTimer']['calendar']['days'], 'hour_min': data['interTriggerTimer']['calendar']['hour_min'], 'hour_max': data['interTriggerTimer']['calendar']['hour_max']}]}
                else:
                    self.ROLE_CAPACITY = {'TRIGGER_TIMER': [math.inf, []]}

                roles = data['roles']
                for idx, key in enumerate(roles):
                    self.ROLE_CAPACITY[key] = [len(roles[key]), {'days': [0, 1, 2, 3, 4, 5, 6], 'hour_min': 0, 'hour_max': 23}]
        else:
            raise ValueError('Parameter file does not exist')
