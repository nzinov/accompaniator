import time
import sys
import numpy as np
import aubio
import pyaudio
from aubio import notes, onset, tempo
from time import sleep
from mido import Message, MidiFile, MidiTrack
from rtmidi import MidiOut
from structures import Note, Chord
from multiprocessing.dummy import Queue, Process, Value

default_tempo = 124
default_instrument = 30
min_velocity = 0
default_port = 0
delay = 0.000000001
sec_in_hour = 3600
max_time = sys.float_info.max

samplerate = 44100
win_s = 256
hop_s = win_s // 2
framesize = hop_s

"""
deadline is the time in seconds since the beginning of the era, float
delay is needed to change deadline
"""

def run_queue_out(player):
    while (player.runing.value):
        sleeping_time = player.get_sleeping_time()
        if sleeping_time < sec_in_hour:
            if sleeping_time > 0:
                sleep(sleeping_time)
            if (not player.queue_out.empty()):
                player.play_chord()         
    
def from_ms_to_our_time(time, bpm):
    return int(time * (128 * 60 * 1000) / bpm)

def run_queue_in(listener):
    
    listener.tempo.value = 124
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

    # the stream is read until you call stop
    t = time.time()
    while (listener.runing.value):
        print(time.time() - t)
        t = time.time()
        # read data from audio input
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
                listener.set_tempo(np.median(beats))
            listener.queue_in.put(Chord([Note(int(new_note[0]))], from_ms_to_our_time(last_onset, listener.tempo.value), int(new_note[1])))
            listener.set_deadline(time.time())
            
            
class Player:
    def __init__(self, queue, runing, tempo, deadline):
        self.midiout = MidiOut()
        self.midi_for_file = MidiFile()
        
        self.queue_out = queue
        self.runing = runing
        self.tempo = tempo
        self.deadline = deadline        
    
    def play_chord(self):
        
        chord = self.queue_out.get()
        
        if self.last_chord != None:
            for note in self.last_chord.value.notes:
                note_off = Message('note_off', note=note.number, velocity=min_velocity).bytes()
                self.midiout.send_message(note_off)
        
        for note in chord.notes:
            note_on = Message('note_on', note=note.number, velocity=chord.velocity).bytes()
            self.midiout.send_message(note_on)
            
        self.last_chord = Value('last_chord', chord)

        sleep(chord.len_in_ms(self.tempo.value) / 1000)
        
        if self.last_chord.value == chord:
            for note in chord.notes:
                note_off = Message('note_off', note=note.number, velocity=min_velocity).bytes()
                self.midiout.send_message(note_off)   
        
    def put(self, chord):
        if type(chord) == Chord:
            self.queue_out.put(chord)
            return True
        return False
    
    def set_up_ports(self):
        """ This is necessary to HEAR the music """
        available_ports = self.midiout.get_ports()
        if available_ports:
            self.midiout.open_port()
        else:
            self.midiout.open_virtual_port("Tmp virtual output") 
             
    def set_up_instrument(self, program=default_instrument):
        program_change = Message('program_change', program=program).bytes()
        self.midiout.send_message(program_change)       
    
    def set_up_midi_for_file(self):
        self.midi_for_file.tracks.append(MidiTrack()) 
        
    def get_sleeping_time(self):
        return self.deadline.value - time.time()
    
    def get_track(self):
        return self.midi_for_file.tracks[0]
    
    def save_file(self, filename='my track.mid'):
        self.midi_for_file.save(filename)
        return filename
        
    def run(self):
        self.set_up_ports()
        self.set_up_midi_for_file()
        self.set_up_instrument()
        
        self.process = Process(target=run_queue_out, args=(self, ))
        self.process.start()
        
    def stop(self):
        """ All chords that already sound will continue to sound """
        self.process.join()
        
    queue_out = None
    runing = None
    tempo = None
    deadline = None
    
    process = None
    midiout = None
    midi_for_file = None
    last_chord = None  
    
class Listener:
    def __init__(self, queue, runing, tempo, deadline):
        self.queue_in = queue
        self.runing = runing
        self.tempo = tempo
        self.deadline = deadline      

    def run(self):
        self.process = Process(target=run_queue_in, args=(self, ))
        self.process.start()

    def stop(self):
        self.process.join()

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

class Accompanist:
    def __init__(self):
        self.queue = Queue()
        self.runing = Value('runing', False)
        self.tempo = Value('tempo', default_tempo)
        self.deadline = Value('deadline', max_time, lock=False)
        
        self.player = Player(self.queue, self.runing, self.tempo, self.deadline)
        self.listener = Listener(self.queue, self.runing, self.tempo, self.deadline)        
    
    def run(self):
        self.runing.value = True
        self.listener.run()
        self.player.run()
        
    def stop(self):
        self.runing.value = False
        self.player.stop()
        self.listener.stop()        
        self.queue = Queue()
        
    def set_tempo(self, tempo=default_tempo):
        self.tempo.value = tempo
        
    def set_deadline(self, deadline=max_time):
        self.deadline.value = deadline
         
    player = None
    listener = None
    queue = None
    runing = None
    tempo = None
    deadline = None

if __name__ == '__main__':
    a = Accompanist()
    '''q = a.player
    start_time = time.time()
    a.run()
    chord = Chord([60, 64, 67, 72], 64, 120)    
    q.put(chord)
    chord = Chord([76], 64, 120)    
    q.put(chord)    
    a.set_deadline(start_time + 2)
    sleep(2)
    a.set_deadline(start_time + 3.5)
    '''
    
    '''q = a.listener
    a.run()
    sleep(1)
    b = q.get()
    print(b)
    a.stop()
    print("Stopped")
    '''

    start_time = time.time()
    a.run()
    sleep(10)
    a.stop()
    