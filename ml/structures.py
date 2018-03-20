import pickle


class TimeSignature:
    def __init__(self, time, numerator, denominator, clocks_per_click, notated_32nd_notes_per_beat):
        """
        :param time: start of this time signature (in 128th notes)
        """
        self.time = time
        self.numerator = numerator
        self.denominator = denominator
        self.clocks_per_click = clocks_per_click
        self.notated_32nd_notes_per_beat = notated_32nd_notes_per_beat

    def __str__(self):
        return "%s (%s %s %s %s)"%(self.time,
                                   self.numerator, self.denominator,
                                   self.clocks_per_click, self.notated_32nd_notes_per_beat)

    def __repr__(self):
        return self.__str__()


class Note:
    """ Stores individual note
    Attributes:
        number: MIDI number of note
    """

    def __init__(self, number):
        self.number = number

    def freq(self):
        """ Returns frequency in Hz """
        return 2**((self.number - 69)/12.)*440

    def __str__(self):
        return "%s"%(self.number)

    def __repr__(self):
        return self.__str__()


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
        return self.duration*bpm/(128*60*1000)

    def __str__(self):
        return "{%s %s %s}"%(self.duration, self.velocity, str(self.notes))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.duration == other.duration and self.velocity == other.velocity and self.notes == other.notes

    def add_notes(self, notes_list):
        self.notes.extend(notes_list)


class Track:
    """ Chords one by one """

    def __init__(self, chords=[], track_name='', instrument_name='', program=-1):
        self.chords = chords[:]
        self.track_name = track_name
        self.instrument_name = instrument_name
        self.program = program

    def __str__(self):
        return "track '%s' '%s' %s with %d chords"%(
            self.track_name, self.instrument_name, self.program, len(self.chords))

    def __repr__(self):
        return self.__str__()

    def merge_track(self, track2):
        for i in range(len(self.chords)):
            self.chords[i].add_notes(track2.chords[i].notes)


class Song:
    def __init__(self, tracks=[], bpm=0, name=""):
        self.tracks = tracks[:]
        self.name = name
        self.bpm = bpm
        self.time_signature = None
        self.key_signature = None

    def add_track(self, track):
        self.tracks.append(track)

    def del_track_num(self, track):
        self.tracks.pop(track)

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
        ret = "'%s' %s %s\n"%(self.name, len(self.tracks), self.bpm)
        for t in self.tracks:
            ret += str(t) + '\n'
        return ret

    def __repr__(self):
        return self.__str__()
