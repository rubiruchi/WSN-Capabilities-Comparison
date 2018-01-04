from threading import Thread
from time import sleep
import signal
import threading
import os

class cTimer:

    class WakeUpException(Exception):
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return repr(self.value)


    def signal_handler(self,signum, stack):
        print(signum)
        print("exception raised")
        #raise WakeUpException("wake up!")


    def __init__(self, function):
        self.seconds = 1
        self.last_sec = 1
        self.func = function
        self.stopped = True
        self.expired = False
        self.running = False
        signal.signal(signal.SIGUSR1, self.signal_handler)

    def _run(self, function, args):
        self.running = True
        self.expired = False
        print("timer started",self.seconds,self.stopped,self.expired,self.running,args)
        while self.seconds:
            if(not self.stopped):
                try:
                    sleep(1)
                except WakeUpException:
                    print("timer closing after forced expire")
                    break

                self.seconds -= 1

        if not self.expired:
            self.expired = True
            print("timer closing after normal expire")
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
            print("starting timer")
            self._t = Thread(target = self._run,name ="cTimer", args = (self.func, arguments))
            self._t.daemon = True
            self._t.start()

    def reset(self, *args):
        if not self.running:
            print("reset after expired")
            self.start(self.last_sec, *args)

        if self.running:
            print("reset after stopped")
            self.seconds = self.last_sec
            self.stopped = False

    def close(self):
        print("closing")
        os.kill(os.getpid(), signal.SIGUSR1)
