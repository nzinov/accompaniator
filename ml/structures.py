import pickle


class Note:
    """ Stores individual note
    Attributes:
        number: MIDI number of note
    """

    def __init__(self, number):
        self.number = number

    def freq(self):
        """ Returns frequency in Hz """
        return 2 ** ((self.number - 69) / 12.) * 440

    def __str__(self):
        return "%s" % (self.number)

    def __repr__(self):
        return self.__str__()

    number = None


class Chord:
    """Stores a chord and its length in 1/128 beats"""

    def __init__(self, notes_list, duration, velocity):
        self.notes = notes_list[:]
        self.velocity = velocity
        self.duration = duration

    def len(self):
        return self.duration

    def len_in_ms(self, bpm):
        """ Returns length of chord in ms given beats per minute"""
        return self.duration * bpm / (128 * 60 * 1000)

    def __str__(self):
        return "{%s %s %s}" % (self.duration, self.velocity, str(self.notes))

    def __eq__(self, other):
        return self.duration == other.duration and self.velocity == other.velocity and self.notes == other.notes

    def add_notes(self, notes_list):
        self.notes.extend(notes_list)

    duration = None
    notes = None
    velocity = None


class Track:
    """ Chords one by one """

    def __init__(self, chords=[], instrument=''):
        self.chords = chords[:]
        self.instrument_name = instrument

    def __str__(self):
        return "'%s' '%s' %s" % (self.track_name, self.instrument_name, self.program)

    def __repr__(self):
        return self.__str__()

    def merge_track(self, track2):
        for i in range(len(self.chords)):
            self.chords[i].add_notes(track2.chords[i].notes)
        self.instrument_name += " and " + track2.instrument_name

    track_name = None
    instrument_name = None
    program = None


class Song:
    def __init__(self, tracks=[], bpm=0, name=""):
        self.tracks = tracks[:]
        self.name = name
        self.bpm = bpm

    def add_track(self, track):
        self.tracks.append(track)

    def del_track_num(self, track_number):
        self.tracks.pop(track_number)

    def del_track(self, track):
        self.tracks.remove(track)

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
        ret = "'%s' %s %s\n" % (self.name, len(self.tracks), self.bpm)
        for t in self.tracks:
            ret += str(t) + '\n'
        return ret

    def __repr__(self):
        return self.__str__()

    name = None
    bpm = None
    key = None
    tracks = []
