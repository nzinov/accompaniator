from time import sleep
from mido import Message, MidiFile, MidiTrack
from structures import Note, Chord
from multiprocessing.dummy import Queue, Process, Value
import alsaaudio
import numpy as np
import aubio
import time

"""
Writing in file
1. playchord()
2. setupinstrument()
3. savefile() - to check the correctness of opening and recording
4. stop()
"""


def runqueue(picker, tmp):
    samplerate = 44100
    win_s = 2048
    hop_s = win_s // 2
    framesize = hop_s

    # установка микрофона
    recorder = alsaaudio.PCM(type=alsaaudio.PCM_CAPTURE)
    recorder.setperiodsize(framesize)
    recorder.setrate(samplerate)
    recorder.setformat(alsaaudio.PCM_FORMAT_FLOAT_LE)
    recorder.setchannels(1)

    # create aubio pitch detection (first argument is method, "default" is
    # "yinfft", can also be "yin", "mcomb", fcomb", "schmitt").
    pitcher = aubio.pitch("fcomb", win_s, hop_s, samplerate)
    # set output unit (can be 'midi', 'cent', 'Hz', ...)
    pitcher.set_unit("midi")
    # ignore frames under this level (dB)
    pitcher.set_silence(-40)

    print("Starting to listen, press Ctrl+C to stop")

    now = time.time()
    # поток считывается пока вы не нажмете на стоп
    while picker.runing is True:
        # read data from audio input
        _, data = recorder.read()
        # конвертим data в aubio float samples
        samples = np.fromstring(data, dtype=aubio.float_type)
        # высота нынешнего frame
        midi = int(pitcher(samples)[0])
        # они считают магически энергию, по тому что я пробовал, это похоже на громкость
        energy = np.sum(samples ** 2) / len(samples)
        #print(midi)
        # кидаем в массив частот энергии и времени
        picker.queue_in.put(Chord([midi], time.time() - now, 127))
        
        now = time.time()


class PickFromMick:
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
    q = PickFromMick()
    q.run()
    sleep(1)
    a = q.get()
    print(a)
    q.stop()
    print("Stopped")
