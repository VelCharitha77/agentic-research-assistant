import queue
import threading


class RunEventBroadcaster:
    """Thread-safe in-memory pub/sub for streaming per-run progress events.

    Scoped deliberately: one process, in-memory only. Fine for this
    project's current single-instance scale; a multi-instance deployment
    would need a real broker (Redis pub/sub) instead of a Python dict.
    """

    def __init__(self):
        self._queues: dict[str, queue.Queue] = {}
        self._lock = threading.Lock()

    def subscribe(self, run_id: str) -> queue.Queue:
        with self._lock:
            return self._queues.setdefault(run_id, queue.Queue())

    def publish(self, run_id: str, event: dict) -> None:
        with self._lock:
            q = self._queues.get(run_id)
        if q is not None:
            q.put(event)

    def close(self, run_id: str) -> None:
        with self._lock:
            q = self._queues.pop(run_id, None)
        if q is not None:
            q.put(None)  # sentinel: tells the stream consumer "no more events"


broadcaster = RunEventBroadcaster()
