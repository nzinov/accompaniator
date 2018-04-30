import sys
import time
from multiprocessing.dummy import Queue, Process, Value
from time import sleep

from production.listener import Listener
from production.player import Player

default_tempo = 124
max_time = sys.float_info.max

"""
deadline is the time in seconds since the beginning of the era, float
"""


def run_accompanist(accompanist):
    while (accompanist.runing.value):
        if (not accompanist.queue_in.empty()):
            chord = accompanist.queue_in.get()
            accompanist.queue_out.put(chord)
            accompanist.set_deadline(time.time())


class Accompanist:
    def __init__(self):
        self.queue_in = Queue()
        self.queue_out = Queue()
        self.runing = Value('i', False)
        self.tempo = Value('i', default_tempo)
        self.deadline = Value('f', max_time)

        self.player = Player(self.queue_out, self.runing,
                             self.tempo, self.deadline)
        self.listener = Listener(self.queue_in, self.runing,
                                 self.tempo, self.deadline)

    def run(self):
        self.runing.value = True
        self.process = Process(target=run_accompanist, args=(self,))
        self.process.start()
        self.listener.run()
        self.player.run()

    def stop(self):
        self.runing.value = False
        self.player.stop()
        self.listener.stop()
        self.queue_in = Queue()
        self.queue_out = Queue()
        self.process.join()

    def set_tempo(self, tempo=default_tempo):
        self.tempo.value = tempo

    def set_deadline(self, deadline=max_time):
        self.deadline.value = deadline

    player = None
    listener = None
    queue_in = None
    queue_out = None
    runing = None
    tempo = None
    deadline = None
    process = None


if __name__ == '__main__':
    a = Accompanist()
    a.run()
    sleep(50)
    a.stop()
    '''q = a.player
    start_time = time.time()
    a.run()
    chord = Chord([60, 64, 67, 72], 64, 120)
    q.put(chord)
    chord = Chord([76], 64, 120)
    q.put(chord)
    a.set_deadline(start_time + 2)
    sleep(2)
    a.set_deadline(start_time + 3.5)
    '''

    '''q = a.listener
    a.run()
    sleep(1)
    b = q.get()
    print(b)
    a.stop()
    print("Stopped")
    '''
