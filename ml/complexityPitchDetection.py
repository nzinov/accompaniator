from time import sleep
from structures import Note, Chord
from multiprocessing.dummy import Queue, Process, Value
import pyaudio
import struct
import numpy as np
import time
from scipy.fftpack import fft
import wave

CHUNK = 1024
CHANNELS = 2
RATE = 44100
FORMAT = pyaudio.paInt16

threshold = 0.3
k = 2
tonality_shift = 1.
low_freq = 120.
high_freq = 520.
chunk = CHUNK * CHANNELS
FREQUENCY_CONSTANT = RATE / 4096
frequency_coef = FREQUENCY_CONSTANT * tonality_shift


def loud_freqs(y_fft):
    lowest_freq = int(round(low_freq / frequency_coef))
    highest_freq = int(high_freq / frequency_coef) + 1
    Q = np.arange(lowest_freq, highest_freq)
    our_fft = np.abs(y_fft[lowest_freq:highest_freq])
    assert len(Q) == len(our_fft)
    if k is None:
        if threshold >= 1:
            W = Q[our_fft > threshold] * frequency_coef
            L = our_fft[our_fft > threshold]
        else:
            W = Q[our_fft > our_fft.max() * threshold] * frequency_coef
            L = our_fft[our_fft > our_fft.max() * threshold]
    else:
        E = list(enumerate(our_fft))
        E.sort(key=lambda x: -x[1])
        sorted_idx = [x[0] for x in E]
        peaks_only = []
        for i in range(len(sorted_idx)):
            x = sorted_idx[i]
            if x - 1 in sorted_idx[:max(0, i - 3)] or x + 1 in sorted_idx[:max(0, i - 3)] \
                    or x - 2 in sorted_idx[:i] or x + 2 in sorted_idx[:i]:
                continue
            peaks_only.append(x)
        peaks_only = peaks_only[:k]
        W = Q[peaks_only] * frequency_coef
        L = our_fft[peaks_only]

    return W, L

silent_midi = 0


def frequency_to_midi(frequency):
    if (frequency < 0.1):
        return silent_midi
    else:
        return np.int_(np.round(12 * np.log2(frequency / 440) + 69))


def myFFT(data_pieces, window='gaussian'):
    data = []
    for j in range(4):
        data = data + list(data_pieces[j])
    data = np.array(data, dtype='b').astype(np.int32)
    data_np = data[::2] + 256 * data[1::2]

    if window == 'rectangular':
        window_function = np.ones(CHUNK)
    if window == 'hamming':
        window_function = 0.54 - 0.46 * np.cos(2 * np.pi * np.arange(CHUNK)) / (CHUNK - 1)
    if window == 'gaussian':
        A = (CHUNK - 1) / 2.
        sigma = 2.5
        window_function = np.exp(-0.5 * ((CHUNK - A) / (sigma * A)) ** 2)

    if CHANNELS == 1:
        data_for_fft = data_np
    if CHANNELS == 2:
        data_for_fft = (data_np[::2] + data_np[1::2]) / 2. * window_function
    y_fft = np.fft.fft(data_for_fft)
    y_fft = y_fft[:CHUNK // 2]
    return y_fft


def runqueue(picker, tmp):
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        output=True,
        frames_per_buffer=CHUNK
    )
    chunk = CHUNK * CHANNELS

    frames = []
    print('record started')

    numbers = []
    times = []
    lengths = []
    start_time = time.time()
    now_time = time.time()
    last = []
    while (picker.runing):
        data = stream.read(CHUNK)
        data_int = struct.unpack(str(2 * chunk) + 'B', data)
        data_np = np.array(data_int, dtype='b')[::2] + 128
        y_fft = fft(data_np)
        last.append(data_int)

        if (len(last) >= 4):
            y_fft = myFFT(last[len(last) - 4:])

        freq, vol = loud_freqs(y_fft)
        midi = frequency_to_midi(freq[0])
        picker.queue_in.put(Chord([midi], time.time() - now_time, 127))
        now_time = time.time()


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
