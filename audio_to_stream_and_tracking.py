import pyaudio
import wave
import sys
import subprocess
import io

CHUNK = 1024

name = "Whisper"


file_name = "Whisper.wav"

wf = wave.open(file_name, 'rb')

# instantiate PyAudio (1)
p = pyaudio.PyAudio()

# open stream (2)


sample_rate = 44100
frame_size = 2048
hop_size = 441
fps = 100
num_channels = 1

stream = p.open(rate=sample_rate,
                           channels=num_channels,
                           format=pyaudio.paFloat32, output=True,
                           frames_per_buffer=hop_size,
                           start=True)



BT = subprocess.Popen('python3 madmom_bins/DBNBeatTracker online', shell=True, stdout=subprocess.PIPE)
# read data
data = wf.readframes(CHUNK)

# play stream (3)
beats_stream = io.StringIO
while len(data) > 0:
    stream.write(data)
    data = wf.readframes(CHUNK)
    print(str(BT.stdout.readline())[2:-3])

# stop stream (4)
stream.stop_stream()
stream.close()

# close PyAudio (5)
p.terminate()