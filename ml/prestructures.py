import pickle

class PreNote:
    """ Stores individual note
    Attributes:
        number: MIDI number of note
    """
    def __init__(self, number, duration, velocity):
        self.number = number
        self.velocity = velocity
        self.duration = duration

    def freq(self):
        """ Returns frequency in Hz """
        return 2**((self.number-69)/12.)*440

    def __str__(self):
        return "%s %s %s"%(self.number, self.duration, self.velocity)
    
    def __repr__(self):
        return self.__str__()
    
    number = None
    duration = None
    velocity = None


class PreChord:
    """Stores a chord and its length in 1/128 beats"""

    def __init__(self, delta, notes_list):
        self.notes = notes_list[:]
        self.delta = delta

    def __str__(self):
        return "{%s %s}"%(self.delta, str(self.notes))
    
    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.notes == other.notes and self.delta == other.delta

    notes = None
    delta = None

class PreTrack:
    """ PreChords one by one """
    def __init__(self, chords=[], instrument=''):
        self.chords = chords[:]
        self.instrument_name = instrument
    
    def __str__(self):
        return "'%s' '%s' %s"%(self.track_name, self.instrument_name, self.program)
    
    def __repr__(self):
        return self.__str__()
    
    track_name = None
    instrument_name = None
    program = None

class PreSong:
    def __init__(self, tracks=[], bpm=0, name=""):
        self.tracks = tracks[:]
        self.name = name
        self.bpm = bpm
        self.time_signature = None

    def add_track(self, track):
        self.tracks.append(track)

    def dump(self, f):
        pickle.dump(self, f)
        
    def save(self, path):
        with open(path, 'wb') as f:        
            self.dump(f)

    def undump(self, f):
        self.__dict__.update(pickle.load(f).__dict__)
        
    def load(self, path):
        with open(path, 'rb') as f:
            self.undump(f)
            
    def __str__(self):
        ret = "'%s' %s %s\n"%(self.name, len(self.tracks), self.bpm)
        for t in self.tracks:
            ret += str(t)+'\n'
        return ret
    
    def __repr__(self):
        return self.__str__()

    name = None
    bpm = None
    key = None
    tracks = []
