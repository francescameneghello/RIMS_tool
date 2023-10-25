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
from inter_trigger_timer import InterTriggerTimer
from result_analysis import Result
from datetime import timedelta
import warnings
import sys

EXAMPLE = {'arrivalsD': ['example/example_arrivals/bpi2012.pnml', 'example/example_arrivals/input_arrivals_example_distribution.json', 1, 20, 'example_arrivals'],
           'arrivalsS': ['example/example_arrivals/bpi2012.pnml', 'example/example_arrivals/input_arrivals_example_timeseries.json', 1, 10, 'example_arrivals'],
           'process_times': ['example/example_process_times/synthetic_petrinet.pnml', 'example/example_process_times/input_process_times_example.json', 1, 15, 'example_process_times'],
           'decision_mining': ['example/example_decision_mining/bpi2012.pnml', 'example/example_decision_mining/input_decision_mining_example.json', 1, 10, 'example_decision_mining'],
           }


def setup(env: simpy.Environment, PATH_PETRINET, params, i, NAME, f):
    simulation_process = SimulationProcess(env, params)
    utility.define_folder_output("output/output_{}".format(NAME))
    writer = csv.writer(f)
    writer.writerow(Buffer(writer).get_buffer_keys())
    net, im, fm = pm4py.read_pnml(PATH_PETRINET)
    interval = InterTriggerTimer(params, simulation_process, params.START_SIMULATION)
    for i in range(0, params.TRACES):
        prefix = Prefix()
        itime = interval.get_next_arrival(env, i)
        yield env.timeout(itime)
        parallel_object = utility.ParallelObject()
        time_trace = params.START_SIMULATION + timedelta(seconds=env.now)
        env.process(Token(i, net, im, params, simulation_process, prefix, 'sequential', writer, parallel_object, time_trace, None).simulation(env))

def run_simulation(PATH_PETRINET, PATH_PARAMETERS, N_SIMULATION, N_TRACES, NAME):
    for i in range(0, N_SIMULATION):
        with open("output/output_{}/simulated_log_{}_{}".format(NAME, NAME, i) + ".csv", 'w') as f:
            params = Parameters(PATH_PARAMETERS, N_TRACES)
            env = simpy.Environment()
            env.process(setup(env, PATH_PETRINET, params, i, NAME, f))
            env.run(until=params.SIM_TIME)
    result = Result("output_{}".format(NAME), params)
    result._analyse()


def main(argv):
    opts, args = getopt.getopt(argv, "h:p:s:t:i:o:e:")
    for opt, arg in opts:
        print(opt, arg)
        if opt == '-h':
            print('main.py -p <petrinet in pnml format> -s <parameters read from file .json> -t <total number of traces> -i <total number of simulation>')
            sys.exit()
        elif opt == "-p":
            PATH_PETRINET = arg
        elif opt == "-s":
            PATH_PARAMETERS = arg
        elif opt == "-t":
            N_TRACES = int(arg)
        elif opt == "-i":
            N_SIMULATION = int(arg)
        elif opt == "-o":
            NAME = arg
        elif opt == "-e":
            if arg in EXAMPLE:
                PATH_PETRINET, PATH_PARAMETERS, N_SIMULATION, N_TRACES, NAME = EXAMPLE[arg]
            else:
                raise ValueError('The keywords for the provided examples are the following: arrivalsD, arrivalsS, decision_mining, process_times')
    print(PATH_PETRINET, PATH_PARAMETERS, N_SIMULATION, N_TRACES, NAME)
    run_simulation(PATH_PETRINET, PATH_PARAMETERS, N_SIMULATION, N_TRACES, NAME)


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main(sys.argv[1:])