from branch_bound_deterministic import BBdeterministic
import pandas as pd
from run_simulation import main
import math
import numpy as np

import json

##### JOB SHOP SCHEDULING PROBLEM

'''TASKS = {
    ('job1', 'machine_1'): {'mean': 50, "std": 4, 'prec': None},
    ('job1', 'machine_2'): {'mean': 60, "std": 10, 'prec': ('job1', 'machine_1')},
    ('job1', 'machine_3'): {'mean': 14, "std": 1, 'prec': ('job1', 'machine_2')},
    ('job2', 'machine_2'): {'mean': 75, "std": 20, 'prec': ('job2', None)},
    ('job2', 'machine_1'): {'mean': 45, "std": 6, 'prec': ('job2', 'machine_2')},
    ('job2', 'machine_4'): {'mean': 35, "std": 17, 'prec': ('job2', 'machine_1')},
    ('job2', 'machine_3'): {'mean': 25, "std": 9, 'prec': ('job2', 'machine_4')},
    ('job3', 'machine_1'): {'mean': 50, "std": 10, 'prec': None},
    ('job3', 'machine_2'): {'mean': 70, "std": 12, 'prec': ('job3', 'machine_1')},
    ('job3', 'machine_4'): {'mean': 20, "std": 3, 'prec': ('job3', 'machine_2')},
}'''

#MACHINES = ['machine_1', 'machine_2', 'machine_3', 'machine_4']

def define_job_problem():
    TASKS = {}
    MACHINES = []
    path = '/Users/francescameneghello/Documents/GitHub/RIMS_tool/core_jsp/example/input_simple_example_distribution.json'
    with open(path) as file:
        data = json.load(file)
        jobs = data['jobs']
        MACHINES = data['machines']
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
        return TASKS, MACHINES

def simulate_schedule(s, N, MACHINES, D_start=None):
    if s:
        schedule = pd.DataFrame(s)
        #print('\nSchedule by Machine')
        schedule = schedule.sort_values(by=['Machine', 'Start'])
        schedule_sim = {m: [] for m in MACHINES}
        for index, row in schedule.iterrows():
            schedule_sim[row['Machine']].append(row['Job'])
        print(schedule_sim)
    else:
        schedule_sim = None
    makespan_simulation = main(schedule_sim, N, D_start)
    return makespan_simulation


def CP_DQL():
    Q = 1.25
    Q_star = 1.25
    q_dec = 0.05
    N = 5000
    #### first iteration
    TASKS, MACHINES = define_job_problem()
    BB = BBdeterministic(TASKS)
    s_star, D_star = BB.jobshop(Q)
    D_sim = simulate_schedule(s_star, N, MACHINES, D_star)
    Q = round(Q - q_dec, 3)
    #print('######### FIRST ITERATION #########')
    #print('D_star', D_star, 'D_simulate', D_sim, 'Q', Q)
    while Q >= 0:
        s, D = BB.jobshop(Q)
        makespan_alpha = simulate_schedule(s, N, MACHINES, D_star)
        if makespan_alpha:
            s_star = s
            D_star = D
            Q_star = Q
            print('new makespan_alpha', makespan_alpha, 'Q', Q_star)
        #print('######### ITERATION #########')
        #print('Q', Q, 'D_star', D_star)
        Q = round(Q-q_dec, 3)

    print('BEST Q', Q_star)


def CP_BetterSolution(Q):
    N = 5000
    #### first iteration
    TASKS, MACHINES = define_job_problem()
    BB = BBdeterministic(TASKS)
    s_star, D_star = BB.jobshop(Q)
    D_sim = simulate_schedule(s_star, N, MACHINES, D_star)
    print('Makespan simulated', D_sim)
    print('Solution', s_star)
    print('Deterministic Makespan', D_star)


def define_Q3(n_activities):
    TASKS, MACHINES = define_job_problem()
    length_path, stds_list = simulate_schedule(None, 1000, MACHINES)
    stds_2 = [s*s for s in stds_list]
    Q3 = (1.645/math.sqrt(n_activities))*(math.sqrt(np.mean(stds_2))/np.mean(stds_list))
    return Q3

n_activities = 3
Q1 = 1.645/(math.sqrt(n_activities))
print('---------------- Q1: ', Q1, ' ----------------------')
CP_BetterSolution(0)
'''#Q3 = define_Q3(n_activities)
Q3 = 0.49725478658755135
print('---------------- Q3: ', Q3, ' ----------------------')
CP_BetterSolution(Q3)
Q2 = (Q1 + Q3)/2
print('---------------- Q2: ', Q2, ' ----------------------')
CP_BetterSolution(Q2)

#simulate_schedule(s=None, N=1)'''

#define_Q3(10)

#CP_DQL()
