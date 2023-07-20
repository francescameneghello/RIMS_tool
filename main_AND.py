import csv
import simpy

import utility
from process import SimulationProcess
from event_trace import Token
from MAINparameters import Parameters
import sys, getopt
import warnings
from utility import *
import pm4py
from inter_trigger_timer import InterTriggerTimer
from result_analysis import Result


def setup(env: simpy.Environment, PATH_PETRINET, params, i, NAME):
    simulation_process = SimulationProcess(env, params)
    utility.define_folder_output("output_{}".format(NAME))
    f = open("output_{}/simulated_log_{}_{}".format(NAME, NAME, i), 'w')
    writer = csv.writer(f)
    writer.writerow(Buffer(writer).get_buffer_keys())
    net, im, fm = pm4py.read_pnml(PATH_PETRINET)
    #pm4py.view_petri_net(net, im, fm)
    interval = InterTriggerTimer(params, simulation_process, params.START_SIMULATION)
    for i in range(0, params.TRACES):
        prefix = Prefix()
        itime = interval.get_next_arrival(env, i)
        yield env.timeout(itime)
        parallel_object = utility.ParallelObject()
        env.process(Token(i, net, im, params, simulation_process, prefix, 'sequential', writer, parallel_object).simulation(env))

def run_simulation(PATH_PETRINET, PATH_PARAMETERS, N_SIMULATION, N_TRACES, NAME):
    params = Parameters(PATH_PARAMETERS, N_TRACES)
    for i in range(0, N_SIMULATION):
        env = simpy.Environment()
        env.process(setup(env, PATH_PETRINET, params, i, NAME))
        env.run(until=params.SIM_TIME)

    result = Result("output_{}".format(NAME), params)
    result._analyse()

def main(argv):
    opts, args = getopt.getopt(argv, "h:p:s:t:i:o:")
    for opt, arg in opts:
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
    print(PATH_PETRINET, N_SIMULATION, N_TRACES, NAME)
    run_simulation(PATH_PETRINET, PATH_PARAMETERS, N_SIMULATION, N_TRACES, NAME)


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main(sys.argv[1:])