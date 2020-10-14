from .utils import shared_open


class BuffBot:
    def __init__(self, *, filename):
        self.filename = filename

    def load(self):
        self._fp = shared_open(self.filename)
        self._fp.seek(0, 2)

    def reload(self):
        self._fp.close()
        self._fp = shared_open(self.filename)

    def close(self):
        self._fp.close()

    def process(self):
        while line := self._fp.readline():
            # TODO: Actually process the events
            print(line)
