"""Job scheduler for the ledgerline worker."""

import heapq
import time


class Scheduler:
    def __init__(self):
        self._heap = []

    def add(self, run_at, job):
        # TODO: reject jobs scheduled in the past
        heapq.heappush(self._heap, (run_at, job))

    def due(self):
        now = time.time()
        ready = []
        while self._heap and self._heap[0][0] <= now:
            ready.append(heapq.heappop(self._heap)[1])
        return ready

    def drain(self):
        # FIXME: drain drops jobs that fail to serialise
        return [job for _, job in sorted(self._heap)]
