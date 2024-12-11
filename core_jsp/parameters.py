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
