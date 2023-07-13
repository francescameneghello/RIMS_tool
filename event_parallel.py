from datetime import timedelta
import simpy
import pm4py
import random
import numpy as np
from checking_process import SimulationProcess
from pm4py.objects.petri_net import semantics


class Token_parallel(object):

    def __init__(self, id, net, am, params, process: SimulationProcess, prefix):
        self.id = id
        #self.net, self.am, self.fm = pm4py.read_pnml(PATH_PETRINET)
        self.net = net
        self.am = am
        self.process = process
        self.start_time = params.START_SIMULATION
        self.params = params
        self.pos = 0
        self.prefix = prefix
        self.see_activity = False
        #self.resource_trace = resource_trace

    def simulation(self, env: simpy.Environment, writer):
        trans = self.next_transition()
        while trans is not None:
            if trans.label is not None:
                buffer = [self.id, trans.label]
                self.prefix.append(trans.label)
                if trans.label in self.params.ROLE_ACTIVITY:
                    resource = self.process.get_resource(self.params.ROLE_ACTIVITY[trans.label])
                else:
                    raise ValueError('Not resource/role defined for this activity', trans.label)

                self.prefix.append(trans.label)
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
                #pr_wip = self.resource_trace.count
                rp_oc = self.process.get_occupations_resource(resource.get_name())
                ac_wip = resource_task.count

                duration = np.random.uniform(3600, 7200)

                yield env.timeout(duration)
                timestamp = self.start_time + timedelta(seconds=env.now)
                buffer.append(str(timestamp))

                buffer.append(resource.get_name())
                buffer.append(0)
                buffer.append(ac_wip)
                buffer.append(queue)
                resource.release(request_resource)
                resource_task.release(resource_task_request)
                print(*buffer)
                writer.writerow(buffer)

            self.update_marking(trans)
            trans = self.next_transition()

        self.process.set_last_events(self.am)

    def update_marking(self, trans):
        self.am = semantics.execute(trans, self.net, self.am)

    def extract_valid_transition(self, all_enabled_trans):
        valid = []
        for trans in all_enabled_trans:
            if trans.name in self.transitions:
                valid.append(trans)
        return valid

    def next_transition(self):
        all_enabled_trans = semantics.enabled_transitions(self.net, self.am)
        all_enabled_trans = list(all_enabled_trans)
        all_enabled_trans.sort(key=lambda x: x.name)
        label_element = str(list(self.am)[0])
        if len(all_enabled_trans) == 0:
            return None
        else:
            all_enabled_trans = list(all_enabled_trans)
            all_enabled_trans.sort(key=lambda x: x.name)
            #print(label_element, all_enabled_trans)
            if len(all_enabled_trans) == 0:
                return None
            elif len(all_enabled_trans) > 1:
                next = random.choices(list(range(0, len(all_enabled_trans), 1)))[0]
                return all_enabled_trans[next]
            else:
                return all_enabled_trans[0]

