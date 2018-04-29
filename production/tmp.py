
import pyaudio
import numpy as np
import aubio

from mido import Message, MidiFile, MidiTrack
import wave
from aubio import notes, onset, tempo


sample_rate = 44100
win_s = 2048
hop_s = win_s // 4
buffer_size = hop_s


p = pyaudio.PyAudio()
# open stream
pyaudio_format = pyaudio.paFloat32
n_channels = 1
stream = p.open(format=pyaudio_format,
                channels=n_channels,
                rate=sample_rate,
                input=True,
                frames_per_buffer=buffer_size)

wavefile = wave.open("your_voice.wav", "w")
wavefile.setnchannels(n_channels)
wavefile.setsampwidth(p.get_sample_size(pyaudio_format))
wavefile.setframerate(sample_rate / 2)

notes_o = notes("default", win_s, hop_s, sample_rate)
onset_o = onset("default", win_s, hop_s, sample_rate)

max = 300
cnt = 0
last_onset = 0

mid = MidiFile()
tracks = []
num = 0
while (cnt < max):
    # read data from audio input
    audiobuffer = stream.read(buffer_size, exception_on_overflow=False)
    print(audiobuffer)
    samples = np.fromstring(audiobuffer, dtype=np.float32)
    prom = np.int16((samples + 1) * (2**16))
    print(prom)
    toOut = bytes(prom)
    wavefile.writeframes(toOut)
    cnt += 1
    if (onset_o(samples)):
        last_onset = int(onset_o.get_last_ms())
    new_note = notes_o(samples)
    if (new_note[0] != 0):
        tracks.append(MidiTrack())
        mid.tracks.append(tracks[num])
        new_note[0] = int(new_note[0])
        tracks[num].append(Message('program_change', program=33, time=10))
        nn = int(new_note[0])
        tracks[num].append(Message('note_on', note=nn, velocity=124, time=last_onset))
        tracks[num].append(Message('note_off', note=nn, velocity=0, time=int(new_note[1])))
        tracks[num].append(Message('note_on', note=(nn + 12) % 128, velocity=124, time=last_onset))
        tracks[num].append(Message('note_off', note=(nn + 12) % 128, velocity=0, time=int(new_note[1])))
        num += 1
    print(cnt)

wavefile.close()
mid.save('zmey.midi')
