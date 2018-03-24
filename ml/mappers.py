from prestructures import *
from structures import *
from fetch import *
from base_mapper import *

import numpy as np
from copy import deepcopy

class BadSongsRemoveMapper(BaseMapper):
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
            self.increment_counter(song, 'not with integer durations')
            raise MapperError("Not integer duration")
        else:
            self.increment_counter(song, 'with integer durations')
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


class UnneededInstrumentsMapper(BaseMapper):
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_counters(['tracks same duration', 'tracks different duration', 'not enough tracks'])

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
            for chord in track.chords:
                durations = list(map(lambda note: note.duration, chord.notes))
                if len(set(durations)) > 1:
                    is_same_durations = False
                    break
            if is_same_durations:
                self.stats['tracks same duration'] += 1
                track.chords = self.convert_chords(track.chords)
                new_tracks.append(track)
            else:
                self.stats['tracks different duration'] += 1
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


# work in progress
class MelodyDetectionMapper(BaseMapper):

    @staticmethod
    def is_melody(track):
        is_one_note_at_time = True
        for chord in track.chords:
            if len(chord.notes) > 1:
                is_one_note_at_time = False
                break
        return is_one_note_at_time

    # Не очень понятно, зачем это нужно.
    def is_voice(self, track):
        low = Note.freq_to_number(80)
        high = Note.freq_to_number(8000)
        is_human_frequency = True
        for chord in track.chords:
            for note in chord.notes:
                if not (low <= note.number <= high):
                    is_human_frequency = False
                    break
        return is_human_frequency

    # Во второй кусок попадают ноты, начало которых >= time
    def split_track_by_time(self, track, time):
        cur_time = 0
        i = 0
        for chord in track.chords:
            if cur_time >= time:
                break
            cur_time += chord.duration
            i += 1
        track1 = Track()
        track1.program, track1.instrument_name, track1.track_name \
            = track.program, track.instrument_name, track.track_name
        track1.chords = track.chords[:i]
        track.chords = track.chords[i:]
        return track1, track

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_counters([])

    def process(self, song):
        pass


class GetSongStatisticsMapper(BaseMapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stats['tracks count per song'] = dict()
        self.stats['chord duration'] = dict()
        self.stats['melody tracks count per song'] = dict()
        self.stats['chord tracks count per song'] = dict()
        self.stats['melody and chord'] = dict()

    @staticmethod
    def majority(a):
        return int(np.argmax(np.bincount(a)))

    def process(self, song):
        self.increment_stat(self.stats['tracks count per song'], len(song.tracks))
        melodies_count = 0
        for track in song.tracks:
            self.increment_stat(self.stats['chord duration'],
                                GetSongStatisticsMapper.majority([int(chord.duration) for chord in track.chords]))
            if MelodyDetectionMapper.is_melody(track):
                melodies_count += 1
        chords_count = len(song.tracks) - melodies_count
        self.increment_stat(self.stats['melody tracks count per song'], melodies_count)
        self.increment_stat(self.stats['chord tracks count per song'], chords_count)
        self.increment_stat(self.stats['melody tracks count per song'], melodies_count)
        self.increment_stat(self.stats['melody and chord'], str((melodies_count, chords_count)))

        return song


# Возможно, будут проблемы, если две больших паузы будут накладываться
class CutPausesMapper(BaseMapper):

    @staticmethod
    def get_index_of_time(track, time):
        """ Возвращает номер аккорда аккорда, в котором находится момент time, и абсолютное время его начала"""
        cur_time = 0
        i = 0
        for chord in track.chords:
            if cur_time + chord.duration > time:
                return i, cur_time
            cur_time += chord.duration
            i += 1
        return i, cur_time

    def get_split_times(self, chords, index):
        time1 = 0
        for i in range(0, index):
            time1 += chords[i].duration
        return time1, time1+chords[index].duration

    # Во второй кусок попадают ноты, начало которых >= time
    # Пользуемся тем, что удаляем самую большую паузу, т. е. начало и конец попадают в разные аккорды.
    def cut_fragment_by_time(self, track, time1, time2):
        i2, chord_beginning_2 = self.get_index_of_time(track, time2)

        if i2 <len(track.chords):
            duration_after = track.chords[i2].duration - (time2-chord_beginning_2)

            if duration_after != 0:
                track.chords[i2].duration = duration_after

        i1, chord_beginning_1 = self.get_index_of_time(track, time1)
        duration_before = time1 - chord_beginning_1
        if duration_before != 0:
            track.chords[i1].duration = duration_before
            i1 += 1

        track.chords = track.chords[:i1]+track.chords[i2:]
        return track

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_counters([])

    # Неоптимально, но больших пауз мало, и так сойдёт.
    def process(self, song):
        # Дополняем треки паузами до одинаковой длины.
        track_durations = [track.duration() for track in song.tracks]
        max_track_duration = max(track_durations)
        for i in range(0, len(track_durations)):
            if track_durations[i] < max_track_duration:
                song.tracks[i].chords.append(Chord([], max_track_duration-track_durations[i], -1))

        changing = True
        while changing:
            changing = False
            duration_biggest, times_biggest = 0, None
            for track_num, track in enumerate(song.tracks):
                for i, chord in enumerate(track.chords):
                    if not chord.notes and chord.duration > 128 and chord.duration > duration_biggest:
                        time1, time2 = self.get_split_times(track.chords, i)
                        changing = True
                        duration_biggest = chord.duration
                        times_biggest = (time1, time2)
            if not changing:
                break
            song.tracks = list(map(lambda track:
                                   self.cut_fragment_by_time(track, times_biggest[0], times_biggest[1]), song.tracks))

        return song
