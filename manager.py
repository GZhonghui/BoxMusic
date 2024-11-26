import threading
import time

class WorkerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()
        self.loop_func = None

    def run(self):
        while not self._stop_event.is_set():
            time.sleep(1)
            if self.loop_func: self.loop_func()

    def stop(self):
        self._stop_event.set()