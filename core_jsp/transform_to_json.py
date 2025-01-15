import json
from datetime import datetime
from collections import defaultdict


def makespan_actual(data):
    start_times = []
    end_times = []
    for job in data["jobs"]:
        start_times.append(datetime.strptime(data["jobs"][job]['actual_start'][0], '%Y-%m-%d %H:%M:%S'))
        end_times.append(datetime.strptime(data["jobs"][job]["actual_end"][-1], '%Y-%m-%d %H:%M:%S'))
    print('START', min(start_times))
    print('END', max(end_times))
    print('MAKESPAN', max(end_times) - min(start_times), (max(end_times) - min(start_times)).total_seconds()/60)
    return min(start_times),  max(end_times), (max(end_times) - min(start_times)).total_seconds()/60


def overlap(data, resource):
    dict_data = {}
    for job in data["jobs"]:
        for idx, ma in enumerate(data["jobs"][job]["machine_seq"]):
            if ma == resource:
                start = data["jobs"][job]["actual_start"][idx]
                start = int(datetime.strptime(start, '%Y-%m-%d %H:%M:%S').timestamp())
                end = data["jobs"][job]["actual_end"][idx]
                end = int(datetime.strptime(end, '%Y-%m-%d %H:%M:%S').timestamp())
                for i in range(start, end+1):
                    if i in dict_data:
                        dict_data[i] += 1
                    else:
                        dict_data[i] = 1
    return dict_data


def cal_real_data(day, cal):
    interval = []
    if day in cal['days']:
        start_shift = min(cal["hours"])*60
        end_shift = max(cal["hours"])*60
        interval.append([start_shift, end_shift])
    return interval


def retrieve_actual_schedule(data):
    actual_schedule = {m: [] for m in data['machines']}

    for job in data["jobs"]:
        for idx, m in enumerate(data["jobs"][job]['machine_seq']):
            start = datetime.strptime(data["jobs"][job]['actual_start'][idx], '%Y-%m-%d %H:%M:%S')
            actual_schedule[m].append((job, start))

    actual_schedule_ordered = {}
    for m in actual_schedule:
        actual_schedule_ordered[m] = [item[0] for item in sorted(actual_schedule[m], key=lambda x: x[1])]

    return actual_schedule_ordered


def check_same_elements(job):
    common_elements = defaultdict(list)

    for i in range(len(job['activity_seq'])):
        key = (job['actual_start'][i], job['actual_end'][i], job['activity_seq'][i])
        common_elements[key].append(i)

    # Filter elements with more than one occurrence
    duplicates = {k: v for k, v in common_elements.items() if len(v) > 1}

    return duplicates

names = ['1_13','1_12','1_27','1_6','1_19','1_20','1_5','1_26','1_25','1_4','1_18','1_14','1_11','1_7','1_24','1_10','1_3','1_1','1_17','1_9','1_2','1_16','1_8','1_23','1_15','1_22','2_27','2_20','2_13','2_6','2_19','2_12','2_5','2_26','2_25','2_11','2_18','2_24','2_21','2_4','2_28','2_14','2_17','2_10','2_29','2_3','2_7','2_30','2_8','2_23','2_2','2_22','2_9','2_16','2_15','2_1','3_17','3_3','3_24','3_23','3_9','3_16','3_10','3_2','3_22','3_18','3_29','3_8','3_1','3_15','3_21','3_11','3_7','3_14','3_4','3_25','3_19','3_28','3_27','3_20','3_26','3_13','3_5','3_6','3_12','4_15','4_22','4_1','4_8','4_21','4_29','4_14','4_7','4_28','4_27','4_13','4_6','4_20','4_19','4_12','4_24','4_9','4_26','4_16','4_2','4_23','4_5','4_18','4_11','4_4','4_25','4_17','4_10','4_3']
NAME_list = []
JOBS = []
MACHINE = []
TASKS = []
real_makespan = []

