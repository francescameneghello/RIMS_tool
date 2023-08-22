'''
This file contains all the customizable functions, which the user can define,
and which are called by the simulator in the specific steps.
'''

from statsmodels.tsa.ar_model import AutoRegResults
from utility import Buffer, ParallelObject
import random
import pickle
from datetime import datetime


def attribute_function_case(case: int, time: datetime):
    """
        Function to add one or more attributes to each trace.
        Input parameters are case id number and track start timestamp and return a dictionary.
        For example, we generate a trace attribute, the requested loan amount, to simulate the process from the BPIChallenge2012A.xes log.
    """
    return {"AMOUNT": random.randint(100, 99999)}


def attribute_function_event(case: int, time: datetime):
    """
        Function to add one or more attributes to each event.
        Input parameters are case id number and track start timestamp and return a dictionary.
        In the following example, we assume that there are multiple bank branches where activities
        are executed by day of the week. From Monday to Wednesday, activities are executed in the
        Eindhoven branch otherwise in the Utrecht one.
    """
    bank = "Utrecht" if time.weekday() > 3 else "Eindhoven"
    return {"bank_branch": bank}


def example_arrivals_time(case):
    """
    Function to define a new arrival of a track.
    For example, we used an AutoRegression model for the *arrivals example*.
    """
    loaded = AutoRegResults.load('../example/example_arrivals/arrival_AutoReg_model.pkl')
    return loaded.predict(case+1, case+1)[0]


def example_decision_mining(buffer: Buffer):
    """
    Function to define the next activity from a decision point in the Petri net model.
    For example, we used a Random Forest model for the *decision mining* example.
    """
    # class output names ---> 0: "A_CANCELLED", 1: "A_DECLINED", 2: "tauSplit_5"
    input_feature = list()
    prefix = buffer.get_feature("prefix")
    input_feature.append(1 if 'A_PREACCEPTED' in prefix else 0)
    input_feature.append(1 if 'A_ACCEPTED' in prefix else 0)
    input_feature.append(1 if 'A_FINALIZED' in prefix else 0)
    input_feature.append(buffer.get_feature("attribute_case")['AMOUNT'])
    input_feature.append(buffer.get_feature("end_time").hour)
    input_feature.append(buffer.get_feature("end_time").day)

    loaded_model = pickle.load(open('/Users/francescameneghello/Documents/GitHub/RIMS_tool/example/example_decision_mining/random_forest.pkl', 'rb'))
    y_pred_f = loaded_model.predict([input_feature])
    return int(y_pred_f[0])