from prestructures import *
from structures import *
from fetch import *
from simplifier import *
from base_mapper import *

import numpy as np


class BadSongsRemoveMapper(BaseMapper):
    """Removes songs with <=1 track"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_counters(['<=1 track', '>1 track'])

    def process(self, song):
        if len(song.tracks) <= 1:
            self.increment_counter(song, '<=1 track')
            raise MapperError("1 track")
        else:
            self.increment_counter(song, '>1 track')
        return song


# Useless
class SongsWithIntegerDurationsMapper(BaseMapper):
    """Was designed to count songs with integer durations of notes. Almost no such songs were found."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_counters(['not with integer durations', 'with integer durations'])

    @staticmethod
    def myround(x, base=4):
        return int(base*round(float(x)/base))

    def process(self, song, precision=1):
        is_with_integer_durations = True
        for track in song.tracks:
            # Round notes durations.
            for chord in track.chords:
                if not np.isclose(self.myround(chord.delta, precision), chord.delta):
                    # print((self.myround(chord.delta, precision), chord.delta))
                    is_with_integer_durations = False
                    break
                else:
                    chord.delta = self.myround(chord.delta, precision)
                for note in chord.notes:
                    if not np.isclose(self.myround(note.duration, precision), note.duration):
                        # print((self.myround(note.duration, precision), note.duration))
                        is_with_integer_durations = False
                        break
                    else:
                        # print("SUCCESS", (self.myround(note.duration, precision), note.duration))
                        note.duration = self.myround(note.duration, precision)
                if not is_with_integer_durations:
                    break

            if not is_with_integer_durations:
                break

        if not is_with_integer_durations:
            self.increment_counter(song, 'not with integer durations')
            raise MapperError("Not integer duration")
        else:
            self.increment_counter(song, 'with integer durations')
            return song


class NoiseReductionMapper(BaseMapper):
    """Rounds durations of notes to 1/32 by default.
    This method is quite rough, and some small notes could be appended to wrong chords
    (zero duration notes appear as well)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_counters([])

    # rounding to 4/128th note
    @staticmethod
    def myround(x, base=4):
        return int(base*round(float(x)/base))

    def process(self, song):
        for track in song.tracks:
            # Round notes durations.
            for chord in track.chords:
                chord.delta = self.myround(chord.delta, 4)
                new_notes = []
                for note in chord.notes:
                    note.duration = self.myround(note.duration, 4)
                    new_notes.append(note)

                chord.notes = new_notes

            # Concatenate chords.
            new_chords = [PreChord(0, [])]
            for chord in track.chords[1:]:
                if chord.delta != 0:
                    new_chords.append(chord)
                else:
                    new_chords[-1].notes += chord.notes

            # Remove dummy chord.
            if new_chords[0] == PreChord(0, []):
                new_chords.pop(0)
            track.chords = new_chords
        return song


class UnneededInstrumentsMapper(BaseMapper):
    """Removes strange instruments: sound_effects, drums, synth."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_counters(['sound_effects', 'drums', 'synth', 'normal', 'not enough tracks'])

    def process(self, song):
        new_tracks = []
        for track in song.tracks:
            if track.program >= 112:
                self.stats['sound_effects'] += 1
            elif 80 <= track.program <= 103:
                self.stats['synth'] += 1
            elif track.program == 9:
                self.stats['drums'] += 1
            else:
                self.stats['normal'] += 1
                new_tracks.append(track)
        if len(new_tracks) <= 1:
            self.stats['not enough tracks'] += 1
            raise MapperError("Not enough tracks")
        song.tracks = new_tracks
        return song


