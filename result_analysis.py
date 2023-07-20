'''
Class to generate the output json file "result_simulated_log(experiment_name)" with some analysis on the simulated log.
Example of analysis:

| Name       | Description  |
|------------|--------------------------
| total_events | Total events in the log |
| total_traces | Total traces in the log |
| *A*_frequency | Total occurrences of activity *A* in the log |


'''


import glob
import os
import pandas as pd
import json
from MAINparameters import Parameters


class Result(object):

    def __init__(self, folder: str, params: Parameters):
        self._folder = folder
        self._all_file = glob.glob("{}/{}/simulated_log_*".format(os.getcwd(), self._folder))
        self._params = params

    def analysis_log(self, sim):
        '''
        Method to compute the analysis over the single log
        '''
        analysis = dict()
        sim_df = pd.read_csv(sim, sep=',')
        analysis['total_events'] = len(sim)
        analysis['total_traces'] = len(set(sim_df['id_case']))
        for act in self._params.ACTIVITIES.values():
            analysis[act + "_frequency"] = len(sim_df[sim_df['activity'] == act])
        print(analysis)
        try:
            filename = '{}/result_{}.json'.format(self._folder, os.path.splitext(os.path.basename(sim))[0])
            with open(filename, 'w') as json_file:
                json.dump(analysis, json_file, indent=len(analysis))
        except Exception as e:
            print(f"Error: {e}")

    def _analyse(self, type='single'):
        if type == 'single':
            self.analysis_log(self._all_file[0])
        else:
            for file in self._all_file:
                self.analysis_log(file)
