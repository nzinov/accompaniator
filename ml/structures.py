import pickle

class Note:
    """ Stores individual note
    Attributes:
        freq: frequency, Hz
    """
    def __init__(self, fr):
        self.frequency = fr

    def freq(self):
        return self.frequency

    frequency = None

class Chord:
    """Stores a chord and its length in 1/128 beats"""

    def __init__(self, notes_list, length, beat_force):
        self.notes = notes_list[:]
        self.beat_force = beat_force
        self.length = length

    def len(self):
        return self.length

    def len_in_ms(self, bpm):
        """ Returns length of chord in ms given beats per minute"""
        return self.length * bpm / (128 * 60 * 1000)

    length = None   
    notes = None
    beat_force = None

class Track:
    """ Chords one by one """
    def __init__(self, chords, instrument):
        self.chords = chords[:]
        self.instrument_name = instrument

    instrument_name = None

class Song:
    def __init__(self, tracks=[], bpm=0, name=""):
        self.tracks = tracks[:]
        self.name = name
        self.bpm = bpm

    def add_track(self, track):
        self.tracks.append(track)

    def save(self, path):
        with open(path, 'wb') as f:        
            pickle.dump(self, f)

    def load(self, path):
        with open(path, 'rb') as f:
            self.__dict__.update(pickle.load(f).__dict__)

    name = None
    bpm = None
    key = None
    tracks = []

note1 = Note(440)
note2 = Note(330)
chord1 = Chord([note1, note2], 5, 0)
chord2  = Chord([], 3, 0)
track1 = Track([chord1, chord2], 'voice')
song = Song([track1], 5, "test song")
song.save("somewhere")
song1 = Song()
song1.load("somewhere")
print(song1.name)
