import subprocess
from madmom.io.audio import decode_to_pipe, decode_to_disk;
import io;
import pyaudio
import wave
from pydub import AudioSegment

file_name = "Whisper.mp3"
sample_rate = 44100
frame_size = 2048
hop_size = 441
fps = 100
num_channels = 1

# Вот основной вариант.
# Ориентировался я вот на что: если внимательно вчитаться в madmom.io.audio.py (новой версии), в методы decode_to_pipe
# и decode_to_memory, то можно увидеть, что у них есть отдельный случай, если файл - instance ихнего класса Signal.
# В этом случае, если я правильно понял, в методе decode_to_memory отправляется на stdin decode_to_pipe-a
# обработанный файл, и дальше он обрабатывается уже им. Вот туда я хотел встрять и сделать чтение из пайпа, но не понял,
# каким образом это сделать и в каком месте должен возникать наш внедренный Signal.



with open(file_name, 'rb') as infile:
    outp = subprocess.Popen(['ffmpeg', '-i', '-', '-f', 'mp3', '-'], stdin=infile, stdout=subprocess.PIPE)
    args = ['python', 'madmom-master/bin/DBNBeatTracker.py', 'single', 'pipe:0', 'worker']# Если что, внутренности
    #madmom-master/bin/DBNBeatTracker.py такие же, как и бинарника; я пытался и туда встрять как-нибудь безрезультатно

    BT = subprocess.Popen(args, stdin=outp.stdout, stdout=subprocess.PIPE)

    for i in range(0, 2):
        print(str(BT.stdout.readline())[2:-3])

# Ниже попытки реализовать покусочные предсказания, типа записали сколько-то фреймов - записали в маленький файлик
# и скормили мэдмому, но получилось медленно и хреново.


"""
#wf = wave.open(file_name, 'rb')
#nchannels = wf.getnchannels()
#sampwidth = wf.getsampwidth()
#framerate = wf.getframerate()

args = ['python', 'madmom-master/bin/DBNBeatTracker.py', 'single', 'tmp.wav']

#nframes = wf.getnframes()

song = AudioSegment.from_mp3("Whisper.wav")
frame_size = 2000
song_length = len(song)//frame_size
last_one = 0.0
for i in range(0, song_length):

    #wf2 = wave.open("tmp.wav", 'w')
    #wf2.setnchannels(nchannels)
    #wf2.setsampwidth(sampwidth)
    #wf2.setframerate(framerate)
    #wf2.writeframes(wf.readframes(frame_size*40))
    #wf2.close()

    short_segment = song[i*frame_size: (i+1)*frame_size]
    short_segment.export("madmom-master/bin/tmp.mp3", format="mp3")
    BT = subprocess.Popen(args, stdout=subprocess.PIPE)
    prev_output = ""
    output=str(BT.stdout.readline())[2:-3]
    while output !="":
        print(last_one+float(output))
        prev_output = output
        output = str(BT.stdout.readline())[2:-3]
    last_one += float(prev_output)

    # print(str(BT.stdout.readline())[2:-3])


"""

"""
with open('Whisper.mp3', 'rb') as infile:

    outp=subprocess.Popen(['ffmpeg', '-i', '-', '-f', 'mp3', '-'], stdin=infile, stdout=subprocess.PIPE)
    args = ['python', 'madmom-master/bin/DBNBeatTracker.py', 'single', 'pipe:0', 'worker']

    BT = subprocess.Popen(args, stdin=outp.stdout, stdout=subprocess.PIPE)

    for i in range(0,2):
        print(str(BT.stdout.readline())[2:-3])
"""
"""
out, outproc = decode_to_pipe(file_name, sample_rate=sample_rate);

p = pyaudio.PyAudio()

# open stream based on the wave object which has been input.
stream = p.open(rate=sample_rate,
                           channels=num_channels,
                           format=pyaudio.paFloat32, output=True,
                           frames_per_buffer=hop_size,
                           start=True)

for i in range(0,100):
    fbytes = io.BytesIO(outproc.stdout.read(frame_size))
    fwave = wave.open(fbytes, 'r')
    data = fwave.readframes(2048)
    stream.write(data)*/


    #str = outproc.stdout.read(frame_size);
    #print(str);
"""

