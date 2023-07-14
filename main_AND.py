import csv
import simpy
from process import SimulationProcess
from event_trace import Token
from MAINparameters import Parameters
import sys, getopt
import warnings
from buffer_log import Buffer
import pm4py
from inter_trigger_timer import InterTriggerTimer


def setup(env: simpy.Environment, PATH_PETRINET, params, i):
    simulation_process = SimulationProcess(env, params, PATH_PETRINET)
    f = open('event_log.csv', 'w')
    writer = csv.writer(f)
    buffer = Buffer(writer)
    buffer.write_columns()
    net, im, fm = pm4py.read_pnml(PATH_PETRINET)
    interval = InterTriggerTimer(params.INTER_TRIGGER, simulation_process, params.START_SIMULATION)
    for i in range(0, params.TRACES):
        itime = interval.get_next_arrival(env)
        yield env.timeout(itime)
        env.process(Token(i, net, im, params, simulation_process, [], 'sequential', buffer).simulation(env))


def run_simulation(PATH_PETRINET, PATH_PARAMETERS, N_SIMULATION, N_TRACES):

    for i in range(0, N_SIMULATION):
        params = Parameters(PATH_PARAMETERS, N_TRACES)
        env = simpy.Environment()
        env.process(setup(env, PATH_PETRINET, params, i))
        env.run(until=params.SIM_TIME)



def main(argv):
    opts, args = getopt.getopt(argv, "h:p:s:t:i:")
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
    print(PATH_PETRINET, N_SIMULATION, N_TRACES)
    run_simulation(PATH_PETRINET, PATH_PARAMETERS, N_SIMULATION, N_TRACES)


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main(sys.argv[1:])