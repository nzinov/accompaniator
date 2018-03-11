# ! sudo pip install time
# ! sudo pip install pyalsaaudio
# (перед этим  On  Debian or Ubuntu, install  libasound2 - dev.    On
# ! Arch, install    alsa - lib.а     если    будут    еще    проблемы,
#   то    https: // github.com / larsimmisch / pyalsaaudio)
# ! sudo pip install aubio
# ! А если еще что-то не понятно, то есть набор примеров, нормальной документации у них нет
# ! https: // github.com / aubio / aubio / blob / master / python / demos / demo_alsa.py
# ! Как работает запись: пишется все риалтайме,
#  так чтобы получить порцию данных запустите первый блок, спойте/поставьте музыку, нажмите на стоп


import alsaaudio
import numpy as np
import aubio
import time


silent_midi = -1  # если не слышно или просто ничего не звучит, то выдавать это midi


def frequency_to_midi(frequency):
    if (frequency < 0.1):
        return silent_midi
    else:
        return np.int_(np.round(12 * np.log2(frequency / 440) + 69))


# constants
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
pitcher = aubio.pitch("default", win_s, hop_s, samplerate)
# set output unit (can be 'midi', 'cent', 'Hz', ...)
pitcher.set_unit("Hz")
# ignore frames under this level (dB)
pitcher.set_silence(-20)  # изначально стоит -40,
#  но из-за этого пишутся лишние шумы, я поставил на -20 может еще поднять

print("Starting to listen, press Ctrl+C to stop")

freq = np.array([])
energy = np.array([])
now = time.time()
times = np.array([])
midi = np.array([])
# поток считывается пока вы не нажмете на стоп
while True:
    try:
        # read data from audio input
        _, data = recorder.read()
        # конвертим data в aubio float samples
        samples = np.fromstring(data, dtype=aubio.float_type)
        # высота нынешнего frame
        freq_now = pitcher(samples)[0]
        # они считают магически энергию, по тому что я пробовал, это похоже на громкость
        energy_now = np.sum(samples ** 2) / len(samples)
        # кидаем в массив частот энергии и времени
        freq = np.append(freq, freq_now)
        energy = np.append(energy, energy_now)
        times = np.append(times, time.time() - now)
        # я не знаю куда поставить считывание времени потому что если поставлю вначало,
        #  то очень большой разрыв с реальным временем будет
        midi = np.append(midi, frequency_to_midi(freq_now))

        now = time.time()
    except KeyboardInterrupt:
        break

n = len(freq)

chords = [[-1, 0]]

cnt = times[0]
for i in range(1, n):
    if (abs(midi[i] - midi[i - 1]) < 0.01):
        cnt += times[i]
    else:
        chords.append([midi[i - 1], cnt])
        cnt = times[i]

print(chords)
