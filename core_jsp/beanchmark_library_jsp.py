
import pandas as pd
from run_simulation import main
import math
import numpy as np

import json
import time


def define_job_problem(path, type, calendar=False):
    TASKS = {}
    with open(path) as file:
        data = json.load(file)
        jobs = data['jobs']
        MACHINES = data['machines']
        SCHEDULES = None if "solutions_q1" in data else data['solutions']
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
    length_path, stds_list = simulate_schedule(None, 50, MACHINES, path)
    stds_2 = [s*s for s in stds_list]
    Q3 = (1.645/math.sqrt(n_activities))*(math.sqrt(np.mean(stds_2))/np.mean(stds_list))
    return Q3


########## CALENDAR ################
#final_path = path + "/new_experiments/simulation_settings_abz6_cp_solver_0.1_q3_CAL.json"


def define_top_ten(final_path, results_iteration):
    N = 100
    TASK, MACHINES, SCHEDULES = define_job_problem(final_path, type)
    makespans = []
    s = 0
    number_best = 0
    s_star = SCHEDULES[str(s)]["solution"]
    D_star = math.inf
    while s < len(SCHEDULES):
        schedule = SCHEDULES[str(s)]["solution"]
        makespans = simulate_schedule(schedule, N, MACHINES, final_path)  ## D'
        D_alpha = np.percentile(makespans, 95)
        print('Solution n ', s, 'D_alpha', D_alpha)
        print("Mean of makespans", np.mean(makespans), "Std of makespans", np.std(makespans))
        print("********************************************************************************")
        results_iteration["first_step"][s] = {"D_alpha": D_alpha, "mean": np.mean(makespans), "std": np.std(makespans),
                                "DET_makespan": SCHEDULES[str(s)]["makespan"], "n_simulation": 100}
        if D_alpha < D_star:
            number_best = s
            s_star = SCHEDULES[str(s)]["solution"]
            D_star = D_alpha

        s += 1

    ### find best 10 solution
    sort_results = {k: v for k, v in sorted(results_iteration['first_step'].items(), key=lambda item: item[1]["D_alpha"], reverse=True)}
    top_ten = [k for k in sort_results]
    if len(top_ten) > 10:
        top_ten = top_ten[-10:]
    results_iteration["top_ten"] = top_ten

    print('Best solution', D_star, number_best)
    results_iteration["Best_solution_1_step"] = {"solution": number_best, "D_alpha": D_star, "schedule": s_star}

    return results_iteration, top_ten


def define_k_solutions(results_path):
    with open(results_path, "r") as f:
        data = json.load(f)
        makespan_det = []
        for s in data["solutions"]:
            makespan_det.append(data["solutions"][s]["makespan"])

    improvements = []
    for i in range(0, len(makespan_det)-1):
        imp = ((makespan_det[i] - makespan_det[i+1]) /makespan_det[i])*100
        improvements.append(round(imp, 3))

    search_list = improvements
    start_point_research = -1
    while start_point_research < 0:
        try:
            jump = next(i for i in reversed(search_list) if i >= 0.7)
            index_jump = improvements.index(jump)
        except StopIteration:
            index_jump = 0
        count = 0
        for i in range(index_jump, len(improvements)):
            if improvements[i] < 0.6:
                count += 1
        if count >= 5:
            start_point_research = index_jump
        search_list = improvements[:index_jump]
        if not search_list:
            start_point_research = 0

    return range(start_point_research, len(data["solutions"]), 1)


def final_simulation(final_path, results_iteration, top_k):
    print("TOP K solutions", top_k)
    N = 1000
    TASK, MACHINES, SCHEDULES = define_job_problem(final_path, type)
    number_best = 0
    s_star = None
    D_star = math.inf
    for s in top_k:
        schedule = SCHEDULES[str(s)]["solution"]
        makespans = simulate_schedule(schedule, N, MACHINES, final_path)  ## D'
        D_alpha = np.percentile(makespans, 95)
        print('Solution n ', s, 'D_alpha', D_alpha)
        print("Mean of makespans", np.mean(makespans), "Std of makespans", np.std(makespans))
        print("********************************************************************************")
        results_iteration["k_step"][s] = {"D_alpha": D_alpha, "mean": np.mean(makespans), "std": np.std(makespans),
                                "DET_makespan": SCHEDULES[str(s)]["makespan"], "n_simulation": 1000}
        if D_alpha < D_star:
            number_best = s
            s_star = SCHEDULES[str(number_best)]["solution"]
            D_star = D_alpha

        s -= 1

    print('Best solution', D_star, number_best)
    results_iteration["Best_solution"] = {"solution": number_best, "D_alpha": D_star, "schedule": s_star}

    return results_iteration


CRITICAL_PATH_DISCOVERY = False
start_time = time.time()
path = '/Users/francescameneghello/Documents/GitHub/RIMS_tool/core_jsp/example/'
NAME_EXP = 'cscmax_30_15_2_cp_solver_0.1_q3'
final_path = path + 'new_experiments/cscmax_30_15_2/simulation_settings_' +NAME_EXP+ '.json'

if not CRITICAL_PATH_DISCOVERY:

    TASK, MACHINES, SCHEDULES = define_job_problem(final_path, type)  #### read the beanchmarks and define json file to find the solution with CP

    top_k_solutions = define_k_solutions(final_path)

    results_iteration = {"top_k": list(top_k_solutions), "k_step": {}, "Best_solution": {}}

    results_iteration = final_simulation(final_path, results_iteration, top_k_solutions)

    write_path = path + '/results/results_simulation_' + NAME_EXP + '.json'
    with open(write_path, 'w') as outfile:
        json.dump(results_iteration, outfile, indent=2)
else:
    Q3 = define_Q3(10, final_path)
    print('---------------- Q3: ', Q3, ' ----------------------')



'''if not CRITICAL_PATH_DISCOVERY:
    makespans = []
    s = 44
    number_best = 44
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
    print('---------------- Q3: ', Q3, ' ----------------------')'''


