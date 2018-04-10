import time
import sys
import numpy as np
import aubio
import pyaudio
from time import sleep
from mido import Message, MidiFile, MidiTrack
from multiprocessing import Queue, Process, Value
from aubio import notes, onset, tempo
from structures import Note, Chord

import wave

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
    
    p = pyaudio.PyAudio()
    # open stream
    '''pyaudio_format = pyaudio.paFloat32
    n_channels = 1
    stream = p.open(format=pyaudio_format,
                    channels=n_channels,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=buffer_size)
    '''
    s = aubio.source('/home/nikolay/pahanini.mp3', sample_rate, buffer_size)
    

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
    while (listener.runing.value):
        # read data from audio input
        audiobuffer, read = s()
        #audiobuffer = stream.read(buffer_size, exception_on_overflow = False)
        #samples = np.fromstring(audiobuffer, dtype=np.float32)
        samples = audiobuffer

        if (onset_o(samples)):
            last_onset = onset_o.get_last_ms()
        if (temp_o(samples)):
            tmp = temp_o.get_last_ms()
            beats.append(tmp - last_beat)
            count_beat = (count_beat + 1) % 4
            last_beat = tmp
            if (count_beat == 0):
                last_downbeat = last_beat
                bar_start = True
        new_note = notes_o(samples)
        if (new_note[0] != 0):
            if (len(beats) != 0):
                listener.set_tempo(60 * 1000.0 / np.median(beats))
            chord = Chord([Note(int(new_note[0]))], from_ms_to_our_time(last_onset - prev_time, listener.tempo.value), int(new_note[1]), bar_start)
            bar_start = False
            listener.queue_in.put(chord)
            listener.set_deadline(last_downbeat + (4 - count_beat) * 60 * 1000.0 / listener.tempo.value)
            #print(listener.tempo.value)
            prev_time = last_onset

class Listener:
    def __init__(self, queue=Queue(), runing=Value('i', False), tempo=Value('f', default_tempo), deadline=Value('f', max_time)):
        self.queue_in = queue
        self.runing = runing
        self.tempo = tempo
        self.deadline = deadline             

    def run(self):
        self.runing.value = True
        self.process = Process(target=run_queue_in, args=(self, ))
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
