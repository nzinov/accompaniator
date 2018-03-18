from prestructures import *
from structures import *
from fetch import *
from base_mapper import *

import numpy as np


class BadSongsRemoveMapper(BaseMapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_stats (['<=1 track', '>1 track'])

    def process(self, song):
        if len(song.tracks) <= 1:
            self.stats['<=1 track'] += 1
            self.add_example('<=1 track', song.name)
            raise MapperError("1 track")
        else:
            self.stats['>1 track'] += 1
            self.add_example('>1 track', song.name)
        return song


class SongsWithIntegerDurationsMapper(BaseMapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stats = {'not with integer durations': 0, 'with integer durations': 0}

    @staticmethod
    def myround(x, base=4):
        return int(base*round(float(x)/base))

    def process(self, song, precision=1):
        is_with_integer_durations = True
        for track in song.tracks:
            # Round notes durations.
            for chord in track.chords:
                if not np.isclose(self.myround(chord.delta, precision), chord.delta):
                    #print((self.myround(chord.delta, precision), chord.delta))
                    is_with_integer_durations = False
                    break
                else:
                    chord.delta = self.myround(chord.delta, precision)
                for note in chord.notes:
                    if not np.isclose(self.myround(note.duration, precision), note.duration):
                        #print((self.myround(note.duration, precision), note.duration))
                        is_with_integer_durations = False
                        break
                    else:
                        #print("SUCCESS", (self.myround(note.duration, precision), note.duration))
                        note.duration = self.myround(note.duration, precision)
                if not is_with_integer_durations:
                    break

            if not is_with_integer_durations:
                break

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
        if not is_with_integer_durations:
            self.stats['not with integer durations'] += 1
            raise MapperError("Not integer duration")
        else:
            self.stats['with integer durations'] += 1
            return song


# This method is quite rough, and some small notes could be appended to wrong chords.
class NoiseReductionMapper(BaseMapper):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # rounding to 4/128th note
    @staticmethod
    def myround(x, base=4):
        return int(base*round(float(x)/base))

    def process(self, song):
        for track in song.tracks:
            # Round notes durations.
            for chord in track.chords:
                chord.delta = self.myround(chord.delta, 4)
                for note in chord.notes:
                    note.duration = self.myround(note.duration, 4)

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


class UnneededInstrumentsHandler(BaseMapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stats = {'sound_effects': 0, 'drums': 0, 'synth': 0, 'normal': 0}

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
            raise MapperError("Not enough tracks")
        song.tracks = new_tracks
        return song


class PreToFinalConvertMapper(BaseMapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_stats(['same duration', 'different duration'])

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
        new_tracks = []
        for track in song.tracks:
            is_same_durations = True
            for chord in track.chords:
                durations = list(map(lambda note: note.duration, chord.notes))
                if len(set(durations)) > 1:
                    is_same_durations = False
                    break
            if is_same_durations:
                self.stats['same duration'] += 1
                track.chords = self.convert_chords(track.chords)
                new_tracks.append(track)
            else:
                self.stats['different duration'] += 1
        if len(new_tracks) <= 1:
            raise MapperError("Not enough tracks")
        song.tracks = new_tracks
        return song


class TimeSignatureMapper(BaseMapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stats = {'no signature': 0, 'one signature': 0, 'many signatures': 0,
                      'different clocks_per_click': 0, 'different notated_32nd_notes_per_beat': 0,
                      'signature concatenated':0}

    def process(self, song):
        # gather stat
        clocks_per_click = [sig.clocks_per_click for sig in song.time_signature]
        if len(set(clocks_per_click)) > 1:
            self.stats['different clocks_per_click'] += 1
        notated_32nd_notes_per_beat = [sig.notated_32nd_notes_per_beat for sig in song.time_signature]
        if len(set(notated_32nd_notes_per_beat)) > 1:
            self.stats['different notated_32nd_notes_per_beat'] += 1

        # merge same
        new_signatures = []
        new_signatures.append(song.time_signature[0])
        for i in range(1, len(song.time_signature)):
            if song.time_signature[i].numerator == new_signatures[-1].numerator and \
                    song.time_signature[i].denominator == new_signatures[-1].denominator:
                new_signatures[-1].time += song.time_signature[i].time
            else:
                new_signatures.append(song.time_signature[i])
        if len(song.time_signature) != len(new_signatures):
            self.stats['signature concatenated'] += 1
        song.time_signature = new_signatures

        if len(song.time_signature) == 0:
            self.stats['no signature'] += 1
            raise MapperError('Bad signature')
        elif len(song.time_signature) == 1:
            song.time_signature = (song.time_signature[0].numerator, song.time_signature[0].denominator)
            self.stats['one signature'] += 1
        else:
            # change_times = [sig.time for sig in song.time_signature]
            self.stats['many signatures'] += 1
            raise MapperError('Bad signature')
        return song