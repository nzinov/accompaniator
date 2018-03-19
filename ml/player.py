from time import sleep
from mido import Message, MidiFile, MidiTrack
from rtmidi import MidiOut
from structures import Note, Chord
from multiprocessing.dummy import Queue, Process, Value

"""
Writing in file
1. playchord()
2. setupinstrument()
3. savefile() - to check the correctness of opening and recording
4. stop()
"""

def runqueue(player, bpmvalue):
    player.setupports()
    player.setupinmidiforfile()
    player.setupinstrument()
        
    while(player.runing):
        if(not player.queue.empty()):
            player.playchord(bpmvalue)    

class Player:
    
    def __init__(self, bpm=0):
        self.queue = Queue()
        self.midiout = MidiOut()
        self.midiforfile = MidiFile()
        runing = False
        self.bpmvalue = Value('bpm', bpm)
    
    def playchord(self, bpmvalue):
        
        chord = self.queue.get()
        
        for note in chord.notes:
            note_on = Message('note_on', note=note.number, velocity=chord.velocity).bytes()
            self.midiout.send_message(note_on)

        sleep(chord.len_in_ms(bpmvalue.value) / 1000)    
        
        for note in chord.notes:
            note_off = Message('note_off', note=note.number, velocity=0).bytes()
            self.midiout.send_message(note_off)       
        
    def put(self, chord):
        if type(chord) == Chord:
            self.queue.put(chord)
            return True
        return False
    
    def setupports(self):
        """ This is necessary to HEAR the music """
        available_ports = self.midiout.get_ports()
        if available_ports:
            self.midiout.open_port(0)
        else:
            self.midiout.open_virtual_port("Tmp virtual output") 
             
    def setupinstrument(self, program=30):
        program_change = Message('program_change', program=program).bytes()
        self.midiout.send_message(program_change)       
    
    def setupinmidiforfile(self):
        self.midiforfile.tracks.append(MidiTrack()) 
        
    def gettrack(self):
        return self.midiforfile.tracks[0]
    
    def savefile(self, filename='my track.mid'):
        self.midiforfile.save(filename)
        return filename
        
    def run(self):
        self.runing = True
        self.process = Process(target=runqueue, args=(self, self.bpmvalue))
        self.process.start()
        
    def stop(self):
        """ All chords that already sound will continue to sound """
        self.runing = False
        self.process.join()
        
        self.queue = Queue()        
    
    queue = None
    process = None
    midiout = None
    midiforfile = None
    runing = None
    bpmvalue = None
    
if __name__ == '__main__':
    q = Player(240000000)
    q.run()
    chord = Chord([Note(60), Note(64), Note(67), Note(72)], 32, 120)    
    q.put(chord)
    chord = Chord([], 32, 0)
    q.put(chord)
    chord = Chord([Note(60), Note(64), Note(67), Note(72)], 32, 120)    
    q.put(chord)
    sleep(1)
    q.stop()
