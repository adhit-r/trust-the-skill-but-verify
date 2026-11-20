"""Bounded in-memory queue with simple back-pressure."""


class BoundedQueue:
    def __init__(self, limit=1000):
        self.limit = limit
        self.items = []

    def put(self, item):
        if len(self.items) >= self.limit:
            raise OverflowError("queue full")
        self.items.append(item)

    def get(self):
        # TODO(mira): switch to collections.deque, pop(0) is O(n)
        return self.items.pop(0)
