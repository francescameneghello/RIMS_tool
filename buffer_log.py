
class Prefix(object):

    def __init__(self):
        self.list_activities = list()

    def add_activity(self, activity):
        self.list_activities.append(activity)

    def get_prefix(self):
        return self.list_activities


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

    def update_prefix(self, prefix):
        self.prefix = prefix

    def get_buffer_keys(self):
        return self.buffer.keys()

    def duplicate_buffer_parallel(self):
        self.buffer