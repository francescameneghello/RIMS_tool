
import pandas as pd
from run_simulation import main
import math
import numpy as np

import json
import time

def define_job_problem():
    TASKS = {}
    MACHINES = []
    path = '/Users/francescameneghello/Documents/GitHub/RIMS_tool/core_jsp/example/simulation_settings.json'
    with open(path) as file:
        data = json.load(file)
        jobs = data['jobs']
        MACHINES = data['machines']
        SCHEDULES = data['solutions']
        for job, details in jobs.items():
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
                    "std": math.sqrt(std),
                    "prec": prec
                }
        return TASKS, MACHINES, SCHEDULES

def simulate_schedule(s, N, MACHINES, D_start=None):
    '''if s:
        schedule = pd.DataFrame(s)
        #print('\nSchedule by Machine')
        schedule = schedule.sort_values(by=['Machine', 'Start'])
        schedule_sim = {m: [] for m in MACHINES}
        for index, row in schedule.iterrows():
            schedule_sim[row['Machine']].append(row['Job'])
        print(schedule_sim)
    else:
        schedule_sim = None'''
    makespan_simulation = main(schedule, N, D_start)
    return makespan_simulation


start_time = time.time()
N = 1000
TASK, MACHINES, SCHEDULES = define_job_problem()
makespans = []
s = len(SCHEDULES)-1
search = True
while search and s > 0:
    schedule = SCHEDULES[str(s)]["solution"]
    D_star = SCHEDULES[str(s)]["makespan"]
    makespans = simulate_schedule(schedule, N, MACHINES, D_star)
    prob = [dur <= D_star for dur in makespans]
    prob = sum(prob)/len(prob)
    if prob >= 0.95:
        print("**************************************** END ****************************************")
        print('Find probabilistic solution with prob ', prob, 'and D_star ', D_star)
        print("--- %s seconds ---" % (time.time() - start_time))
        search = False
    else:
        print('Solution with prob ', prob, 'and makespan ', D_star)
        print('**************************************** GO TO NEXT SOLUTION ****************************************')
        s -= 1
