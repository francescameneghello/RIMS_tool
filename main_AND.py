import csv
import simpy
from checking_process import SimulationProcess
from event_trace import Token
from MAINparameters import Parameters
import sys, getopt
import warnings
import random
from inter_trigger_timer import InterTriggerTimer


def setup(env: simpy.Environment, PATH_PETRINET, params, i):
    simulation_process = SimulationProcess(env, params, PATH_PETRINET)
    f = open('event_log.csv', 'w')
    writer = csv.writer(f)
    writer.writerow(['caseid', 'task', 'start:timestamp', 'time:timestamp', 'role', 'st_wip', 'st_tsk_wip', 'queue'])
    for i in range(0, params.TRACES):
        interval = random.randrange(20, 10000, 1)
        yield env.timeout(interval)
        env.process(Token(i, PATH_PETRINET, params, simulation_process).simulation(env, writer))


def run_simulation(PATH_PETRINET, PATH_PARAMETERS, N_TRACES):

    for i in range(0, N_TRACES):
        params = Parameters(PATH_PARAMETERS, N_TRACES)
        env = simpy.Environment()
        env.process(setup(env, PATH_PETRINET, params, i))

        env.run(until=params.SIM_TIME)



def main(argv):
    opts, args = getopt.getopt(argv, "h:p:s:t:")
    for opt, arg in opts:
        if opt == '-h':
            print('main.py -t <[rims, rims_plus]> -l <log_name> -n <total number of simulation>')
            sys.exit()
        elif opt == "-p":
            PATH_PETRINET = arg
        elif opt == "-s":
            PATH_PARAMETERS = arg
        elif opt == "-t":
            N_TRACES = int(arg)
    print(PATH_PETRINET, N_TRACES)
    run_simulation(PATH_PETRINET, PATH_PARAMETERS, N_TRACES)




if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main(sys.argv[1:])