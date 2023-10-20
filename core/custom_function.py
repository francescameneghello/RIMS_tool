'''
This file contains all the customizable functions, which the user can define,
and which are called by the simulator in the specific steps.

The following table describes the case and inter-case features that can be
used as input from a predictive model.

| Feature      | Description  |
|:------------:|:-------------------------- |
| id_case | Case id of the trace to which the event belongs. |
| activity | Represents the next activity to be performedg. |
| enabled_time | Timestamp of when the activity requests the role to be executed. |
| start_time |  Timestamp of when the activity starts to run.   |
| end_time |   Timestamp of when the activity ends to run.    |
| role |   Designated role to perform the next activity.   |
| resource |  Role resource available to perform the activity.   |
| wip_wait | Represents the number of traces running in the simulation before the waiting time.  |
| wip_start |  Represents the number of traces running in the simulation once an available resource is obtained to run the activity. |
| wip_end | Represents the number of traces running in the simulation at the end of the activity execution. |
| wip_activity |  Represents the number of events running in the simulation that perform the same activity, once an available resource is obtained.   |
| ro_total |    The percentage of occupancy in terms of resources in use for the roles defined in the simulation.   |
| ro_single |   The percentage of occupancy in terms of resources in use for the role defined for the next activity.     |
| queue |  Represents the length of the queue for the required resource.  |
| prefix |  List of activities already performed.  |
| attribute_case |  Attributes defined for the trace.      |
| attribute_event |  Attributes defined for the next event to be executed.   |

'''

from statsmodels.tsa.ar_model import AutoRegResults
from utility import Buffer
import random
import pickle
from datetime import datetime
import os


def case_function_attribute(case: int, time: datetime):
    """
        Function to add one or more attributes to each trace.
        Input parameters are case id number and trace start timestamp and return a dictionary.
        For example, we generate a trace attribute, the requested loan amount, to simulate the process from the BPIChallenge2012A.xes log.
    """
    return {"AMOUNT": random.randint(100, 99999)}


def event_function_attribute(case: int, time: datetime):
    """
        Function to add one or more attributes to each event.
        Input parameters are case id number and track start timestamp and return a dictionary.
        In the following example, we assume that there are multiple bank branches where activities
        are executed by day of the week. From Monday to Wednesday, activities are executed in the
        Eindhoven branch otherwise in the Utrecht one.
    """
    bank = "Utrecht" if time.weekday() > 3 else "Eindhoven"
    return {"bank_branch": bank}


def custom_arrivals_time(case, previous):
    """
    Function to define a new arrival of a trace. 
    The input parameters are the case id number and 
    the start timestamp of the previous trace.
    For example, we used an AutoRegression model 
    for the *arrivals example*.
    """
    loaded = AutoRegResults.load('example/example_arrivals/arrival_AutoReg_model.pkl')
    return loaded.predict(case+1, case+1)[0]


def custom_processing_time(buffer: Buffer):
    """
    Define the processing time of the activity (return the duration in seconds).
    Example of features that can be used to predict:

    ```json
            {
                "id_case": 23,
                "activity": "A_ACCEPTED",
                "enabled_time": "2023-08-23 11:14:13",
                "start_time": "2023-08-23 11:14:13",
                "end_time": "2023-08-23 11:20:13",
                "role": "Role 2",
                "resource": "Sue",
                "wip_wait": 3,
                "wip_start": 3,
                "wip_end": 3,
                "wip_activity": 1,
                "ro_total": [0.5, 1],
                "ro_single": 1,
                "queue": 0,
                "prefix": ["A_SUBMITTED", "A_PARTLYSUBMITTED", "A_PREACCEPTED"],
                "attribute_case": {"AMOUNT": 59024},
                "attribute_event": {"bank_branch": "Eindhoven"}
            }
    ```
    """
    input_feature = list()
    input_feature.append(buffer.get_feature("wip_start"))
    input_feature.append(buffer.get_feature("wip_activity"))
    input_feature.append(buffer.get_feature("start_time").weekday())
    input_feature.append(buffer.get_feature("start_time").hour)
    loaded_model = pickle.load(
        open(os.getcwd()+'/example/example_process_times/processing_time_random_forest.pkl', 'rb'))
    y_pred_f = loaded_model.predict([input_feature])
    return int(y_pred_f[0])


def custom_waiting_time(buffer: Buffer):
    """ Define the waiting time of the activity (return the duration in seconds).
    Example of features that can be used to predict:
    ```json
    {
        "id_case": 15,
        "activity": "A_PARTLYSUBMITTED",
        "enabled_time": "None",
        "start_time": "None",
        "end_time": "None",
        "role": "Role 2",
        "resource": "None",
        "wip_wait": 21,
        "wip_start": -1,
        "wip_end": -1,
        "wip_activity": 1,
        "ro_total": [0.5, 1],
        "ro_single": 1,
        "queue": 13,
        "prefix": ["A_SUBMITTED"],
        "attribute_case": {"AMOUNT": 18207},
        "attribute_event": {"bank_branch": "Eindhoven"}

    }
    ```
    """
    input_feature = list()
    buffer.print_values()
    input_feature.append(buffer.get_feature("wip_wait"))
    input_feature.append(buffer.get_feature("wip_activity"))
    input_feature.append(buffer.get_feature("enabled_time").weekday())
    input_feature.append(buffer.get_feature("enabled_time").hour)
    input_feature.append(buffer.get_feature("ro_single"))
    input_feature.append(buffer.get_feature("queue"))
    loaded_model = pickle.load(
        open(os.getcwd() + '/example/example_process_times/waiting_time_random_forest.pkl', 'rb'))
    y_pred_f = loaded_model.predict([input_feature])
    return int(y_pred_f[0])


def custom_decision_mining(buffer: Buffer):
    """
    Function to define the next activity from a decision point in the Petri net model.
    For example, we used a Random Forest model for the *decision mining* example.

    Example of features that can be used to predict:
    ```json
        {
            "id_case": 43,
            "activity": "A_FINALIZED",
            "enabled_time": "2023-08-24 16:24:29",
            "start_time": "2023-08-24 19:37:31",
            "end_time": "2023-08-24 20:03:34",
            "role": "Role 2",
            "resource": "Sue",
            "wip_wait": 16,
            "wip_start": 4,
            "wip_end": 4,
            "wip_activity": 2,
            "ro_total": [0.0, 1],
            "ro_single": 1,
            "queue": 15,
            "prefix": ["A_SUBMITTED", "A_PARTLYSUBMITTED", "A_PREACCEPTED", "A_ACCEPTED"],
            "attribute_case": {"AMOUNT": 86061},
            "attribute_event": {"bank_branch": "Eindhoven"}

        }
    ```
    """
    input_feature = list()
    prefix = buffer.get_feature("prefix")
    input_feature.append(1 if 'A_PREACCEPTED' in prefix else 0)
    input_feature.append(1 if 'A_ACCEPTED' in prefix else 0)
    input_feature.append(1 if 'A_FINALIZED' in prefix else 0)
    input_feature.append(buffer.get_feature("attribute_case")['AMOUNT'])
    input_feature.append(buffer.get_feature("end_time").hour)
    input_feature.append(buffer.get_feature("end_time").weekday())

    loaded_model = pickle.load(
        open(os.getcwd() + '/example/example_decision_mining/random_forest.pkl', 'rb'))
    y_pred_f = loaded_model.predict([input_feature])
    return int(y_pred_f[0])