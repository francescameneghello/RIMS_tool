
import pandas as pd
from run_simulation import main
import math
import numpy as np

import json
import time

def define_job_problem(path, type):
    TASKS = {}
    MACHINES = []
    with open(path) as file:
        data = json.load(file)
        jobs = data['jobs']
        MACHINES = data['machines']
        SCHEDULES = data['solutions']
        for job, details in jobs.items():
            if type == 'fsjp':
                last = data["n_solutions"] - 1
                machine_seq_solution = data['solutions'][last]['machine_seq']
            machine_seq = details["machine_seq"]
            times = details["times"]

            for i, machine in enumerate(machine_seq):
                mean, std = times[i]
                if i == 0:
                    prec = None
                else:
                    prec = (job, machine_seq[i - 1])

                TASKS[(job, machine)] = {
                    "mean": mean,
                    "std": math.sqrt(float(std)),
                    "prec": prec
                }
    return TASKS, MACHINES, SCHEDULES


def simulate_schedule(s, N, MACHINES, path, D_start=None):
    makespan_simulation = main(s, N, path, D_start)
    return makespan_simulation


def define_Q3(n_activities, path):
    TASK, MACHINES, SCHEDULES = define_job_problem(path, type)
    length_path, stds_list = simulate_schedule(None, 1000, MACHINES, path)
    stds_2 = [s*s for s in stds_list]
    Q3 = (1.645/math.sqrt(n_activities))*(math.sqrt(np.mean(stds_2))/np.mean(stds_list))
    return Q3


CRITICAL_PATH_DISCOVERY = False
start_time = time.time()
path = '/Users/francescameneghello/Documents/GitHub/RIMS_tool/core_jsp/example'
NAME_EXP = 'abz5_cp_solver_0.5_q3'
final_path = path + '/new_experiments/simulation_settings_'+NAME_EXP+'.json'

########## CALENDAR ################
#final_path = path + "/new_experiments/simulation_settings_abz6_cp_solver_0.1_q3_CAL.json"

N = 1
TASK, MACHINES, SCHEDULES = define_job_problem(final_path, type)  #### read the beanchmarks and define json file to find the solution with CP

results_iteration = {}

if not CRITICAL_PATH_DISCOVERY:
    makespans = []
    s = 0
    number_best = 0
    D_initial = SCHEDULES[str(s)]["makespan"]
    s_star = SCHEDULES[str(s)]["solution"]
    D_star = math.inf
    search = True
    while s < len(SCHEDULES):
        schedule = SCHEDULES[str(s)]["solution"]
        makespans = simulate_schedule(schedule, N, MACHINES, final_path)  ## D'
        D_alpha = np.percentile(makespans, 95)
        print('Solution n ', s, 'D_alpha', D_alpha)
        print("Mean of makespans", np.mean(makespans), "Std of makespans", np.std(makespans))
        print("********************************************************************************")
        results_iteration[s] = {"D_alpha": D_alpha, "mean": np.mean(makespans), "std": np.std(makespans)}

        if D_alpha < D_star:
            number_best = s
            s_star = SCHEDULES[str(s)]["solution"]
            D_star = D_alpha

        s += 1
        if s < len(SCHEDULES):
            schedule = SCHEDULES[str(s)]["solution"]

        print('Best solution', D_star, number_best)
        schedule = SCHEDULES[str(number_best)]["solution"]
        print(schedule)

        print(results_iteration)
        write_path = path + '/results/results_simulation_' + NAME_EXP +'.json'
        with open(write_path, 'w') as outfile:
            json.dump(results_iteration, outfile, indent=2)
else:
    Q3 = define_Q3(10, final_path)
    print('---------------- Q3: ', Q3, ' ----------------------')


