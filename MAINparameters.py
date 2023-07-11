'''
Principal parameters to run the process

DA AGGIUNGERE: configurazione risorse, tempi per ogni attivita'
'''
import json
import os
from datetime import datetime


class Parameters(object):

    def __init__(self, path_parameters, traces):
        self.SIM_TIME = 1460*36000000000000000  # 10 day
        #self.ARRIVALS = pd.read_csv(self.NAME_EXP + '/arrivals/iarr' + str(iterations) + '.csv', sep=',')
        self.START_SIMULATION = datetime.now()
        self.TRACES = traces
        self.PATH_PARAMTERS = path_parameters
        self.read_metadata_file()

    def read_metadata_file(self):
        if os.path.exists(self.PATH_PARAMTERS):
            with open(self.PATH_PARAMTERS) as file:
                data = json.load(file)
                roles_table = data['roles_table']
                self.ACTIVITIES = data['activities']
                self.ROLE_ACTIVITY = dict()
                for elem in roles_table:
                    self.ROLE_ACTIVITY[elem['task']] = elem['role']

                self.INDEX_ROLE = {'SYSTEM': 0}
                self.ROLE_CAPACITY = {'SYSTEM': [1000, {'days': [0, 1, 2, 3, 4, 5, 6], 'hour_min': 0, 'hour_max': 23}]}
                roles = data['roles']
                for idx, key in enumerate(roles):
                    self.INDEX_ROLE[key] = idx
                    self.ROLE_CAPACITY[key] = [len(roles[key]), {'days': [0, 1, 2, 3, 4, 5, 6], 'hour_min': 0, 'hour_max': 23}]
        else:
            raise ValueError('Parameter file does not exist')
