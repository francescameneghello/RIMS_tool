from datetime import timedelta
import simpy
import pm4py
import random
from checking_process import SimulationProcess
from pm4py.objects.petri_net import semantics
from event_parallel import Token_parallel
from simpy.events import AnyOf, AllOf, Event
import numpy as np
import copy


class Token(object):

    '''def __init__(self, id, PATH_PETRINET, params, process: SimulationProcess):
        self.id = id
        self.net, self.am, self.fm = pm4py.read_pnml(PATH_PETRINET)
        self.PATH_PETRINET = PATH_PETRINET
        self.process = process
        self.start_time = params.START_SIMULATION
        self.params = params
        self.pos = 0
        self.prefix = []
        self.see_activity = False'''

    def __init__(self, id, net, am, params, process: SimulationProcess, prefix, type):
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

    def delete_places(self, places):
        delete = []
        for place in places:
            for p in self.net.places:
                if str(place) in str(p.name):
                    delete.append(p)
        return delete

    def simulation(self, env: simpy.Environment, writer):
        trans = self.next_transition(env, writer)
        ### register trace in process ###
        resource_trace = self.process.get_resource_trace()
        resource_trace_request = resource_trace.request()

        while trans is not None:
            if self.see_activity:
                yield resource_trace_request
            if type(trans) == list:
                yield AllOf(env, trans)
                am_after = self.process.get_last_events() - set(self.am)
                for d in self.delete_places(self.am):
                    del self.am[d]
                for t in am_after:
                    self.am[t] = 1
                all_enabled_trans = list(semantics.enabled_transitions(self.net, self.am))
                trans = all_enabled_trans[0]

            if trans.label is not None:
                buffer = [self.id, trans.label]
                self.prefix.append(trans.label)
                ### call predictor for waiting time
                if trans.label in self.params.ROLE_ACTIVITY:
                    resource = self.process.get_resource(self.params.ROLE_ACTIVITY[trans.label])
                else:
                    raise ValueError('Not resource/role defined for this activity', trans.label)

                self.prefix.append(trans.label)
                #pr_wip_wait = self.pr_wip_initial + resource_trace.count
                rp_oc = self.process.get_occupations_resource(resource.get_name())

                waiting = 5

                if len(resource.queue) > 0:
                    queue = len(resource.queue[-1])
                else:
                    queue = 0

                if self.see_activity:
                    yield env.timeout(waiting)

                request_resource = resource.request()
                yield request_resource

                ### register event in process ###
                resource_task = self.process.get_resource_event(trans.name)
                resource_task_request = resource_task.request()
                yield resource_task_request

                #register start-timestamp
                buffer.append(str(self.start_time + timedelta(seconds=env.now)))
                ### call predictor for processing time
                pr_wip = resource_trace.count
                rp_oc = self.process.get_occupations_resource(resource.get_name())
                ac_wip = resource_task.count

                duration = np.random.uniform(3600, 7200)

                if trans.label == 'Start' or trans.label == 'End':
                    yield env.timeout(0)
                else:
                    yield env.timeout(duration)
                buffer.append(str(self.start_time + timedelta(seconds=env.now)))

                buffer.append(resource.get_name())
                buffer.append(pr_wip)
                buffer.append(ac_wip)
                buffer.append(queue)
                resource.release(request_resource)
                resource_task.release(resource_task_request)
                print(*buffer)
                writer.writerow(buffer)

            self.update_marking(trans)
            trans = self.next_transition(env, writer)

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

    def next_transition(self, env, writer):
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
                path = env.process(Token(self.id, self.net, new_am, self.params, self.process, self.prefix, "parallel").simulation(env, writer))
                events.append(path)

            return events