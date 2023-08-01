from datetime import timedelta
import simpy
import pm4py
import random
from process import SimulationProcess
from pm4py.objects.petri_net import semantics
from parameters import Parameters
from utility import Prefix
from simpy.events import AnyOf, AllOf, Event
import numpy as np
import copy
import csv
from utility import Buffer, ParallelObject
import json
from custom_function import *
from simpy.events import Condition


class Token(object):

    def __init__(self, id: int, net: pm4py.objects.petri_net.obj.PetriNet, am: pm4py.objects.petri_net.obj.Marking, params: Parameters, process: SimulationProcess, prefix: Prefix, type: str, writer: csv.writer, parallel_object: ParallelObject, buffer=None):
        self._id = id
        self._process = process
        self._start_time = params.START_SIMULATION
        self._params = params
        self._net = net
        self._am = am
        self._prefix = prefix
        self._type = type
        if type == 'sequential':
            self.see_activity = False
        else:
            self.see_activity = True
        self._writer = writer
        self._parallel_object = parallel_object
        if buffer:
            self.buffer = buffer
        else:
            self.buffer = Buffer(self._writer)

    def _delete_places(self, places):
        delete = []
        for place in places:
            for p in self._net.places:
                if str(place) in str(p.name):
                    delete.append(p)
        return delete

    def simulation(self, env: simpy.Environment):
        trans = self.next_transition(env)
        ### register trace in process ###
        request_resource = None
        resource_trace = self._process.get_resource_trace()
        resource_trace_request = resource_trace.request() if type == 'sequential' else None

        while trans is not None:
            if self.see_activity and type == 'sequential':
                yield resource_trace_request
            if type(trans) == list:
                yield AllOf(env, trans)
                am_after = self._parallel_object._get_last_events()
                for d in self._delete_places(self._am):
                    del self._am[d]
                for t in am_after:
                    self._am[t] = 1
                trans = self.next_transition(env)

            if trans and trans.label:
                self.buffer.set_feature("id_case", self._id)
                self.buffer.set_feature("activity", trans.label)
                self.buffer.set_feature("prefix", self._prefix.get_prefix(self._start_time + timedelta(seconds=env.now)))

                ### call predictor for waiting time
                if trans.label in self._params.ROLE_ACTIVITY:
                    resource = self._process.get_resource(self._params.ROLE_ACTIVITY[trans.label])
                else:
                    raise ValueError('Not resource/role defined for this activity', trans.label)

                self.buffer.set_feature("wip_wait", 0 if type != 'sequential' else resource_trace.count-1)
                self.buffer.set_feature("ro_single", self._process.get_occupations_single_resource(resource.get_name()))

                queue = 0 if len(resource.queue) == 0 else len(resource.queue[-1])
                self.buffer.set_feature("queue", queue)

                waiting = self.define_waiting_time(trans.name)

                if self.see_activity:
                    yield env.timeout(waiting)

                request_resource = resource.request()
                #request_resource = {res.get_name(): res.request() for res in resource}
                self.buffer.set_feature("enabled_time", str(self._start_time + timedelta(seconds=env.now)))
                yield request_resource
                #yield AnyOf(env, request_resource.values())
                #if Condition.all_events(list(request_resource.values()), 1):
                #    request_resource = list(request_resource.values())[0]
                #else:
                #    request_resource_choiced = random.choice(list(request_resource.values()))
                #    print(request_resource_choiced)
                #    list(request_resource.values()).remove(request_resource_choiced)

                ### register event in process ###
                resource_task = self._process.get_resource_event(trans.name)
                resource_task_request = resource_task.request()
                yield resource_task_request

                self.buffer.set_feature("start_time", str(self._start_time + timedelta(seconds=env.now)))
                ### call predictor for processing time
                self.buffer.set_feature("wip_start", 0 if type != 'sequential' else resource_trace.count-1)
                self.buffer.set_feature("ro_single", self._process.get_occupations_single_resource(resource.get_name()))
                self.buffer.set_feature("wip_activity", resource_task.count-1)

                duration = self.define_processing_time(trans.name)

                yield env.timeout(duration)

                self.buffer.set_feature("wip_end", 0 if type != 'sequential' else resource_trace.count-1)
                self.buffer.set_feature("end_time", str(self._start_time + timedelta(seconds=env.now)))
                self.buffer.set_feature("role", resource.get_name())
                self.buffer.print_values()
                self._prefix.add_activity(trans.label)
                resource.release(request_resource)
                resource_task.release(resource_task_request)

            self._update_marking(trans)
            trans = self.next_transition(env) if self._am else None

        if self._type == 'parallel':
            self._parallel_object._set_last_events(self._am)
        if self._type == 'sequential':
            resource_trace.release(resource_trace_request)

    def _get_resource_role(self, activity):
        elements = self._params.ROLE_ACTIVITY[activity.label]
        resource_object = []
        for e in elements:
            resource_object.append(self._process.get_resource(e))
        return resource_object

    def _update_marking(self, trans):
        self._am = semantics.execute(trans, self._net, self._am)

    def _delete_tokens(self, name):
        to_delete = []
        for p in self._am:
            if p.name != name:
                to_delete.append(p)
        return to_delete

    def _check_probability(self, prob):
        """Check if the sum of probabilities is 1
        """
        if sum(prob) != 1:
            print('WARNING: The sum of the probabilities associated with the paths is not 1, to run the simulation we define equal probability')
            return False
        else:
            return True

    def _check_type_paths(self, prob):
        if type(prob[0]) is str:
            if sum([x == prob[0] for x in prob]) != len(prob):
                raise ValueError('ERROR: Not all path are defined as same type ', prob)
        elif type(prob[0]) is float:
            if sum([isinstance(x, float) for x in prob]) != len(prob):
                raise ValueError('ERROR: Not all path are defined as same type (float number) ', prob)
        else:
            raise ValueError("ERROR: Invalid input, specify the probability as AUTO, float number or CUSTOM ", prob)

    def _retrieve_check_paths(self, all_enabled_trans):
        list_trans = [trans.name for trans in all_enabled_trans]
        try:
            prob = [self._params.PROBABILITY[key] for key in list_trans]
        except:
            print('ERROR: Not all path probabilities are defined. Define all paths: ', list_trans)
        return prob

    def define_xor_next_activity(self, all_enabled_trans):
        """ Three different methods to decide which path following from XOR gateway:
        * Random choice: each path has equal probability to be chosen (AUTO)
        ```json
        "probability": {
            "Activity_1sh8ud3": "AUTO",
            "Activity_1tpvdm3": "AUTO"
        }
        ```
        * Defined probability: in the file json it is possible to define for each path a specific probability (PROBABILITY as value)
        ```json
        "probability": {
            "Activity_1sh8ud3": 0.20,
            "Activity_1tpvdm3": 0.80
        }
        ```
        * Custom method: it is possible to define a dedicate method that given the possible paths it returns the one to
        follow, using whatever techniques the user prefers. (CUSTOM)
        ```json
        "probability": {
            "Activity_1sh8ud3": "CUSTOM",
            "Activity_1tpvdm3": "CUSTOM"
        }
        ```
        """
        prob = self._retrieve_check_paths(all_enabled_trans)
        self._check_type_paths(prob)
        if prob[0] == 'AUTO':
                next = random.choices(list(range(0, len(all_enabled_trans), 1)))[0]
        elif prob[0] == 'CUSTOM':
            next = self.call_custom_xor_function(all_enabled_trans)
        elif type(prob[0] == float()):
            if not self._check_probability(prob):
                value = [*range(0, len(prob), 1)]
                next = int(random.choices(value, prob)[0])
            else:
                next = random.choices(list(range(0, len(all_enabled_trans), 1)))[0]

        return all_enabled_trans[next]

    def define_processing_time(self, activity):
        """ Three different methods are available to define the processing time for each activity:
            * Distribution function: specify in the json file the distribution with the right parameters for each
            activity, see the [numpy_distribution](https://numpy.org/doc/stable/reference/random/generator.html) distribution, (DISTRIBUTION)
            ```json
             "processing_time": {
                 "Activity_id":  ["uniform", 3600, 7200],
             }
            ```
            * Custom method: it is possible to define a dedicated method that, given the activity and its
            characteristics, returns the duration of processing time required. (CUSTOM)
            ```json
            "processing_time": {
                 "Activity_id":  ["custom"]
            }
            ```
            * Mixed: It is possible to define a distribution function for some activities and a dedicated method for the others.
            ```json
            "processing_time": {
                 "Activity_id1":  ["custom"],
                 "Activity_id2":  ["uniform", 3600, 7200]
            }
            ```
        """
        try:
            if self._params.PROCESSING_TIME[activity][0] == 'custom':
                duration = self.call_custom_processing_time()
            else:
                distribution = self._params.PROCESSING_TIME[activity][0]
                parameters = self._params.PROCESSING_TIME[activity][1:-1]
                duration = getattr(np.random, distribution)(parameters, size=1)[0]
        except:
            raise ValueError("ERROR: The processing time of", activity, "is not defined in json file")

        return duration

    def define_waiting_time(self, next_act):
        """ Three different methods are available to define the waiting time before each activity:
            * Distribution function: specify in the json file the distribution with the right parameters for each
            activity, see the [numpy_distribution](https://numpy.org/doc/stable/reference/random/generator.html) distribution, (DISTRIBUTION)
            ```json
             "waiting_time": {
                 "Activity_id":  ["uniform", 3600, 7200],
             }
            ```
            * Custom method: it is possible to define a dedicated method that, given the next activity with its
            features, returns the duration of waiting time. (CUSTOM)
            ```json
            "waiting_time": {
                 "Activity_id":  ["custom"]
            }
            ```
            * Mixed: As the processing time, it is possible to define a mix of methods for each activity.
            ```json
            "waiting_time": {
                 "Activity_id1":  ["custom"],
                 "Activity_id2":  ["uniform", 3600, 7200]
            }
            ```
        """
        try:
            if self._params.WAITING_TIME[next_act][0] == 'custom':
                duration = self.call_custom_waiting_time()
            else:
                distribution = self._params.WAITING_TIME[next_act][0]
                parameters = self._params.WAITING_TIME[next_act][1:-1]
                duration = getattr(np.random, distribution)(parameters, size=1)[0]
        except:
            duration = 0

        return duration

    def call_custom_processing_time(self):
        """Define the processing time of the activity (return the duration in seconds).
           Example of features that can be used to predict:
        ```json
        {
                  "activity": "F",
                  "enabled_time": "2023-03-16 10:31:58.131415",
                  "end_time": null,
                  "id_case": 0,
                  "prefix": [ "A", "C", "B"],
                  "queue": 0,
                  "ro_single": 0.33,
                  "ro_total": [],
                  "role": null,
                  "start_time": "2023-03-16 10:31:58.131415",
                  "wip_activity": 0,
                  "wip_end": -1,
                  "wip_start": 0,
                  "wip_wait": 0
        }
        ```"""
        print(json.dumps(self.buffer.buffer, indent=14, sort_keys=True))
        return 0

    def call_custom_waiting_time(self):
        """Define the waiting time of the activity (return the duration in seconds).
        Example of features that can be used to predict:
        ```json
        {
                  "activity": "F",
                  "enabled_time": "2023-03-16 10:31:58.131415",
                  "end_time": null,
                  "id_case": 0,
                  "prefix": [ "A", "C", "B"],
                  "queue": 0,
                  "ro_single": 0.33,
                  "ro_total": [],
                  "role": null,
                  "start_time": "2023-03-16 10:31:58.131415",
                  "wip_activity": 0,
                  "wip_end": -1,
                  "wip_start": 0,
                  "wip_wait": 0
        }
        ```"""
        print(json.dumps(self.buffer.buffer, indent=14, sort_keys=True))
        return 0

    def call_custom_xor_function(self, all_enabled_trans):
        """Define the custom method to determine the path to follow up (return the index of path).
        Example of features that can be used to predict:
        ```json
        {
              "activity": "B",
              "enabled_time": "2023-03-16 11:15:27.449050",
              "end_time": "2023-03-16 12:49:17.927216",
              "id_case": 0,
              "prefix": [ "A", "C", "E"],
              "queue": 0,
              "ro_single": 0.33,
              "ro_total": [],
              "role": "Role 2",
              "start_time": "2023-03-16 11:15:27.449050",
              "wip_activity": 1,
              "wip_end": 3,
              "wip_start": 3,
              "wip_wait": 3
        }
        ```"""
        print('Possible transitions of patrinet: ', all_enabled_trans)
        print(self.buffer.buffer)
        #print(json.dumps(self.buffer.duplicate_buffer_parallel(), indent=14, sort_keys=True))

        """Sistemare risorse prima di fare example!!!!!!!!!!!!!!!!"""
        #import pickle
        #label_name = {0: 'examine casually', 1: 'examine thoroughly'}
        #loaded_clf = pickle.load(open('decision_tree_running_example.pkl', 'rb'))
        #example = [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 2, 0]
        #loaded_clf.predict([example])

        return 0

    def next_transition(self, env):
        """
        Method to define the next activity in the petrinet.
        """
        all_enabled_trans = semantics.enabled_transitions(self._net, self._am)
        all_enabled_trans = list(all_enabled_trans)
        all_enabled_trans.sort(key=lambda x: x.name)
        if len(all_enabled_trans) == 0:
            return None
        elif len(all_enabled_trans) == 1:
            return all_enabled_trans[0]
        else:
            if len(self._am) == 1:
                return self.define_xor_next_activity(all_enabled_trans)
            else:
                events = []
                for token in self._am:
                    name = token.name
                    new_am = copy.copy(self._am)
                    tokens_to_delete = self._delete_tokens(name)
                    for p in tokens_to_delete:
                        del new_am[p]
                    path = env.process(Token(self._id, self._net, new_am, self._params, self._process, self._prefix, "parallel", self._writer, self._parallel_object, self.buffer).simulation(env))
                    events.append(path)
                return events
