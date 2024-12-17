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

names = ['test_dfci_1_22_2022', 'test_dfci_3_12_2022', 'test_dfci_2_1_2022','test_dfci_3_6_2022', 'test_dfci_2_15_2022',
         'test_dfci_1_8_2022', 'test_dfci_4_10_2022', 'test_dfci_2_9_2022', 'test_dfci_2_22_2022', 'test_dfci_1_23_2022']

for name in names:
    NAME_DAY = name
    json_path = '/Users/francescameneghello/Downloads/JSON 2/' + NAME_DAY + '.json'

    with open(json_path, "r") as f:
        data = json.load(f)

    #### find number of jobs, tasks, machines
    print('******************************************** ', NAME_DAY, ' ***************************************')
    print('N_JOBS', len(data['jobs']))
    print('N_MACHINES', len(data['machines']))

    ###### makespan and dates #######
    start, end, actual_makespan = makespan_actual(data)
    data['actual_start']= str(start)
    data['actual_end']= str(end)
    data['actual_makespan'] = str(actual_makespan)


    ###### definition jobs and machines ######
    machine_key = {}
    for idx, m in enumerate(data['machines']):
        machine_key[m] = str(idx)
    data['machines'] = list(machine_key.values())

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

    #### actual scheduling #########

    data["actual_scheduling"] = retrieve_actual_schedule(data)

    path = '/Users/francescameneghello/Documents/GitHub/Job_Shop_Scheduling_Benchmark_Environments_and_Instances/' + NAME_DAY + '_cal_actual.json'
    with open(path, 'w') as outfile:
        json.dump(data, outfile, indent=2)

    print('********************************************************************************************************')
