from datetime import datetime
import csv
import simpy
from checking_process import SimulationProcess
from token import Token
from MAINparameters import Parameters
import sys, getopt
import warnings
from os.path import exists


def main(argv):
    opts, args = getopt.getopt(argv, "h:t:l:n:")
    NAME_EXPERIMENT = 'confidential_1000'
    for opt, arg in opts:
        if opt == '-h':
            print('main.py -t <[rims, rims_plus]> -l <log_name> -n <total number of simulation [1, 25]>')
            sys.exit()
        elif opt == "-t":
            type = arg
        elif opt == "-l":
            NAME_EXPERIMENT = arg
        elif opt == "-n":
            N_SIMULATION = int(arg)
            if N_SIMULATION > 25:
                N_SIMULATION = 25
    print(NAME_EXPERIMENT, N_SIMULATION, type)
    run_simulation(NAME_EXPERIMENT, N_SIMULATION, type)


def setup(env: simpy.Environment, NAME_EXPERIMENT, params, i, type):
    simulation_process = SimulationProcess(env=env, params=params)

    if type == 'rims':
        path_result = NAME_EXPERIMENT + '/results/rims/simulated_log_LSTM_' + NAME_EXPERIMENT + str(i) + '.csv'
    else:
        path_result = NAME_EXPERIMENT + '/results/rims_plus/simulated_log_LSTM_' + NAME_EXPERIMENT + str(i) + '.csv'
    f = open(path_result, 'w')

    writer = csv.writer(f)
    writer.writerow(['caseid', 'task', 'start:timestamp', 'time:timestamp', 'role', 'st_wip', 'st_tsk_wip', 'queue'])
    prev = params.START_SIMULATION
    for i in range(1, len(params.ARRIVALS) + 1):
        next = datetime.strptime(params.ARRIVALS.loc[i - 1].at["timestamp"], '%Y-%m-%d %H:%M:%S')
        interval = (next - prev).total_seconds()
        prev = next
        yield env.timeout(interval)
        ## in case of SynLoan, and L1_syn, .... L6_syn, set simulation input as: (env, writer, type aand True)
        env.process(Token(i, params, simulation_process, params).simulation(env, writer, type))


def run_simulation(NAME_EXPERIMENT, N_SIMULATION, type):
    path_model = NAME_EXPERIMENT + '/' + type + '/' + NAME_EXPERIMENT
    if exists(path_model + '_diapr_meta.json'):
        FEATURE_ROLE = 'all_role'
    elif exists(path_model + '_dispr_meta.json'):
        FEATURE_ROLE = 'no_all_role'
    else:
        raise ValueError('LSTM models do not exist in the right folder')

    for i in range(0, N_SIMULATION):
        params = Parameters(NAME_EXPERIMENT, FEATURE_ROLE, i, type)
        env = simpy.Environment()
        env.process(setup(env, NAME_EXPERIMENT, params, i, type))

        env.run(until=params.SIM_TIME)


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main(sys.argv[1:])



