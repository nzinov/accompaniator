import pickle
import numpy as np
from functools import total_ordering
import music21


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
        return "%s (%s %s %s %s)" % (self.time,
                                     self.numerator, self.denominator,
                                     self.clocks_per_click, self.notated_32nd_notes_per_beat)

    def __repr__(self):
        return self.__str__()


@total_ordering
class Note:
    """ Stores individual note
    Attributes:
        number: MIDI number of note
    """

    letters_list = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def __init__(self, number):
        self.number = number

    def freq(self):
        """ Returns frequency in Hz """
        return 2**((self.number - 69) / 12.) * 440

    @staticmethod
    def freq_to_number(freq):
        return 12 * np.log2(freq / 440)

    def letter(self):
        return self.letters_list[(abs(self.number - 24)) % 12]

    def __str__(self):
        return "%s" % (self.number)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.number == other.number

    def __lt__(self, other):
        return self.number < other.number

    def __hash__(self):
        return self.number

    def get_music21_pitch(self):
        ret = music21.pitch.Pitch()
        ret.midi = self.number
        return ret


class Chord:
    """Stores a chord and its length in 1/128 beats"""

    def __init__(self, notes_list, duration, velocity, is_repeat=False):
        self.notes = notes_list[:]
        self.velocity = velocity
        self.duration = duration
        self.is_repeat = is_repeat

    def len(self):
        return self.duration

    def len_in_ms(self, bpm):
        """ Returns length of chord in ms given beats per minute. """
        return self.duration * bpm / (128 * 60 * 1000)

    def __str__(self):
        return "{%s %s %s}" % (self.duration, self.velocity, str(self.notes))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.duration == other.duration and self.velocity == other.velocity and self.notes == other.notes

    def __hash__(self):
        return hash(tuple(self.notes)) ^ hash(self.velocity) ^ hash(self.duration)

    def add_notes(self, notes_list):
        self.notes.extend(notes_list)

    def get_music21_repr(self):
        ret = music21.chord.Chord()
        ret.add([note.get_music21_pitch() for note in self.notes])
        ret.duration = music21.duration.Duration(self.duration * 4 / 128)
        ret.volume = music21.volume.Volume(velocity=self.velocity)
        return ret


class Track:
    """ Chords one by one """

    def __init__(self, chords=[], track_name='', instrument_name='', program=-1, key_signature=''):
        self.chords = chords[:]
        self.track_name = track_name
        self.instrument_name = instrument_name
        self.program = program
        self.key_signature = key_signature

    def str(self, with_chords=False, chords_in_row=5):
        ret = "Track '%s', instrument '%s' , program %s, with %d chords " % (
            self.track_name, self.instrument_name, self.program, len(self.chords))
        if with_chords:
            ret += '\n'
            for i in range((len(self.chords) - 1) // chords_in_row + 1):
                ret += ' '.join([str(chord) for chord in self.chords[i * chords_in_row:(i + 1) * chords_in_row]])
                ret += '\n'
        return ret

    def __str__(self):
        return self.str()

    def __repr__(self):
        return self.__str__()

    def merge_track(self, track2):
        for i in range(len(self.chords)):
            self.chords[i].add_notes(track2.chords[i].notes)

    def duration(self):
        duration = 0
        for chord in self.chords:
            duration += chord.duration
        return duration

    def nonpause_duration(self):
        duration = 0
        for chord in self.chords:
            if chord.notes:
                duration += chord.duration
        return duration

    def pause_duration(self):
        return self.duration() - self.nonpause_duration()

    def has_one_note_at_time(self):
        one_note_at_time = True
        for chord in self.chords:
            if len(chord.notes) > 1:
                one_note_at_time = False
                break
        return one_note_at_time

    def get_index_of_time(self, time):
        """ Returns the index of chord containing moment `time` and absolute time of its beginning. """
        cur_time = 0
        i = 0
        for chord in self.chords:
            if cur_time + chord.duration > time:
                return i, cur_time
            cur_time += chord.duration
            i += 1
        return i, cur_time

    def get_music21_repr(self):
        ret = music21.stream.Stream()
        try:
            chords_without_repeats = [self.chords[0]]
            for chord in self.chords[1:]:
                if hasattr(chord, 'is_repeat') and chord.is_repeat:
                    chords_without_repeats[-1].duration += chord.duration
                else:
                    chords_without_repeats.append(chord)
            ret.append([chord.get_music21_repr() for chord in chords_without_repeats])
        except IndexError:
            pass
        return ret


class Song:
    melody_index = 0
    rhythm_index = 1

    def __init__(self, tracks=[], bpm=0, name=""):
        self.tracks = tracks[:]
        self.name = name
        self.bpm = bpm
        self.time_signature = None
        self.key_signature = None

    def chord_tracks(self):
        return [track for track in self.tracks if track.has_one_note_at_time()]

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

    def str(self, with_chords=False):
        ret = "Song '%s', %s tracks, bpm %s\n" % (self.name, len(self.tracks), self.bpm)
        for t in self.tracks:
            ret += t.str(with_chords=with_chords) + '\n'
        return ret

    def __str__(self):
        return self.str()

    def __repr__(self):
        return self.__str__()

    def melodies_track_count(self):
        melodies_count = 0
        for track in self.tracks:
            if track.has_one_note_at_time():
                melodies_count += 1
        return melodies_count

    def chords_track_count(self):
        return len(self.tracks) - self.melodies_track_count()

    @property
    def melody_track(self):
        return self.tracks[0]

    @property
    def chord_track(self):
        return self.tracks[1]

    def get_music21_repr(self):
        return music21.stream.Stream([track.get_music21_repr() for track in self.tracks])