for name in names:
    NAME_DAY = name
    json_path = '/Users/francescameneghello/Downloads/JSON 2/test_dfci_' + NAME_DAY + '_2022.json'

    with open(json_path, "r") as f:
        data = json.load(f)

    #### find number of jobs, tasks, machines
    print('******************************************** ', NAME_DAY, ' ***************************************')
    print('N_JOBS', len(data['jobs']))
    print('N_MACHINES', len(data['machines']))

    ###### makespan and dates #######
    start, end, actual_makespan = makespan_actual(data)
    real_makespan.append(actual_makespan)
    data['actual_start']= str(start)
    data['actual_end']= str(end)
    data['actual_makespan'] = str(actual_makespan)


    ###### definition jobs and machines ######
    machine_key = {}
    for idx, m in enumerate(data['machines']):
        machine_key[m] = str(idx)
    data['machines'] = list(machine_key.values())
    data['machines_to_n'] = machine_key
    n_to_machines = {machine_key[key]: key for key in machine_key}
    data['n_to_machines'] = n_to_machines

    data["jobs"]['0'] = data["jobs"].pop(str(len(data["jobs"])))
    last_key, last_value = list(data["jobs"].items())[-1]
    reordered_data = {last_key: last_value, **{k: v for k, v in data["jobs"].items() if k != last_key}}
    data["jobs"] = reordered_data

    for job in data["jobs"]:
        for idx, m in enumerate(data["jobs"][job]["machine_seq"]):
            data["jobs"][job]["machine_seq"][idx] = machine_key[m]

    ######## capacity of resources #########
    data['machines_capacity'] = {}
    for machine in data['machines']:
        data['machines_capacity'][str(machine)] = max(overlap(data, machine).values())

    ##### define fixed actual times
    for job in data["jobs"]:
        for job in data["jobs"].keys():
            data["jobs"][job]['times_fixed'] = []
            for i in range(0, len(data["jobs"][job]['machine_seq'])):
                start = datetime.strptime(data["jobs"][job]['actual_start'][i], '%Y-%m-%d %H:%M:%S')
                end = datetime.strptime(data["jobs"][job]['actual_end'][i], '%Y-%m-%d %H:%M:%S')
                minutes = (end - start).total_seconds()/60
                data["jobs"][job]['times_fixed'].append(int(minutes))

    ##### calendars #######

    not_in_the_machine_list = []
    calendars_new_key = {}

    for r in data["calendars"]:
        if r in machine_key:
            name = machine_key[r]
            calendars_new_key[name] = data["calendars"][r]
        else:
            not_in_the_machine_list.append(r)

    data['calendars_intervals'] = {}
    for key in calendars_new_key:
        data['calendars_intervals'][key] = cal_real_data(start.weekday(), calendars_new_key[key])


    ############ delete duplicate ###############

    for job_id in data["jobs"]:
        duplicates = check_same_elements(data["jobs"][job_id])
        job = data["jobs"][job_id]
        delete = []
        for key, indices in duplicates.items():
            capacity = [(i, data["machines_capacity"][job["machine_seq"][i]]) for i in indices]
            min_tuple = min(capacity, key=lambda x: x[1])
            indices.remove(min_tuple[0])

            delete += indices

        # Create a new list excluding the specified indices
        for e in ['machine_seq', 'activity_seq', 'actual_start', 'actual_end', 'times_fixed', 'scheduled_duration', 'times']:
            job[e] = [item for index, item in enumerate(job[e]) if index not in delete]

        data["jobs"][job_id] = job

    task = 0
    for job in data["jobs"]:
        task += len(data['jobs'][job]['machine_seq'])

    data["n_tasks"] = task
    print('TASK', task)

    NAME_list.append(NAME_DAY)
    JOBS.append(len(data['jobs']))
    MACHINE.append(len(data['machines']))
    #TASKS.append(task)

    #### actual scheduling #########

    data["actual_scheduling"] = retrieve_actual_schedule(data)

    path = '/Users/francescameneghello/Documents/GitHub/Job_Shop_Scheduling_Benchmark_Environments_and_Instances/LSTM/original/' + NAME_DAY + '_cal_actual.json'
    with open(path, 'w') as outfile:
        json.dump(data, outfile, indent=2)

    print('********************************************************************************************************')

print(NAME_list)
print(real_makespan)
print(JOBS)
print(MACHINE)
print(TASKS)