from threading import Thread
from time import sleep

class Timer:

    def __init__(self, function):
        self.sec = 1
        self.last_sec = 1
        self.func = function
        self.stopped = True
        self.expired = False

    def _run(self, seconds, function, stopped, expired):
        expired = False
        while seconds:
            if(expired):
                return

            if(not stopped):
                sleep(1)
                seconds -= 1
            else:
                sleep(1)

        expired = True
        function("resend\n")

    def is_expired(self):
        return self.expired

    def is_stopped(self):
        return self.stopped

    def stop(self):
        if not self.expired:
            self.stopped = True

    def cont(self):
        self.stopped = False

    def start(self, seconds):
        self.sec = seconds
        self.last_sec = seconds
        self.stopped = False
        self.expired = False
        self._t = Thread(target = self._run,
                args = (self.sec, self.func, self.stopped, self.expired))
        self._t.daemon = True
        self._t.start()

    def reset(self):
        if self.expired:
            start(self.last_sec)

        if self.stopped:
            self.sec = self.last_sec
            self.stopped = False

    def close(self):
        self.expired = True;
