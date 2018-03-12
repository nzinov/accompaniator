from prestructures import *
from structures import *
from fetch import *
from base_mapper import *

import numpy as np


class BadSongsRemoveMapper(BaseMapper):
    def __init__(self):
        super().__init__(self)
        self.stats = {'1 track': 0, '>1 track': 0}

    def process(self, song):
        if len(song.tracks) <= 1:
            self.stats['1 track'] += 1
            raise MapperError("1 track")
        else:
            self.stats['>1 track'] += 1
        return song


# Convention: dummy chord should persist.
# This method is quite rough, and some small notes could be appended to wrong chords.
class NoiseReductionMapper(BaseMapper):

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

            # Persist dummy chord.
            if new_chords[0] != PreChord(0, []):
                new_chords.insert(0, PreChord(0, []))
            track.chords = new_chords
        return song


class UnneededInstrumentsHandler(BaseMapper):
    def __init__(self):
        super().__init__(self)
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
    def __init__(self):
        super().__init__(self)
        self.stats = {'same duration': 0, 'different duration': 0}

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
    def __init__(self):
        super().__init__(self)
        self.stats = {'no signature': 0, 'one signature': 0, 'many signatures': 0}

    def process(self, song):
        # merge same

        if len(song.time_signature) == 0:
            self.stats['no signature'] += 1
        elif len(song.time_signature) == 1:
            song.time_signature = (song.time_signature[0].numerator, song.time_signature[0].denominator)
            self.stats['one signature'] += 1
        else:
            new_signatures = []
            new_signatures.append(self.time_signature[0])
            for i in range(1, len(self.time_signature)):
                pass #TODO
            change_times = [sig.time for sig in song.time_signature]
            self.stats['many signatures'] += 1
