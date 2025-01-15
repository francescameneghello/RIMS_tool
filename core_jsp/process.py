import simpy
from role_simulator import RoleSimulator
import math
import json
from parameters import Parameters
from datetime import timedelta
from call_LSTM import Predictor
import torch
import pickle
import joblib
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from keras_preprocessing.sequence import pad_sequences

def custom_sigma_activation(x):
    return torch.nn.functional.elu(x) + 1


# Define the LSTM-based model
class CustomModel(nn.Module):
    def __init__(self, num_unique_act_res, embedding_size, window_size, feature_dim, lstm_size):
        super(CustomModel, self).__init__()

        self.embedding = nn.Embedding(num_embeddings=num_unique_act_res, embedding_dim=embedding_size)
        self.lstm = nn.LSTM(input_size=embedding_size + feature_dim, hidden_size=lstm_size, batch_first=True,
                            num_layers=2, dropout=0.2)
        self.mu_layer = nn.Linear(lstm_size, 1)
        self.sigma_layer = nn.Linear(lstm_size, 1)

    def forward(self, act_res, numerical):
        embedded = self.embedding(act_res)
        concatenated = torch.cat((embedded, numerical), dim=2)
        lstm_out, _ = self.lstm(concatenated)
        lstm_out_last = lstm_out[:, -1, :]

        mu = self.mu_layer(lstm_out_last)
        sigma = custom_sigma_activation(self.sigma_layer(lstm_out_last))
        return mu, sigma


# Adjust CustomDataset to handle two targets: 'mu' and 'sigma'
class CustomDataset(Dataset):
    def __init__(self, act_res, numerical, mu_targets, sigma_targets, original_indices):
        self.act_res = act_res
        self.numerical = numerical
        self.mu_targets = mu_targets
        self.sigma_targets = sigma_targets
        self.original_indices = original_indices

    def __len__(self):
        return len(self.mu_targets)

    def __getitem__(self, idx):
        return self.act_res[idx], self.numerical[idx], self.mu_targets[idx], self.sigma_targets[idx], self.original_indices[idx]

class SimulationProcess(object):

    def __init__(self, env: simpy.Environment, params: Parameters, NAME_EXP= None):
        self._env = env
        self._params = params
        #self._date_start = params.START_SIMULATION
        self._resources = self.define_single_machines()
        self._intervals_resources = self._params.CALENDARS
        self._resource_events = self._define_resource_events(env)
        self._resource_trace = simpy.Resource(env, math.inf)
        #self._am_parallel = []

        #self.predictor = Predictor(self._params)
        #self.predictor.predict()
        #self.load_lstm()
        self.NAME_EXP = NAME_EXP
        #self.load_simulation_setting()
        #self.loaded_model_reg = joblib.load('/Users/francescameneghello/Desktop/multioutput_model_all.pkl')

    def load_simulation_setting(self):
        #json_path = '/Users/francescameneghello/Documents/GitHub/RIMS_tool/core_jsp/example/new_experiments/real_LSTM/simulation_settings_test_dfci_' + self.NAME_EXP + '_2022_cal_actuq3_1.json'
        json_path = '/Users/francescameneghello/Documents/GitHub/Job_Shop_Scheduling_Benchmark_Environments_and_Instances/LSTM/original/' + self.NAME_EXP + '_cal_actual.json'
        with open(json_path, "r") as f:
            self._simulation_parameters = json.load(f)

    def set_simulation_parameters(self, caseid, pos_seq, mean, sigma):
        new_time = [mean, sigma]
        self._simulation_parameters["jobs"][str(caseid)]["times"][pos_seq] = new_time
        self.write_simulation_parameter()

    def write_simulation_parameter(self):
        path = '/Users/francescameneghello/Documents/GitHub/Job_Shop_Scheduling_Benchmark_Environments_and_Instances/LSTM/prediction/prediction_' + self.NAME_EXP + '_cal_actual.json'
        with open(path, "w") as json_file:
            json.dump(self._simulation_parameters, json_file, indent=2)
        #print('Write file', path)


    def load_lstm(self):
        with open("/Users/francescameneghello/Documents/GitHub/LSTM_clear/MY_MODEL/metadata_with_sigma_mu_all.pkl", "rb") as f:
            metadata = pickle.load(f)

        self.WINDOW_SIZE = metadata["WINDOW_SIZE"]
        self.EMBEDDING_SIZE = metadata["EMBEDDING_SIZE"]
        self.FEATURE_COLUMNS = metadata["FEATURE_COLUMNS"]
        self.idx_to_act_res = metadata["idx_to_act_res"]
        self.act_res_to_idx = metadata["act_res_to_idx"]

        self.num_unique_act_res = len(self.act_res_to_idx)

        # Load model
        self.model = CustomModel(self.num_unique_act_res, self.EMBEDDING_SIZE, self.WINDOW_SIZE, len(self.FEATURE_COLUMNS), lstm_size=100)
        self.model.load_state_dict(torch.load("/Users/francescameneghello/Documents/GitHub/LSTM_clear/MY_MODEL/lstm_mae_model_with_sigma_mu_all.pth"))
        self.model.eval()

    def define_dependent_processing_time_jsp(self, cid, transition, time, res):
        return self.predictor.processing_time_distribution(cid, transition, time, res)
        #return self.predictor.processing_time(cid, transition, time, res)

    def get_waiting_time_calendar(self, machine, time, duration):
        intervals_m = self._intervals_resources[machine]
        calendar_time = False
        min_start = 0
        for start, stop in intervals_m:
            if start <= time <= stop:
                calendar_time = True
            if time < start and min_start == 0:
                min_start = start
        wait = 0 if calendar_time or (min_start-time) < 0 else (min_start-time)
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
            if self._params.SCHEDULE and res in self._params.SCHEDULE:
                res_simpy = RoleSimulator(self._env, res, self._params.CAPACITY[res], calendar, self._params.SCHEDULE[res])
            else:
                res_simpy = RoleSimulator(self._env, res, self._params.CAPACITY[res], calendar, n_jobs=self._params.N_JOBS)
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
        if str(task) in self._params.INDEX_AC:
            resource_event = self._resource_events[str(task)]
        else:
            resource_event = self._resource_events['Start']
        return resource_event

    def _get_resource_trace(self):
        return self._resource_trace

    def _define_resource_events(self, env):
        resources = dict()
        for key in self._params.INDEX_AC:
            resources[key] = simpy.Resource(env, math.inf)
        return resources

    def _set_single_resource(self, resource_task):
        return self._resources[resource_task]._get_resources_name()

    def _release_single_resource(self, role, resource):
        self._resources[role]._release_resource_name(resource)