class PreToFinalConvertMapper(BaseMapper):
    """ Converts song to inner representation.
    In: PreChord and PreNote
    Out: Chord and Note

    Removes tracks with non-uniform chords and notes with zero duration.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_counters(['notes in chords have same duration',
                           'notes in chords have different duration',
                           'notes in chords have zero duration',
                           'not enough tracks'])

    @staticmethod
    def convert_chord(chord):
        velocity = np.mean(list(map(lambda n: n.velocity, chord.notes)))
        duration = chord.notes[0].duration
        notes = [Note(note.number) for note in chord.notes]
        new_chord = Chord(notes, duration, velocity)
        return new_chord

    @staticmethod
    def convert_chords(chords):
        new_chords = []

        # Pause in the start
        if chords[0].delta != 0:
            new_chords.append(Chord([], chords[0].delta, 0))

        for i in range(0, len(chords) - 1):
            new_chord = PreToFinalConvertMapper.convert_chord(chords[i])
            delta = chords[i + 1].delta
            pause = delta - new_chord.duration
            new_chords.append(new_chord)
            if pause > 0:
                new_chords.append(Chord([], pause, 0))

        # The last chord
        new_chords.append(PreToFinalConvertMapper.convert_chord(chords[-1]))

        return new_chords

    def process(self, song):
        new_tracks = list()
        for track in song.tracks:

            is_same_durations = True
            is_zero_durations = False
            for chord in track.chords:
                durations = list(map(lambda note: note.duration, chord.notes))
                if len(set(durations)) > 1:
                    is_same_durations = False
                    break
                if durations[0] == 0:
                    is_zero_durations = True
                    break

            if is_zero_durations:
                self.stats['notes in chords have zero duration'] += 1
            if not is_same_durations:
                self.stats['notes in chords have different duration'] += 1
            else:
                self.stats['notes in chords have same duration'] += 1
                track.chords = self.convert_chords(track.chords)
                new_tracks.append(track)

        if len(new_tracks) <= 1:
            self.stats['not enough tracks'] += 1
            raise MapperError("not enough tracks")

        song.tracks = new_tracks
        return song


class TimeSignatureMapper(BaseMapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_counters(['no signature', 'one signature', 'many signatures',
                           'different clocks_per_click', 'different notated_32nd_notes_per_beat',
                           'signature concatenated'])

    def process(self, song):
        # gather stat
        clocks_per_click = [sig.clocks_per_click for sig in song.time_signature]
        if len(set(clocks_per_click)) > 1:
            self.increment_counter(song, 'different clocks_per_click')
        notated_32nd_notes_per_beat = [sig.notated_32nd_notes_per_beat for sig in song.time_signature]
        if len(set(notated_32nd_notes_per_beat)) > 1:
            self.increment_counter(song, 'different notated_32nd_notes_per_beat')

        # merge same
        new_signatures = list()
        new_signatures.append(song.time_signature[0])
        for i in range(1, len(song.time_signature)):
            if song.time_signature[i].numerator == new_signatures[-1].numerator and \
                    song.time_signature[i].denominator == new_signatures[-1].denominator:
                new_signatures[-1].time += song.time_signature[i].time
            else:
                new_signatures.append(song.time_signature[i])
        if len(song.time_signature) != len(new_signatures):
            self.increment_counter(song, 'signature concatenated')
        song.time_signature = new_signatures

        if len(song.time_signature) == 0:
            self.increment_counter(song, 'no signature')
            raise MapperError('Bad signature')
        elif len(song.time_signature) == 1:
            song.time_signature = (song.time_signature[0].numerator, song.time_signature[0].denominator)
            self.increment_counter(song, 'one signature')
        else:
            # change_times = [sig.time for sig in song.time_signature]
            self.increment_counter(song, 'many signatures')
            raise MapperError('Bad signature')
        return song


class GetSongStatisticsMapper(BaseMapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stats['tracks count per song'] = dict()
        self.stats['chord duration'] = dict()
        self.stats['most frequent chord duration'] = dict()
        self.stats['melody tracks count per song'] = dict()
        self.stats['chord tracks count per song'] = dict()
        self.stats['melody and chord'] = dict()
        self.stats['track nonpause duration'] = dict()
        self.stats['track duration'] = dict()
        self.stats['track pause to all ratio'] = dict()

    @staticmethod
    def majority(a):
        return int(np.argmax(np.bincount(a)))

    def process(self, song):
        self.increment_stat(self.stats['tracks count per song'], len(song.tracks))
        melodies_count = 0
        for track in song.tracks:
            self.increment_stat(self.stats['most frequent chord duration'],
                                GetSongStatisticsMapper.majority([int(chord.duration) for chord in track.chords]))
            # Too slow
            # for chord in track.chords:
            #     self.increment_stat(self.stats['chord duration'],
            #                         GetSongStatisticsMapper.majority([int(chord.duration) for chord in track.chords]))
            if track.has_one_note_at_time():
                melodies_count += 1
            self.increment_stat(self.stats['track nonpause duration'], track.nonpause_duration())
            self.increment_stat(self.stats['track duration'], track.nonpause_duration())
            if track.duration() != 0:
                self.increment_stat(self.stats['track pause to all ratio'], track.pause_duration()/track.duration())
        chords_count = len(song.tracks) - melodies_count
        self.increment_stat(self.stats['melody tracks count per song'], melodies_count)
        self.increment_stat(self.stats['chord tracks count per song'], chords_count)
        self.increment_stat(self.stats['melody tracks count per song'], melodies_count)
        self.increment_stat(self.stats['melody and chord'], str((melodies_count, chords_count)))

        return song
