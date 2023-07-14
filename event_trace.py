from datetime import timedelta
import simpy
import pm4py
import random
from process import SimulationProcess
from pm4py.objects.petri_net import semantics
from simpy.events import AnyOf, AllOf, Event
import numpy as np
import copy
from buffer_log import Buffer


class Token(object):

    def __init__(self, id, net, am, params, process: SimulationProcess, prefix, type, buffer):
        self.id = id
        self.process = process
        self.start_time = params.START_SIMULATION
        self.params = params
        self.pos = 0
        self.net = net
        self.am = am
        self.prefix = prefix
        self.type = type
        if type == 'sequential':
            self.see_activity = False
        else:
            self.see_activity = True
        self.buffer = buffer

    def delete_places(self, places):
        delete = []
        for place in places:
            for p in self.net.places:
                if str(place) in str(p.name):
                    delete.append(p)
        return delete

    def simulation(self, env: simpy.Environment):
        trans = self.next_transition(env)
        ### register trace in process ###
        resource_trace = self.process.get_resource_trace()
        resource_trace_request = resource_trace.request()

        while trans is not None:
            if self.see_activity:
                yield resource_trace_request
            if type(trans) == list:
                #print(trans)
                self.process.get_last_events()
                #yield AllOf(env, trans)
                yield trans[0] & trans[1]
                am_after = self.process.get_last_events() - set(self.am)
                for d in self.delete_places(self.am):
                    del self.am[d]
                for t in am_after:
                    self.am[t] = 1
                #pm4py.view_petri_net(self.net, self.am)
                all_enabled_trans = list(semantics.enabled_transitions(self.net, self.am))
                trans = all_enabled_trans[0]

            if trans.label is not None:
                self.buffer.set_feature("id_case", self.id)
                self.buffer.set_feature("activity", trans.label)
                self.buffer.set_feature("prefix", trans.label)

                ### call predictor for waiting time
                if trans.label in self.params.ROLE_ACTIVITY:
                    resource = self.process.get_resource(self.params.ROLE_ACTIVITY[trans.label])
                else:
                    raise ValueError('Not resource/role defined for this activity', trans.label)

                self.buffer.set_feature("wip_wait", resource_trace.count)
                self.buffer.set_feature("ro_single", self.process.get_occupations_single_resource(resource.get_name()))

                queue = 0 if len(resource.queue) == 0 else len(resource.queue[-1])
                self.buffer.set_feature("queue", queue)

                waiting = 5

                if self.see_activity:
                    yield env.timeout(waiting)

                request_resource = resource.request()
                self.buffer.set_feature("enabled_time", str(self.start_time + timedelta(seconds=env.now)))
                yield request_resource

                ### register event in process ###
                resource_task = self.process.get_resource_event(trans.name)
                resource_task_request = resource_task.request()
                yield resource_task_request

                self.buffer.set_feature("start_time", str(self.start_time + timedelta(seconds=env.now)))
                ### call predictor for processing time
                self.buffer.set_feature("wip_start", resource_trace.count)
                self.buffer.set_feature("ro_single", self.process.get_occupations_single_resource(resource.get_name()))
                self.buffer.set_feature("wip_activity", resource_task.count)

                duration = np.random.uniform(3600, 7200)

                yield env.timeout(duration)

                self.buffer.set_feature("wip_end", resource_trace.count)
                self.buffer.set_feature("end_time", str(self.start_time + timedelta(seconds=env.now)))
                self.buffer.set_feature("role", resource.get_name())

                self.buffer.print_values()
                resource.release(request_resource)
                resource_task.release(resource_task_request)

            self.update_marking(trans)
            trans = self.next_transition(env)

        if self.type == 'parallel':
            self.process.set_last_events(self.am)
        resource_trace.release(resource_trace_request)

    def update_marking(self, trans):
        self.am = semantics.execute(trans, self.net, self.am)


    def check_probability(self, prob):
        """Check if the sum of probabilities is 1
        """
        if sum(prob) != 1:
            print('WARNING: The sum of the probabilities associated with the paths is not 1, to run the simulation we define equal probability')
            return False
        else:
            return True

    def define_xor_next_activity(self, all_enabled_trans):
        list_trans = [trans.name for trans in all_enabled_trans]
        if set(self.params.PROBABILITY.keys()).intersection(list_trans) != set():
            try:
                prob = [self.params.PROBABILITY[key] for key in list_trans]
            except:
                print('ERROR: Not all path probabilities are defined. Define all paths: ', list_trans)
            if not self.check_probability(prob):
                next = random.choices(list(range(0, len(all_enabled_trans), 1)))[0]
            else:
                value = [*range(0, len(prob), 1)]
                next = int(random.choices(value, prob)[0])
        else:
            next = random.choices(list(range(0, len(all_enabled_trans), 1)))[0]
        return all_enabled_trans[next]

    def delete_tokens(self, name):
        to_delete = []
        for p in self.am:
            if p.name != name:
                to_delete.append(p)
        return to_delete

    def next_transition(self, env):
        all_enabled_trans = semantics.enabled_transitions(self.net, self.am)
        all_enabled_trans = list(all_enabled_trans)
        all_enabled_trans.sort(key=lambda x: x.name)
        label_element = str(list(self.am)[0])
        if len(all_enabled_trans) == 0:
            return None
        elif len(self.am) == 1:  ### caso di un singolo token processato dentro petrinet
            if len(all_enabled_trans) > 1:
                return self.define_xor_next_activity(all_enabled_trans)
            else:
                return all_enabled_trans[0]
        else:
            events = []
            for token in self.am:
                name = token.name
                new_am = copy.copy(self.am)
                tokens_to_delete = self.delete_tokens(name)
                for p in tokens_to_delete:
                    del new_am[p]
                path = env.process(Token(self.id, self.net, new_am, self.params, self.process, self.prefix, "parallel", self.buffer).simulation(env))
                events.append(path)

            #pm4py.view_petri_net(self.net, self.am)
            return events