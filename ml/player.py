from time import sleep
from mido import Message, MidiFile, MidiTrack
from rtmidi import MidiOut
from structures import Note, Chord 
from multiprocessing import Queue

"""
Important problems
1. I have to learn parallel programming on python:
sleep() in playchord() is not OK. I think it stops all the programm
2. How should I meachure time to get chord from the queue on right time?
3. It's test vertion of my programm, so
now I play chords as soon as they are put to queue

Additional problems
Writing in file has a lot of problems
"""

class Player:
    
    def __init__(self):
        self.queue = Queue()
        self.midiout = MidiOut()
        self.midiforfile = MidiFile()
    
    # TODO NOT NOW writing in file
    def playchord(self):
        
        chord = self.queue.get()
        
        for note in chord.notes:
            note_on = Message('note_on', note=note.number, velocity=chord.velocity).bytes()
            self.midiout.send_message(note_on)
        # TODO
        sleep(chord.duration)    
        for note in chord.notes:
            note_off = Message('note_off', note=note.number, velocity=0).bytes()
            self.midiout.send_message(note_off)       
        
    def put(self, chord):
        if type(chord) == Chord:
            self.queue.put(chord)
            return True
        return False
    
    """ this is necessary to HEAR the music """
    def setupports(self):
        available_ports = self.midiout.get_ports()
        if available_ports:
            self.midiout.open_port(0)
        else:
            self.midiout.open_virtual_port("Tmp virtual output") 
             
    # TODO NOT NOW writing in file
    def setupinstrument(self, program=30):
        program_change = Message('program_change', program=program).bytes()
        self.midiout.send_message(program_change)       
    
    def setupinmidiforfile(self):
        self.midiforfile.tracks.append(MidiTrack()) 
        
    def gettrack(self):
        return self.midiforfile.tracks[0]
    
    # TODO NOT NOW to check the correctness of opening and recording
    def savefile(self, filename='my track.mid'):
        self.midiforfile.save(filename)
        return filename
        
    def run(self):
        
        self.setupports()
        self.setupinmidiforfile()
        self.setupinstrument()
        
        #TODO
        #while(True):
        #    if(not self.queue.empty()):
        while (not self.queue.empty()):
                self.playchord()
        return
    
    queue = None
    midiout = None
    midiforfile = None
    

q = Player()
chord = Chord([Note(60), Note(64), Note(67), Note(72)], 1, 120)
q.put(chord)
q.run()