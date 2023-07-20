"""
* Prefix: Class to handle the prefix shared by events within traces.
* Buffer: Class to handle the features of a single event required for predictive models.
"""

import os


def define_folder_output(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


class ParallelObject(object):

    def __init__(self):
        self._am_parallel = []
    def _set_last_events(self, am):
        for token in am:
            self._am_parallel.append(token)

    def _get_last_events(self):
        tokens = set(self._am_parallel)
        print(tokens)
        self._am_parallel = []
        return tokens

    def _update_last_events(self):
        self._am_parallel = []


class Prefix(object):

    def __init__(self):
        self._list_activities = list()

    def add_activity(self, activity, time):
        self._list_activities.append(activity)
        #self._list_activities.append((activity, time))

    def get_prefix(self, time):
        '''temporal_prefix = []
        for tuple in self._list_activities:
            if tuple[1] >= time:
                temporal_prefix.append(tuple)'''
        return self._list_activities


class Buffer(object):

    def __init__(self, writer):
        self.buffer = {
            "id_case": -1,
            "activity": None,
            "enabled_time": None,
            "start_time": None,
            "end_time": None,
            "role": None,
            "wip_wait": -1,
            "wip_start": -1,
            "wip_end": -1,
            "wip_activity": -1,
            "ro_total": [],
            "ro_single": -1,
            "queue": -1,
            "prefix": Prefix
        }
        self.writer = writer

    def set_feature(self, feature, value):
        if isinstance(self.buffer[feature], list):
            self.buffer[feature].append(value)
        else:
            self.buffer[feature] = value

    def get_feature(self, feature):
        return self.buffer[feature]

    def print_values(self):
        print(*self.buffer.values())
        self.writer.writerow(self.buffer.values())

    def get_buffer_keys(self):
        return self.buffer.keys()

    def duplicate_buffer_parallel(self):
        self.buffer
