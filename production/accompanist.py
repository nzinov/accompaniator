import sys
import time
from time import sleep
from multiprocessing import Queue, Value
from listener import Listener
from player import Player
from chord_predictor import ChordPredictor


default_tempo = 124
max_time = sys.float_info.max

"""
deadline is the time in seconds since the beginning of the era, float
"""


class Accompanist:
    def __init__(self):
        self.queue_in = Queue()
        self.queue_out = Queue()
        self.predictor_queue = Queue()
        self.running = Value('i', False)
        self.tempo = Value('f', default_tempo)
        self.deadline = Value('f', 0)

        self.player = Player(self.queue_out, self.running, self.tempo, self.deadline)
        self.predictor = ChordPredictor(self.queue_in, self.queue_out)
        self.listener = Listener(self.queue_in, self.running, self.tempo, self.deadline)

    def run(self):
        self.running.value = True
        self.listener.run()
        self.player.run()
        self.predictor.run()

    def stop(self):
        self.running.value = False
        self.player.stop()
        self.listener.stop()
        self.predictor.stop()
        self.queue_in = Queue()
        self.queue_out = Queue()

    def set_tempo(self, tempo=default_tempo):
        self.tempo.value = tempo

    def set_deadline(self, deadline=0):
        self.deadline.value = deadline

    player = None
    listener = None
    predictor = None
    queue_in = None
    queue_out = None
    running = None
    tempo = None
    deadline = None
    process = None


if __name__ == '__main__':
    a = Accompanist()
    start_time = time.monotonic()
    a.run()
    sleep(50)
    a.stop()
    '''q = a.player
    start_time = time.monotonic()
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
