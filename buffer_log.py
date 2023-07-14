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
            "prefix": []
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

    def write_columns(self):
        self.writer.writerow(self.buffer.keys())

    def duplicate_buffer_parallel(self):
        self.buffer