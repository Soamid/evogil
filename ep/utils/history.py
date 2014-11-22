import copy


class DefaultHistory(object):
    def __init__(self, length, default_factory=None):
        self.history = [copy.deepcopy(default_factory) for _ in range(length)]
        self.ptr = -1
        self.length = length

    def ptr_move(self, j=1):
        return (self.ptr + j) % self.length

    def next(self):
        self.ptr = self.ptr_move()

    def set(self, val):
        self.history[self.ptr] = val

    def push(self, val):
        self.next()
        self.set(val)

    def newest(self):
        return self.history[self.ptr]

    def oldest(self):
        return self.history[self.ptr_move()]