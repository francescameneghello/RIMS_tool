'''
Class to generate the output json file "result_simulated_log(experiment_name)" with some analysis on the simulated log.
Example of analysis:

| Name       | Description  |
|:------------:|:-------------------------- |
| total_events | Total events in the log |
| total_traces | Total traces in the log |
| *A*_frequency | Total occurrences of activity *A* in the log |
| total_duration | Total duration of simulation |
| start_date | Start date of the simulation |
| end_date | End date of the simulation |

'''


import glob
import os
import pandas as pd
import json
from parameters import Parameters
import pm4py
from datetime import datetime, timedelta


class Result(object):

    def __init__(self, folder: str, params: Parameters):
        self._folder = folder
        self._all_file = glob.glob("{}/output/{}/simulated_log_*.csv".format(os.getcwd(), self._folder))
        self._params = params

    def analysis_log(self, sim):
        '''
        Method to compute the analysis over the single log
        '''
        analysis = dict()
        sim_df = pd.read_csv(sim, sep=',')
        analysis.update(self.general_analysis(sim_df))

        for role in self._params.ROLE_CAPACITY.keys():
            if role != 'TRIGGER_TIMER':
                analysis[role] = {"total": len(sim_df[sim_df['role'] == role])}
                for resource in self._params.ROLE_CAPACITY[role][0]:
                    analysis[role][resource] = len(sim_df[sim_df['resource'] == resource])

        self._write_json(analysis, sim)

    def general_analysis(self, sim_df):
        analysis = dict()
        analysis['total_events'] = len(sim_df)
        analysis['total_traces'] = len(set(sim_df['id_case']))
        for act in self._params.PROCESSING_TIME.keys():
            analysis[act + "_frequency"] = len(sim_df[sim_df['activity'] == act])
        try:
            start = datetime.strptime(sim_df['start_time'].iloc[0], '%Y-%m-%d %H:%M:%S.%f')
        except:
            start = datetime.strptime(sim_df['start_time'].iloc[0], '%Y-%m-%d %H:%M:%S')
        try:
            end = datetime.strptime(sim_df['start_time'].iloc[0], '%Y-%m-%d %H:%M:%S.%f')
        except:
            end = datetime.strptime(sim_df['start_time'].iloc[0], '%Y-%m-%d %H:%M:%S')
        seconds = (end - start).total_seconds()
        analysis['duration'] = str(timedelta(seconds=seconds))
        analysis['start_simulation'] = sim_df['start_time'].iloc[0]
        analysis['end_simulation'] = sim_df['end_time'].iloc[-1]

        return analysis

    def _analyse(self, type='single'):
        if type == 'single':
            self.analysis_log(self._all_file[0])
            self._csv_to_xes(self._all_file[0])
        else:
            for file in self._all_file:
                self.analysis_log(file)

    def _write_json(self, analysis, sim):
        try:
            filename = 'output/{}/result_{}.json'.format(self._folder, os.path.splitext(os.path.basename(sim))[0])
            with open(filename, 'w') as json_file:
                json.dump(analysis, json_file, indent=len(analysis))
        except Exception as e:
            print(f"Error: {e}")

    def _csv_to_xes(self, sim):
        sim_df = pd.read_csv(sim, sep=',')
        sim_df = pm4py.format_dataframe(sim_df, case_id='id_case', activity_key='activity',
                                           timestamp_key='end_time')
        event_log = pm4py.convert_to_event_log(sim_df)
        pm4py.write_xes(event_log, 'output/{}/{}.xes'.format(self._folder, os.path.splitext(os.path.basename(sim))[0]))
