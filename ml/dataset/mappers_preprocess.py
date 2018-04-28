from ml.dataset.corpus import *
from ml.dataset.mappers_simplify import *
from ml.dataset.base_mapper import *

import numpy as np


class BadSongsRemoveMapper(BaseMapper):
    """Removes songs with <=1 track"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stats['tracks count per song'] = dict()

    def process(self, song):
        new_tracks = []
        for track in song.tracks:
            if len(track.chords) != 0:
                new_tracks.append(track)
            else:
                self.increment_stat('track without chords')
        song.tracks = new_tracks

        self.increment_stat(len(song.tracks), self.stats['tracks count per song'])
        if len(song.tracks) <= 1:
            self.example_and_increment(song, '<=1 track')
            raise MapperError("1 track")
        else:
            self.example_and_increment(song, '>1 track')

        return song


class NoiseReductionMapper(BaseMapper):
    """Rounds durations of notes to 1/32 by default.
    This method is quite rough, and some small notes could be appended to wrong chords
    (zero duration notes appear as well).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stats['divergence of duration from majority duration'] = dict()

    @staticmethod
    def round_to_base(x, base=4):
        return int(base*round(float(x)/base))

    @staticmethod
    def get_divergence(x, base=4):
        return abs(x-NoiseReductionMapper.round_to_base(x, base))

    def process(self, song):
        for track in song.tracks:
            # Round notes durations.
            for chord in track.chords:
                chord.delta = self.round_to_base(chord.delta, 4)
                new_notes = []
                for note in chord.notes:
                    divergence = NoiseReductionMapper.get_divergence(note.duration, 4)
                    self.increment_stat(divergence, self.stats['divergence of duration from majority duration'])
                    note.duration = self.round_to_base(note.duration, 4)
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

    def process(self, song):
        new_tracks = []
        for track in song.tracks:
            if track.program >= 112:
                self.increment_stat('sound_effects')
            elif 80 <= track.program <= 103:
                self.increment_stat('synth')
            elif track.program == 9:
                self.increment_stat('drums')
            else:
                self.increment_stat('normal')
                new_tracks.append(track)
        if len(new_tracks) <= 1:
            self.increment_stat('not enough tracks')
            raise MapperError('Not enough tracks')
        song.tracks = new_tracks
        return song


class PreToFinalConvertMapper(BaseMapper):
    """ Converts song to inner representation.
    In: PreChord and PreNote
    Out: Chord and Note

    Removes tracks with non-uniform chords and notes with zero duration.

    TODO: make it more clever. If most of notes are of the same duration, and some slightly diverge, round it.
    """

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def process(self, song):
        new_tracks = list()
        for track in song.tracks:

            if len(track.chords) == 0:
                continue

            has_same_durations = True
            has_zero_durations = False
            for chord in track.chords:
                durations = list(map(lambda note: note.duration, chord.notes))
                if len(set(durations)) > 1:
                    has_same_durations = False
                    break
                if durations[0] == 0:
                    has_zero_durations = True
                    break

            if has_zero_durations:
                self.increment_stat('notes in chords have zero duration')
            if not has_same_durations:
                self.increment_stat('notes in chords have different duration')
            else:
                self.increment_stat('notes in chords have same duration')
                track.chords = self.convert_chords(track.chords)
                if track.duration() == 0:
                    self.increment_stat('track has zero duration')
                else:
                    self.increment_stat('normal track')
                    new_tracks.append(track)

        if len(new_tracks) <= 1:
            self.increment_stat('not enough tracks')
            raise MapperError('not enough tracks')

        song.tracks = new_tracks
        return song


class TimeSignatureMapper(BaseMapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def process(self, song):
        # gather stat
        clocks_per_click = [sig.clocks_per_click for sig in song.time_signature]
        if len(set(clocks_per_click)) > 1:
            self.example_and_increment(song, 'different clocks_per_click')
        notated_32nd_notes_per_beat = [sig.notated_32nd_notes_per_beat for sig in song.time_signature]
        if len(set(notated_32nd_notes_per_beat)) > 1:
            self.example_and_increment(song, 'different notated_32nd_notes_per_beat')

        if len(song.time_signature) == 0:
            self.example_and_increment(song, 'no signature')
            raise MapperError('Bad signature')

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
            self.example_and_increment(song, 'signature concatenated')
        song.time_signature = new_signatures

        if len(song.time_signature) == 1:
            song.time_signature = (song.time_signature[0].numerator, song.time_signature[0].denominator)
            self.example_and_increment(song, 'one signature')
        else:
            # TODO: process more wise, maybe split song to parts
            # change_times = [sig.time for sig in song.time_signature]
            self.example_and_increment(song, 'many signatures')
            raise MapperError('Bad signature')
        return song
