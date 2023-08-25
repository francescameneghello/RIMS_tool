from datetime import datetime, timedelta
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
import custom_function as custom


class Token(object):

    def __init__(self, id: int, net: pm4py.objects.petri_net.obj.PetriNet, am: pm4py.objects.petri_net.obj.Marking, params: Parameters, process: SimulationProcess, prefix: Prefix, type: str, writer: csv.writer, parallel_object: ParallelObject, time: datetime, values=None):
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
        self._buffer = Buffer(writer, values)
        self._buffer.set_feature("attribute_case", custom.attribute_function_case(self._id, time))

    def _delete_places(self, places):
        delete = []
        for place in places:
            for p in self._net.places:
                if str(place) in str(p.name):
                    delete.append(p)
        return delete

    def simulation(self, env: simpy.Environment):
        """
            The main function to handle the simulation of a single trace
        """
        trans = self.next_transition(env)
        ### register trace in process ###
        request_resource = None
        resource_trace = self._process._get_resource_trace()
        resource_trace_request = resource_trace.request() if self._type == 'sequential' else None

        while trans is not None:
            if not self.see_activity and self._type == 'sequential':
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
                self._buffer.reset()
                self._buffer.set_feature("id_case", self._id)
                self._buffer.set_feature("activity", trans.label)
                self._buffer.set_feature("prefix", self._prefix.get_prefix(self._start_time + timedelta(seconds=env.now)))
                self._buffer.set_feature("attribute_event", custom.attribute_function_event(self._id, self._start_time + timedelta(seconds=env.now)))

                ### call predictor for waiting time
                if trans.label in self._params.ROLE_ACTIVITY:
                    resource = self._process._get_resource(self._params.ROLE_ACTIVITY[trans.label])
                else:
                    raise ValueError('Not resource/role defined for this activity', trans.label)

                #self._buffer.set_feature("wip_wait", 0 if type != 'sequential' else resource_trace.count-1)
                self._buffer.set_feature("wip_wait", resource_trace.count)
                self._buffer.set_feature("ro_single", self._process.get_occupations_single_role(resource.get_name()))
                self._buffer.set_feature("ro_total", self._process.get_occupations_all_role())
                self._buffer.set_feature("role", resource.get_name())

                ### register event in process ###
                resource_task = self._process._get_resource_event(trans.label)
                self._buffer.set_feature("wip_activity", resource_task.count)

                queue = 0 if len(resource.queue) == 0 else len(resource.queue[-1])
                self._buffer.set_feature("queue", queue)
                self._buffer.set_feature("enabled_time", self._start_time + timedelta(seconds=env.now))

                waiting = self.define_waiting_time(trans.label)
                if self.see_activity:
                    yield env.timeout(waiting)

                request_resource = resource.request()
                yield request_resource
                single_resource = self._process._set_single_resource(resource.get_name())
                self._buffer.set_feature("resource", single_resource)

                resource_task_request = resource_task.request()
                yield resource_task_request

                ### call predictor for processing time
                self._buffer.set_feature("wip_start", resource_trace.count)
                self._buffer.set_feature("ro_single", self._process.get_occupations_single_role(resource.get_name()))
                self._buffer.set_feature("ro_total", self._process.get_occupations_all_role())
                self._buffer.set_feature("wip_activity", resource_task.count)

                stop = resource.to_time_schedule(self._start_time + timedelta(seconds=env.now))
                yield env.timeout(stop)
                self._buffer.set_feature("start_time", self._start_time + timedelta(seconds=env.now))
                duration = self.define_processing_time(trans.label)

                yield env.timeout(duration)

                self._buffer.set_feature("wip_end", resource_trace.count)
                self._buffer.set_feature("end_time", self._start_time + timedelta(seconds=env.now))
                self._buffer.print_values()
                self._prefix.add_activity(trans.label)
                resource.release(request_resource)
                self._process._release_single_resource(resource.get_name(), single_resource)
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
            resource_object.append(self._process._get_resource(e))
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
        prob = []
        for trans in all_enabled_trans:
            try:
                if trans.label:
                    prob.append(self._params.PROBABILITY[trans.label])
                else:
                    prob.append(self._params.PROBABILITY[trans.name])
            except:
                print('ERROR: Not all path probabilities are defined. Define all paths: ', all_enabled_trans)

        return prob

    def define_xor_next_activity(self, all_enabled_trans):
        """ Three different methods to decide which path following from XOR gateway:
        * Random choice: each path has equal probability to be chosen (AUTO)
        ```json
        "probability": {
            "A_ACCEPTED": "AUTO",
            "skip_2": "AUTO",
            "A_FINALIZED": "AUTO",
        }
        ```
        * Defined probability: in the file json it is possible to define for each path a specific probability (PROBABILITY as value)
        ```json
        "probability": {
            "A_PREACCEPTED": 0.20,
            "skip_1": 0.80
        }
        ```
        * Custom method: it is possible to define a dedicate method that given the possible paths it returns the one to
        follow, using whatever techniques the user prefers. (CUSTOM)
        ```json
        "probability": {
            "A_CANCELLED": "CUSTOM",
            "A_DECLINED": "CUSTOM",
            "tauSplit_5": "CUSTOM"
        }
        ```
        """
        prob = ['AUTO'] if not self._params.PROBABILITY else self._retrieve_check_paths(all_enabled_trans)
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
                 "A_FINALIZED":  ["uniform", 3600, 7200],
             }
            ```
            * Custom method: it is possible to define a dedicated method that, given the activity and its
            characteristics, returns the duration of processing time required. (CUSTOM)
            ```json
            "processing_time": {
                 "A_FINALIZED":  ["custom"]
            }
            ```
            * Mixed: It is possible to define a distribution function for some activities and a dedicated method for the others.
            ```json
            "processing_time": {
                 "A_FINALIZED":  ["custom"],
                 "A_REGISTERED":  ["uniform", 3600, 7200]
            }
            ```
        """
        try:
            if self._params.PROCESSING_TIME[activity]["name"] == 'custom':
                duration = self.call_custom_processing_time()
            else:
                distribution = self._params.PROCESSING_TIME[activity]['name']
                parameters = self._params.PROCESSING_TIME[activity]['parameters']
                duration = getattr(np.random, distribution)(**parameters, size=1)[0]
        except:
            raise ValueError("ERROR: The processing time of", activity, "is not defined in json file")
        return duration

    def define_waiting_time(self, next_act):
        """ Three different methods are available to define the waiting time before each activity:
            * Distribution function: specify in the json file the distribution with the right parameters for each
            activity, see the [numpy_distribution](https://numpy.org/doc/stable/reference/random/generator.html) distribution, (DISTRIBUTION)
            ```json
             "waiting_time": {
                 "A_PARTLYSUBMITTED":  ["uniform", 3600, 7200],
             }
            ```
            * Custom method: it is possible to define a dedicated method that, given the next activity with its
            features, returns the duration of waiting time. (CUSTOM)
            ```json
            "waiting_time": {
                 "A_PARTLYSUBMITTED":  ["custom"]
            }
            ```
            * Mixed: As the processing time, it is possible to define a mix of methods for each activity.
            ```json
            "waiting_time": {
                 "A_PARTLYSUBMITTED":  ["custom"],
                 "A_APPROVED":  ["uniform", 3600, 7200]
            }
            ```
        """
        try:
            if self._params.WAITING_TIME[next_act]["name"] == 'custom':
                duration = self.call_custom_waiting_time()
            else:
                distribution = self._params.WAITING_TIME[next_act]['name']
                parameters = self._params.WAITING_TIME[next_act]['parameters']
                duration = getattr(np.random, distribution)(**parameters, size=1)[0]
        except:
            duration = 0

        return duration

    def call_custom_processing_time(self):
        return custom.custom_processing_time(self._buffer)

    def call_custom_waiting_time(self):
        return custom.custom_waiting_time(self._buffer)

    def call_custom_xor_function(self, all_enabled_trans):
        return custom.example_decision_mining(self._buffer)

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
                    path = env.process(Token(self._id, self._net, new_am, self._params, self._process, self._prefix, "parallel", self._writer, self._parallel_object, self._buffer._get_dictionary()).simulation(env))
                    events.append(path)
                return events
