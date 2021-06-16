import threading

class ChunkCounter:
    def __init__(self, value=0, notify_per=1000):
        self.notify_per = notify_per
        self._value = value
        self._lock = threading.Lock()
        self._event = threading.Event()

    def count(self):
        with self._lock:
            self._value += 1
            if self._value % self.notify_per == 0:
                self._event.set()

    def wait(self):
        self._event.wait()
        self._event.clear()
        with self._lock:
            prev = int(self._value)
            self._value = 0
            return prev