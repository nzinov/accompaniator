import time
import sys
from time import sleep
from mido import Message, MidiFile, MidiTrack
from rtmidi import MidiOut
from structures import Note, Chord
from multiprocessing.dummy import Queue, Process, Value

"""
Writing in file
1. play_chord()
2. set_up_instrument()
3. save_file() - to check the correctness of opening and recording
4. stop()
"""

"""
deadline is the time in seconds since the beginning of the era, float
delay is needed to change deadline
"""

default_tempo = 240000000
default_instrument = 30
min_velocity = 0
default_port = 0
delay = 0.000000001
max_time = sys.float_info.max

def run_queue(player):
    player.set_up_tempo()
    player.set_up_deadline()    
    player.set_up_ports()
    player.set_up_midi_for_file()
    player.set_up_instrument()
    
    while (player.runing):
        sleeping_time = player.get_sleeping_time()
        if (sleeping_time > 0):
            sleep(sleeping_time)
        if (not player.queue.empty()):
            player.play_chord()    

class Player:
    
    def __init__(self):
        self.queue = Queue()
        self.midiout = MidiOut()
        self.midi_for_file = MidiFile()
        runing = False
    
    def play_chord(self):
        
        chord = self.queue.get()
        
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
            self.queue.put(chord)
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
        
    def set_up_tempo(self, tempo=default_tempo):
        self.tempo = Value('tempo', tempo)
        
    def set_up_deadline(self, deadline=max_time):
        self.deadline = Value('deadline', deadline)
        
    def get_sleeping_time(self):
        b = self.deadline.value
        c = time.time()
        return self.deadline.value - time.time()
        
    def get_track(self):
        return self.midi_for_file.tracks[0]
    
    def save_file(self, filename='my track.mid'):
        self.midi_for_file.save(filename)
        return filename
        
    def run(self):
        self.runing = True
        self.process = Process(target=run_queue, args=(self, ))
        self.process.start()
        
    def stop(self):
        """ All chords that already sound will continue to sound """
        self.runing = False
        self.process.join()
        self.queue = Queue()        
    
    queue = None
    process = None
    midiout = None
    midi_for_file = None
    runing = None
    tempo = None
    deadline = None
    last_chord = None
    
if __name__ == '__main__':
    q = Player()
    t = time.time()
    q.run()
    chord = Chord([Note(60), Note(64), Note(67), Note(72)], 64, 120)    
    q.put(chord)
    chord = Chord([Note(76)], 64, 120)    
    q.put(chord)    
    q.set_up_deadline(t + 1.5)
    sleep(delay)
    q.set_up_deadline(t + 3)
