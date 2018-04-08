from time import sleep
from mido import Message, MidiFile, MidiTrack
from structures import Note, Chord
from multiprocessing.dummy import Queue, Process, Value
import numpy as np
from aubio import notes, onset, tempo

import aubio
import pyaudio


def from_ms_to_our_time(time, bpm):
    return int(time * (128 * 60 * 1000) / bpm)


def runqueue(picker, tmp):
    samplerate = 44100
    bpm = 124
    win_s = 256
    hop_s = win_s // 2
    framesize = hop_s
    p = pyaudio.PyAudio()

    # open stream
    buffer_size = 128
    pyaudio_format = pyaudio.paFloat32
    n_channels = 1
    stream = p.open(format=pyaudio_format,
                    channels=n_channels,
                    rate=samplerate,
                    input=True,
                    frames_per_buffer=buffer_size)

    notes_o = notes("default", win_s, hop_s, samplerate)
    onset_o = onset("default", win_s, hop_s, samplerate)
    temp_o = tempo("specdiff", win_s, hop_s, samplerate)
    last_onset = 0
    beats = []
    last_beat = 0

    print("Starting to listen, press Ctrl+C to stop")

    # поток считывается пока вы не нажмете на стоп
    while picker.runing is True:
        # read data from audio input
        #_, data = recorder.read()
        audiobuffer = stream.read(buffer_size)
        samples = np.fromstring(audiobuffer, dtype=np.float32)

        if (onset_o(samples)):
            last_onset = int(onset_o.get_last_ms())
        if (temp_o(samples)):
            tmp = int(temp_o.get_last_ms())
            beats.append(int(tmp - last_beat))
            last_beat = tmp
        new_note = notes_o(samples)
        if (new_note[0] != 0):
            if (len(beats) != 0):
                bpm = np.median(beats)
            #print(new_note[0], last_onset, new_note[1])
            picker.queue_in.put(Chord([new_note[0]], last_onset, new_note[1]))




class Listener:
    def __init__(self):
        self.queue_in = Queue()
        runing = False

    def run(self):
        self.runing = True
        self.process = Process(target=runqueue, args=(self, self.runing))
        self.process.start()

    def stop(self):
        self.runing = False
        self.process.join()

        self.queue_in = Queue()

    def get(self):
        if self.queue_in.empty() is False:
            return self.queue_in.get()

    queue_in = None
    runing = None


if __name__ == '__main__':
    q = Listener()
    q.run()
    sleep(1)
    a = q.get()
    print(a)
    q.stop()
    print("Stopped")
