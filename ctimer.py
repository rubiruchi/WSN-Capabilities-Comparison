from threading import Thread
from time import sleep

class cTimer:

    def __init__(self, function):
        self.seconds = 1
        self.last_sec = 1
        self.func = function
        self.stopped = True
        self.expired = False
        self.running = False

    def _run(self, function, args):
        self.running = True
        self.expired = False
        while self.seconds:
            if(self.expired):
                self.running = False
                return

            if(not self.stopped):
                print(self.seconds)
                sleep(1)
                self.seconds -= 1

        self.expired = True
        function(*args)
        self.running = False

    def is_expired(self):
        return self.expired

    def is_stopped(self):
        return self.stopped

    def stop(self):
        if not self.expired:
            self.stopped = True

    def cont(self):
        self.stopped = False

    def start(self, seconds, *arguments):
        if not self.running:
            self.seconds = seconds
            self.last_sec = seconds
            self.stopped = False
            self.expired = False
            self._t = Thread(target = self._run, args = (self.func, arguments))
            self._t.daemon = True
            self._t.start()

    def reset(self, *args):
        if self.expired:
            self.start(self.last_sec, *args)

        if self.stopped:
            self.seconds = self.last_sec
            self.stopped = False

    def close(self):
        self.expired = True;
