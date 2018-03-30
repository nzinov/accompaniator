from time import sleep
from mido import Message, MidiFile, MidiTrack
from structures import Note, Chord
from multiprocessing.dummy import Queue, Process, Value
import alsaaudio
import numpy as np
from aubio import notes, onset, tempo
import time
import aubio

"""
Writing in file
1. playchord()
2. setupinstrument()
3. savefile() - to check the correctness of opening and recording
4. stop()
"""


def runqueue(picker, tmp):
    samplerate = 44100
    win_s = 256
    hop_s = win_s // 2
    framesize = hop_s

    # установка микрофона
    recorder = alsaaudio.PCM(type=alsaaudio.PCM_CAPTURE)
    recorder.setperiodsize(framesize)
    recorder.setrate(samplerate)
    recorder.setformat(alsaaudio.PCM_FORMAT_FLOAT_LE)
    recorder.setchannels(1)

    notes_o = notes("default", win_s, hop_s, samplerate)
    onset_o = onset("default", win_s, hop_s, samplerate)
    temp_o = tempo("specdiff", win_s, hop_s, samplerate)
    last_onset = 0
    beats = []
    last_beat = 0

    print("Starting to listen, press Ctrl+C to stop")

    now = time.time()
    # поток считывается пока вы не нажмете на стоп
    while picker.runing is True:
        # read data from audio input
        _, data = recorder.read()
        # конвертим data в aubio float samples
        samples = np.fromstring(data, dtype=aubio.float_type)
        # высота нынешнего frame
        if (onset_o(samples[0])):
            last_onset = int(onset_o.get_last_ms())
        if (temp_o(samples[0])):
            tmp = int(temp_o.get_last_ms())
            beats.append(tmp - last_beat)
            last_beat = tmp
        new_note = notes_o(samples[0])
        bpm = np.median(beats[-10:])
        picker.queue_in.put(Chord([new_note[0]], (last_onset / bpm), new_note[1]))

        now = time.time()


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
