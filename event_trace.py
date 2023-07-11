from datetime import timedelta
import simpy
import pm4py
import random

from checking_process import SimulationProcess
from pm4py.objects.petri_net import semantics
from event_parallel import Token_parallel
from simpy.events import AnyOf, AllOf, Event
import numpy as np


class Token(object):

    def __init__(self, id, PATH_PETRINET, params, process: SimulationProcess):
        self.id = id
        self.net, self.am, self.fm = pm4py.read_pnml(PATH_PETRINET)
        self.PATH_PETRINET = PATH_PETRINET
        self.process = process
        self.start_time = params.START_SIMULATION
        self.params = params
        self.pos = 0
        self.prefix = []
        self.see_activity = False

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
                resource_task = self.process.get_resource_event(trans.label)
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

        resource_trace.release(resource_trace_request)

    def update_marking(self, trans):
        self.am = semantics.execute(trans, self.net, self.am)


    def next_transition(self,  env, writer):
        all_enabled_trans = semantics.enabled_transitions(self.net, self.am)
        all_enabled_trans = list(all_enabled_trans)
        all_enabled_trans.sort(key=lambda x: x.name)
        label_element = str(list(self.am)[0])
        if len(all_enabled_trans) == 0:
            return None
        elif len(self.am) == 1: ### caso di un singolo token processato dentro petrinet
            if len(all_enabled_trans) > 1:
                next = random.choices(list(range(0, len(all_enabled_trans), 1)))[0]
                return all_enabled_trans[next]
            else:
                return all_enabled_trans[0]
        else:
            am_sort = []
            for token in self.am:
                token = str(token)
                if 'ent' in token:
                    key = token[token.find('_') + 1:]
                    am_sort.append(key)
            am_sort.sort()
            key = am_sort[0]
            events = []
            for i in range(0, len(self.process.parallel_dict[key])):
                print(self.process.parallel_dict[key][i])
                path = env.process(Token_parallel(self.id, self.net, self.am, self.params, self.process, self.prefix, self.process.parallel_dict[key][i]).simulation(env, writer))
                events.append(path)

            return events