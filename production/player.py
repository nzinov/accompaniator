import time
import sys
import scipy
import numpy as np
from time import sleep
from mido import Message, MidiFile, MidiTrack
from rtmidi import MidiOut
from structures import Note, Chord
from multiprocessing import Queue, Process, Value

"""
1 beat in bpm is 1/4 of musical beat
distance_between_peaks is the time in seconds
deadline is the time in seconds since the beginning of the era, float
delay is needed to change deadline
"""

distance_between_peaks = 2
default_peak_time = 0.1
default_peak_number = 60
default_peak_velocity = 120
default_channel = 0
default_ultrasound_channel = 1
default_tempo = 124
default_instrument = 40
28
default_ultrasound_instrument = 2
min_velocity = 0
default_port = 1
delay = 0.000000001
sec_in_hour = 3600
max_time = sys.float_info.max
empty_chord = Chord([], 0, 0)

def len_in_s(duration, bpm):
    """ Returns length of chord in s given beats per minute"""
    return duration * 60 / (bpm * 32)

def run_peak(player):
    while(player.running.value):
        sleep(distance_between_peaks)
        player.start_peak.value = time.monotonic()
        #player.play_peak()
    
def run_queue_out(player):
    while (player.running.value):
        if not player.queue_out.empty() and time.monotonic() > player.deadline.value:
            """ track is array of pairs: first is note number in chord, second is note len (duration) in 1/128. Sum of durations MUST be equal to 128 """
            player.play_chord_arpeggio(np.array([[0, 19], [1, 18], [2, 18], [3, 18], [2, 18], [1, 18], [0, 19]]))
        time.sleep(0.01)


