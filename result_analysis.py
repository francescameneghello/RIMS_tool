import glob
import os
import pandas as pd
import json


class Result(object):

    def __init__(self, folder, params):
        self._folder = folder
        self._all_file = glob.glob("{}/{}/simulated_log_*".format(os.getcwd(), self._folder))
        self._params = params

    def analysis_log(self, sim):
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

    def analyse(self, type='single'):
        if type == 'single':
            self.analysis_log(self._all_file[0])
        else:
            for file in self._all_file:
                self.analysis_log(file)
