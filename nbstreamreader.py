from threading import Thread
from Queue import Queue, Empty

class NonBlockingStreamReader:

    def __init__(self, stream):

        self._s = stream
        self._q = Queue()

        def _populateQueue(stream, queue):

            while True:
                line = stream.readline()
                if line and line.startswith('NODE$') and line.endswith('\n'):
                    line = line.split('$')[1]
                    #print("read:"+ line.rstrip())
                    queue.put(line)

        self._t = Thread(target = _populateQueue,
                args = (self._s, self._q))
        self._t.daemon = True
        self._t.start() #start collecting lines from the stream

    def getline(self, timeout = None):
        try:
            return self._q.get(block = timeout is not None,
                    timeout = timeout)
        except Empty:
            return None
