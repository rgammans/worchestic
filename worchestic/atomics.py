import threading

try:
    from atomicx import AtomicInt
except ImportError:
    class AtomicInt:
        """Slower locked classes rather than actually atomic"""
        def __init__(self, init_value):
            self.value = init_value
            self._lock = threading.Lock()

        def inc(self):
            with self._lock:
                self.value += 1

        def dec(self):
            with self._lock:
                self.value -= 1

        def load(self):
            return self.value
