from branch_bound_deterministic import BBdeterministic
import pandas as pd
from run_simulation import main

##### JOB SHOP SCHEDULING PROBLEM

'''TASKS = {
    ('job1', 'machine_1'): {'mean': 10, "std": 2, 'prec': None},
    ('job1', 'machine_2'): {'mean': 8, "std": 1, 'prec': ('job1', 'machine_1')},
    ('job1', 'machine_3'): {'mean': 4, "std": 1, 'prec': ('job1', 'machine_2')},
    ('job2', 'machine_2'): {'mean': 8, "std": 3, 'prec': ('job2', None)},
    ('job2', 'machine_1'): {'mean': 3, "std": 2, 'prec': ('job2', 'machine_2')},
    ('job2', 'machine_4'): {'mean': 5, "std": 7, 'prec': ('job2', 'machine_1')},
    ('job2', 'machine_3'): {'mean': 6, "std": 0, 'prec': ('job2', 'machine_4')},
    ('job3', 'machine_1'): {'mean': 4, "std": 1, 'prec': None},
    ('job3', 'machine_2'): {'mean': 7, "std": 2, 'prec': ('job3', 'machine_1')},
    ('job3', 'machine_4'): {'mean': 3, "std": 3, 'prec': ('job3', 'machine_2')},
}'''

TASKS = {
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
}

MACHINES = ['machine_1', 'machine_2', 'machine_3', 'machine_4']


def simulate_schedule(s, N, D_start=None):
    schedule = pd.DataFrame(s)
    #print('\nSchedule by Machine')
    schedule = schedule.sort_values(by=['Machine', 'Start'])
    schedule_sim = {m: [] for m in MACHINES}
    for index, row in schedule.iterrows():
        schedule_sim[row['Machine']].append(row['Job'])
    #print(schedule_sim)
    makespan_simulation = main(schedule_sim, N, D_start)
    return makespan_simulation


def CP_DQL():
    Q = 0
    q_dec = 0.05
    N = 1000
    #### first iteration
    BB = BBdeterministic(TASKS)
    s_star, D_star = BB.jobshop(Q)
    D_sim = simulate_schedule(s_star, N, D_star)
    print('######### FIRST ITERATION #########')
    print('D_star', D_star, 'D_simulate', D_sim)
    Q = 1.25
    while Q >= 0:
        s, D = BB.jobshop(Q)
        makespan_alpha = simulate_schedule(s, N, D_star)
        if makespan_alpha:
            s_star = s
            D_star = D
        print('######### ITERATION #########')
        print('Q', Q, 'D_star', D_star, 's_start', s_star)
        Q = round(Q-q_dec, 3)

def CP_BetterSolution(Q):
    Q = 0.3678
    N = 1000
    #### first iteration
    BB = BBdeterministic(TASKS)
    s_star, D_star = BB.jobshop(Q)
    D_sim = simulate_schedule(s_star, N, D_star)
    print('Makespan simulated', D_sim)
    print('Solution', s_star)
    print('Deterministic Makespan', D_star)


CP_DQL()