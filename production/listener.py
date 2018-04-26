import sys
from multiprocessing.dummy import Queue, Process, Value
from time import sleep

import aubio
import numpy as np
import pyaudio
from aubio import notes, onset
from structures import Note, Chord

"""
1 beat in bpm is 1/4 of musical beat
deadline is the time in seconds since the beginning of the era, float
"""

default_tempo = 124
max_time = sys.float_info.max

sample_rate = 44100
win_s = 256
hop_s = win_s // 2
framesize = hop_s
buffer_size = 128


def from_ms_to_our_time(time, bpm):
    return time * (32 * bpm) / (60 * 1000)


def run_queue_in(listener):
    p = pyaudio.PyAudio()
    # open stream
    pyaudio_format = pyaudio.paFloat32
    n_channels = 1
    stream = p.open(format=pyaudio_format,
                    channels=n_channels,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=buffer_size)

    notes_o = notes("default", win_s, hop_s, sample_rate)
    onset_o = onset("default", win_s, hop_s, sample_rate)
    temp_o = aubio.tempo("specdiff", win_s, hop_s, sample_rate)
    last_onset = 0
    beats = []
    last_beat = 0

    # the stream is read until you call stop
    prev_time = 0
    while (listener.runing.value):
        # read data from audio input
        audiobuffer = stream.read(buffer_size, exception_on_overflow=False)
        samples = np.fromstring(audiobuffer, dtype=np.float32)

        if (onset_o(samples)):
            last_onset = onset_o.get_last_ms()
        if (temp_o(samples)):
            tmp = temp_o.get_last_ms()
            beats.append(tmp - last_beat)
            last_beat = tmp
        new_note = notes_o(samples)
        if (new_note[0] != 0):
            if (len(beats) != 0):
                listener.set_tempo(np.median(beats))
            listener.queue_in.put(
                Chord([Note(int(new_note[0]))],
                      from_ms_to_our_time(last_onset - prev_time,
                                          listener.tempo.value),
                      int(new_note[1])))
            prev_time = last_onset


class Listener:
    def __init__(self, queue=Queue(), runing=Value('i', False),
                 tempo=Value('i', default_tempo),
                 deadline=Value('f', max_time)):
        self.queue_in = queue
        self.runing = runing
        self.tempo = tempo
        self.deadline = deadline

    def run(self):
        self.runing.value = True
        self.process = Process(target=run_queue_in, args=(self,))
        self.process.start()

    def stop(self):
        self.runing.value = False
        self.process.join()
        self.queue_in = Queue()

    def get(self):
        if self.queue_in.empty() is False:
            return self.queue_in.get()

    def set_tempo(self, tempo=default_tempo):
        self.tempo.value = tempo

    def set_deadline(self, deadline=max_time):
        self.deadline.value = deadline

    queue_in = None
    runing = None
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
