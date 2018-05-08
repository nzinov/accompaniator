import sys
import time
import aubio
import numpy as np
# import pyaudio
from time import sleep
from multiprocessing import Queue, Process, Value
from aubio import notes, onset
from production.structures import Note, Chord

"""
1 beat in bpm is 1/4 of musical beat
deadline is the time in seconds since the beginning of the era, float
"""

default_tempo = 124
max_time = sys.float_info.max

sample_rate = 44100
win_s = 1024
hop_s = win_s // 4
buffer_size = hop_s


def from_ms_to_our_time(time, bpm):
    return int(time * (32 * bpm) / (60 * 1000))


def run_queue_in(listener):
    notes_o = notes("default", win_s, hop_s, sample_rate)
    onset_o = onset("default", win_s, hop_s, sample_rate)
    temp_o = aubio.tempo("specdiff", win_s, hop_s, sample_rate)
    last_onset = 0
    beats = []
    last_beat = 0
    count_beat = 0
    last_downbeat = 0
    bar_start = False
    # the stream is read until you call stop
    prev_time = 0
    start_time = time.monotonic()
    while listener.running.value:
        # get new samples
        samples = listener.queue_in.get()
        print('new samples!')
        print(f'len: {len(samples)}')

        print(samples)


        if onset_o(samples):
            print(1)
            last_onset = onset_o.get_last_ms()
        if temp_o(samples):
            print(2)
            tmp = temp_o.get_last_ms()
            beats.append(tmp - last_beat)
            count_beat = (count_beat + 1) % 4
            last_beat = tmp
            if count_beat == 0:
                last_downbeat = last_beat
                bar_start = True
        print('almost thear!')
        new_note = notes_o(samples)
        print('yea')
        if new_note[0] != 0:
            print(3)
            if len(beats) != 0:
                listener.set_tempo(60 * 1000.0 / np.median(beats))
            chord = Chord([Note(int(new_note[0]))], from_ms_to_our_time(last_onset - prev_time, listener.tempo.value),
                          int(new_note[1]), bar_start)
            # print(bar_start, listener.tempo.value, listener.deadline.value, time.monotonic())
            bar_start = False
            listener.queue_in.put(chord)
            KOLYA_time = start_time + (last_downbeat + (4 - count_beat) * 60 * 1000.0 / listener.tempo.value) / 1000.0
            print(bar_start, listener.tempo.value, listener.deadline.value, time.monotonic(), KOLYA_time)
            # print(count_beat, time.monotonic(), KOLYA_time, listener.deadline.value)
            if count_beat != 0:
                listener.set_deadline(KOLYA_time)
            prev_time = last_onset


class Listener:
    def __init__(self, queue=Queue(), running=Value('i', False),
                 tempo=Value('i', default_tempo),
                 deadline=Value('f', 0)):
        self.queue_in = queue
        self.running = running
        self.tempo = tempo
        self.deadline = deadline

    def run(self):
        self.running.value = True
        self.process = Process(target=run_queue_in, args=(self, ))
        self.process.start()

    def stop(self):
        self.running.value = False
        self.process.join()
        self.queue_in = Queue()

    def get(self):
        if self.queue_in.empty() is False:
            return self.queue_in.get()

    def set_tempo(self, tempo=default_tempo):
        self.tempo.value = tempo

    def set_deadline(self, deadline=0):
        self.deadline.value = deadline

    def set_queue_in(self, queue):
        self.queue_in = queue

    queue_in = None
    running = None
    tempo = None
    deadline = None
    process = None


if __name__ == '__main__':
    q = Listener()
    q.run()
    sleep(1)
    a = q.get()
    print(a)
    q.stop()
    print("Stopped")
