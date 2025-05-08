"""
    Class for reading simulation parameters
"""
import json
import math
import os
from datetime import datetime


class Parameters(object):

    def __init__(self, path_parameters: str, schedule):
        self.PATH_PARAMETERS = path_parameters
        """PATH_PARAMETERS: path of json file for others parameters. """
        self.read_metadata_file_jsp()
        self.SIM_TIME = 31536000
        self.SCHEDULE = schedule

        self.MODEL_PATH_PROCESSING = '/Users/francescameneghello/Documents/GitHub/RIMS_tool/core_jsp/example/new_experiments/real_LSTM/lstm_model_files/hospital_JAN_dpiapr.h5'
        self.SCALER = '/Users/francescameneghello/Documents/GitHub/RIMS_tool/core_jsp/example/new_experiments/real_LSTM/lstm_model_files/hospital_JAN_diapr_scaler.pkl'
        self.INTER_SCALER = '/Users/francescameneghello/Documents/GitHub/RIMS_tool/core_jsp/example/new_experiments/real_LSTM/lstm_model_files/hospital_JAN_diapr_inter_scaler.pkl'
        self.END_INTER_SCALER = '/Users/francescameneghello/Documents/GitHub/RIMS_tool/core_jsp/example/new_experiments/real_LSTM/lstm_model_files/hospital_JAN_diapr_end_inter_scaler.pkl'
        self.METADATA = '/Users/francescameneghello/Documents/GitHub/RIMS_tool/core_jsp/example/new_experiments/real_LSTM/lstm_model_files/hospital_JAN_diapr_meta.json'
        self.read_metadata_file()

    def read_metadata_file_jsp(self):
        '''
                Method to read parameters from json file, see *main page* to get the whole list of simulation parameters.
                '''
        if os.path.exists(self.PATH_PARAMETERS):
            with open(self.PATH_PARAMETERS) as file:
                data = json.load(file)
                self.MACHINES = data['machines']
                self.N_JOBS = len(data["jobs"])
                self.JOBS = data["jobs"]
                self.JOBS_FIXED = data["fixed_duration"] if "fixed_duration" in data else None
                self.N_TO_MACHINES = data["n_to_machines"] if "n_to_machine" in data else None
                self.MACHINES_TO_N = data["machines_to_n"] if "machines_to_n" in data else None
                self.START = datetime.strptime(data["start_timestamp"], '%Y-%m-%d %H:%M:%S')

                #### calendars
                if "calendars_res" in data:
                    self.CALENDARS = data["calendars_res"]
                else:
                    self.CALENDARS = {}

                #### capacity
                if "machines_capacity" in data:
                    self.CAPACITY = data["machines_capacity"]
                else:
                    self.CAPACITY = {i: 1 for i in self.MACHINES}

    def read_metadata_file(self):
        if os.path.exists(self.METADATA):
            with open(self.METADATA) as file:
                data = json.load(file)
                self.INDEX_AC = data['ac_index']
                self.INDEX_USR = data["usr_index"]
                #roles_table = data['roles_table']
                #self.ROLE_ACTIVITY = dict()
                #for elem in roles_table:
                #    self.ROLE_ACTIVITY[elem['task']] = elem['role']

                #self.INDEX_ROLE = {'SYSTEM': 0}
                #self.ROLE_CAPACITY = {'SYSTEM': [1000, {'days': [0, 1, 2, 3, 4, 5, 6], 'hour_min': 0, 'hour_max': 23}]}
                #roles = data['roles']
                #for idx, key in enumerate(roles):
                #    self.INDEX_ROLE[key] = idx
                #    self.ROLE_CAPACITY[key] = [len(roles[key]),
                #                               {'days': [0, 1, 2, 3, 4, 5, 6], 'hour_min': 0, 'hour_max': 23}]