class Player:
    def __init__(self, queue=Queue(), running=Value('i', False), tempo=Value('f', default_tempo), deadline=Value('f', 0)):
        self.midiout = MidiOut()
        self.midi_for_file = MidiFile()
        self.last_chord = empty_chord
        
        self.queue_out = queue
        self.running = running
        self.tempo = tempo
        self.deadline = deadline
        self.start_peak = Value('f', 0)  
        self.start_chord = 0 
        
    def play_peak(self, number=default_peak_number, velocity=default_peak_velocity):
        note_on = Message('note_on', note=number, velocity=velocity, channel=default_ultrasound_channel).bytes()
        self.midiout.send_message(note_on)
        sleep(default_peak_time)
        note_off = Message('note_off', note=number, velocity=min_velocity, channel=default_ultrasound_channel).bytes()
        self.midiout.send_message(note_off)      
    
    def play_chord_same_time(self):
        
        chord = self.queue_out.get()
        print("player get", chord, "vel", chord.velocity, "queue", self.queue_out.qsize(), "time", time.monotonic())
        
        if chord.velocity > 127:
            chord.velocity = 127
        if chord.duration == 0:
            return
        for note in chord.notes:
            if note.number > 127:
                print("an incorrect note in player")
                return
       
        if self.last_chord != empty_chord:
            for note in self.last_chord.notes:
                note_off = Message('note_off', note=note.number, velocity=min_velocity, channel=default_channel).bytes()
                self.midiout.send_message(note_off)
        
        for note in chord.notes:
            note_on = Message('note_on', note=note.number, velocity=chord.velocity, channel=default_channel).bytes()
            self.midiout.send_message(note_on)
            
        self.last_chord = chord

        sleep(len_in_s(chord.duration, self.tempo.value))
        
        if self.last_chord == chord: 
            for note in chord.notes:
                note_off = Message('note_off', note=note.number, velocity=min_velocity, channel=default_channel).bytes()
                self.midiout.send_message(note_off)       

    def play_chord_arpeggio(self, track=np.array([])):
        
        chord = self.queue_out.get()
        print("player get", chord, "vel", chord.velocity, "queue", self.queue_out.qsize(), "time", time.monotonic())
        chord.notes = sorted(chord.notes)
        if len(chord.notes) == 3:
            chord.notes.append(Note(chord.notes[0].number + 12))
        if track == np.array([]):
            notes_numbers = np.arange(len(chord.notes))
            notes_durations = np.array([int(128/len(chord.notes)) for i in range(len(chord.notes))])
            track = np.column_stack((notes_numbers, notes_durations))
        if chord.velocity > 127:
            chord.velocity = 127
        if chord.duration == 0:
            return
        for note in chord.notes:
            if note.number > 127:
                print("an incorrect note in player")
                return

        notes_sum_durations = scipy.cumsum(track.transpose(), axis=1)[1]
        if (self.last_note_number != None):
            note_off = Message('note_off', note=self.last_note_number, velocity=min_velocity, channel=default_channel).bytes()
            self.midiout.send_message(note_off)
        self.start_chord = time.monotonic()
        pair = 0
        note_number = track[pair][0]
        note_on = Message('note_on', note=chord.notes[note_number].number, velocity=chord.velocity, channel=default_channel).bytes()
        self.midiout.send_message(note_on)
        while (pair < len(track) - 1):
            #TODO
            if time.monotonic() > self.start_chord + max((self.deadline.value -self.start_chord) * notes_sum_durations[pair] / notes_sum_durations[-1], len_in_s(notes_sum_durations[pair], self.tempo.value)):
                note_off = Message('note_off', note=chord.notes[note_number].number, velocity=min_velocity, channel=default_channel).bytes()
                self.midiout.send_message(note_off)
                pair += 1
                note_number = track[pair][0]
                note_on = Message('note_on', note=chord.notes[note_number].number, velocity=chord.velocity, channel=default_channel).bytes()
                self.midiout.send_message(note_on)
                self.last_note_number = chord.notes[note_number].number
            time.sleep(0.01)

    def put(self, chord):
        if type(chord) == Chord:
            self.queue_out.put(chord)
            return True
        return False
    
    def set_up_ports(self):
        """ This is necessary to HEAR the music """
        available_ports = self.midiout.get_ports()
        if available_ports:
            self.midiout.open_port(default_port)
        else:
            self.midiout.open_virtual_port("Tmp virtual output") 
             
    def set_up_instrument(self, program=default_instrument):
        program_change = Message('program_change', program=program, channel=default_channel).bytes()
        self.midiout.send_message(program_change)  
        
    def set_up_ultrasound_instrument(self, program=default_ultrasound_instrument):
        program_change = Message('program_change', program=program, channel=default_ultrasound_channel).bytes()
        self.midiout.send_message(program_change)     
    
    def set_up_midi_for_file(self):
        self.midi_for_file.tracks.append(MidiTrack()) 
        
    def set_tempo(self, tempo=default_tempo):
        self.tempo.value = tempo
        
    def set_deadline(self, deadline=0):
        self.deadline.value = deadline
    
    def set_start_peak(self, start=max_time):
        self.start_peak.value = start   
        
    def get_sleeping_time(self):
        return self.deadline.value - time.monotonic()
        
    def get_track(self):
        return self.midi_for_file.tracks[0]
    
    def save_file(self, filename='my track.mid'):
        self.midi_for_file.save(filename)
        return filename
        
    def run(self):
        self.running.value = True
        self.set_up_ports()
        self.set_up_midi_for_file()
        self.set_up_instrument()
        self.set_up_ultrasound_instrument()
        
        self.queue_process = Process(target=run_queue_out, args=(self, ))
        self.queue_process.start()
        
        self.queue_process = Process(target=run_peak, args=(self, ))
        self.queue_process.start()        
        
    def stop(self):
        """ All chords that already sound will continue to sound """
        self.running.value = False
        self.queue_process.join()
        self.queue_process.join()  
        self.queue_out = Queue()
        
    queue_out = None
    running = None
    tempo = None
    deadline = None
    start_peak = None
    start_chord = None
    queue_process = None
    peak_process = None
    midiout = None
    midi_for_file = None
    last_chord = None
    last_note_number = None 
    
if __name__ == '__main__':
    q = Player()
    t = time.monotonic()
    q.run()
    #chord = Chord([Note(60), Note(64)], 512, 120)    
    #q.put(chord)
    chord = Chord([Note(76)], 4, 80)    
    q.put(chord)    
    q.set_deadline(t)
    sleep(delay)
    #q.set_deadline(t + 3.5)
    sleep(10)
    q.stop()
    
