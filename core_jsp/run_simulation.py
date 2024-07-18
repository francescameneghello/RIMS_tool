"""
.. include:: ../README.md
.. include:: example/example_arrivals/arrivals-example.md
.. include:: example/example_decision_mining/decision_mining-example.md
.. include:: example/example_process_times/process_times-example.md
"""

import csv
import simpy
import utility
from process import SimulationProcess
from event_trace import Token
from parameters import Parameters
import sys, getopt
from utility import *
import pm4py
from datetime import timedelta
import warnings
import numpy as np
import pandas as pd
import networkx as nx


def setup(env: simpy.Environment, params, i, NAME, f):
    simulation_process = SimulationProcess(env, params)
    utility.define_folder_output("output/output_{}".format(NAME))
    writer = csv.writer(f)
    writer.writerow(Buffer(writer).get_buffer_keys())
    #net, im, fm = pm4py.read_pnml(PATH_PETRINET)
    #interval = InterTriggerTimer(params, simulation_process, params.START_SIMULATION)
    for i in range(0, params.N_JOBS):
        prefix = Prefix()
        #itime = interval.get_next_arrival(env, i)
        yield env.timeout(0)
        #parallel_object = utility.ParallelObject()
        #time_trace = params.START_SIMULATION + timedelta(seconds=env.now)
        machine_id = list(params.JOBS.keys())[i]
        print(machine_id)
        env.process(Token(machine_id, params, simulation_process, prefix, writer).simulation(env))


def run_simulation(PATH_PARAMETERS, N_SIMULATION, schedule, D_start):
    NAME = 'simple_example'
    makespans = []
    for i in range(0, N_SIMULATION):
        path = "output/output_{}/simulated_log_{}".format(NAME, NAME) + ".csv"
        with open(path, 'w') as f:
            params = Parameters(PATH_PARAMETERS, schedule)
            env = simpy.Environment()
            env.process(setup(env, params, i, NAME, f))
            env.run()
        makespans.append(env.now)
        find_critical_path(path, params)
        print('N_SIMULATION ', len(makespans), 'MAX makespan', max(makespans))
    return check_results(makespans, D_start)


def check_results(makespans, D_star):
    if D_star:
        prob = [dur < D_star for dur in makespans]
        if sum(prob)/len(prob) >= 0.95:
            print('Probability makespan Pr(make(s) <= ', D_star, ')= ', sum(prob)/len(prob))
            print('Mean of makespans', np.mean(makespans), 'N_Trials ', len(makespans))
            return True
        else:
            return False
    else:
        return True


def main(schedule, N, D_star=None):
    '''opts, args = getopt.getopt(argv, "h:j:i:")
    #main(argv)
    for opt, arg in opts:
        print(opt, arg)
        if opt == '-h':
            print('main.py -p <petrinet in pnml format> -s <parameters read from file .json> -t <total number of traces> -i <total number of simulation>')
            sys.exit()
        elif opt == "-j":
            PATH_PARAMETERS = arg
        elif opt == "-i":
            N_SIMULATION = int(arg)
    '''
    PATH_PARAMETERS = '/Users/francescameneghello/Documents/GitHub/RIMS_tool/core_jsp/example/input_simple_example_distribution.json'
    N_SIMULATION = N
    #print(PATH_PARAMETERS, N_SIMULATION)
    return run_simulation(PATH_PARAMETERS, N_SIMULATION, schedule, D_star)


def find_critical_path(simulated_path, params):
    job = params.JOBS
    data = pd.read_csv(simulated_path)
    data = {
        'id_job': list(data['id_job']),
        'resource': list(data['resource']),
        'start_time': list(data['start_time']),
        'end_time': list(data['end_time']),
        'std': list(data['wip_start'])
    }
    df = pd.DataFrame(data)
    G = nx.DiGraph()

    # Add nodes and edges with weights
    for index, row in df.iterrows():
        start_node = (row['id_job'], row['resource'], 'start')
        finish_node = (row['id_job'], row['resource'], 'finish')
        duration = row['end_time'] - row['start_time']

        G.add_node(start_node, weight=0, std=row['std'])
        G.add_node(finish_node, weight=duration)
        G.add_edge(start_node, finish_node, weight=duration)

        # Create dependencies between tasks
        for other_index, other_row in df.iterrows():
            if row['end_time'] <= other_row['start_time']:
                finish_node = (row['id_job'], row['resource'], 'finish')
                other_start_node = (other_row['id_job'], other_row['resource'], 'start')
                G.add_edge(finish_node, other_start_node, weight=0)

    # Calculate the longest path
    length, path = nx.algorithms.dag.dag_longest_path_length(G, weight='weight'), nx.algorithms.dag.dag_longest_path(G,
                                                                                                                     weight='weight')

    # Extract the critical path and retrieve attributes
    critical_path = []
    critical_path_attributes = []
    for i in range(0, len(path) - 1, 2):
        critical_path.append(path[i][0])
        attributes = G.nodes[path[i]]
        critical_path_attributes.append(attributes)

    print('CRITICAL_PATH', critical_path)
    stds = [act['std'] for act in critical_path_attributes]
    print(stds)

#if __name__ == "__main__":
#    warnings.filterwarnings("ignore")
#    main()