from structures import *
import numpy as np

from base_mapper import BaseMapper, MapperError


class MelodyDetectionMapper(BaseMapper):

    # Во второй кусок попадают ноты, начало которых >= time
    # def split_track_by_time(self, track, time):
    #     cur_time = 0
    #     i = 0
    #     for chord in track.chords:
    #         if cur_time >= time:
    #             break
    #         cur_time += chord.duration
    #         i += 1
    #     track1 = Track()
    #     track1.program, track1.instrument_name, track1.track_name \
    #         = track.program, track.instrument_name, track.track_name
    #     track1.chords = track.chords[:i]
    #     track.chords = track.chords[i:]
    #     return track1, track

    def __init__(self, fun=np.min, **kwargs):
        super().__init__(**kwargs)
        self.add_counters(['no melody tracks', '1 melody track', 'many melody tracks'])
        self.fun = fun

    def process(self, song):
        probably_melody = [i for i, track in enumerate(song.tracks) if track.has_one_note_at_time()]
        if not probably_melody:
            self.increment_counter(song, 'no melody tracks')
            raise MapperError('no melody tracks')

        for track in song.tracks:
            track.is_melody = False

        if len(probably_melody) == 1:
            song.tracks[0].is_melody = True
            self.increment_counter(song, '1 melody track')
            return song

        vals = []
        for i in probably_melody:
            heights = []
            for chord in song.tracks[i].chords:
                heights += list(map(lambda note: note.number, chord.notes))
            vals.append(self.fun(heights))
        melody_index = np.argmax(vals)
        self.increment_counter(song, 'many melody tracks')
        song.tracks[melody_index].is_melody = True
        return song


class NonUniformChordsTracksRemoveMapper(BaseMapper):
    """Удаляет неравномерные треки и возвращает массив из дорожек, которые можно смерджить"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_counters(['non-uniform track', 'uniform track', 'not enough tracks'])

    def process(self, song):
        tracks = np.array(song.tracks)
        durations = np.array([])
        for track in tracks:
            if track.has_one_note_at_time():
                continue
            chords = np.array(track.chords)
            track_durations = np.array([])
            for chord in chords:
                track_durations = np.append(track_durations, chord.duration)
            unique_durations = np.unique(track_durations)

            # TODO: временное решение, отсекащее большие паузы.
            unique_durations = unique_durations[unique_durations <= 128]

            if len(unique_durations) != 1:
                self.stats['non-uniform track'] += 1
                song.del_track(track)
            else:
                self.stats['uniform track'] += 1
                durations = np.append(durations, unique_durations[0])

        if len(song.tracks) <= 1:
            self.stats['not enough tracks'] += 1
            raise MapperError("Not enough tracks")
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
        return time1, time1 + chords[index].duration

    # Во второй кусок попадают ноты, начало которых >= time
    # Пользуемся тем, что удаляем самую большую паузу, т. е. начало и конец попадают в разные аккорды.
    def cut_fragment_by_time(self, track, time1, time2):
        i2, chord_beginning_2 = self.get_index_of_time(track, time2)

        # TODO: добавить тест-кейсы со входом в эти два if
        if i2 < len(track.chords):
            duration_after = track.chords[i2].duration - (time2 - chord_beginning_2)

            if duration_after != 0:
                track.chords[i2].duration = duration_after

        i1, chord_beginning_1 = self.get_index_of_time(track, time1)
        if i1 < len(track.chords):
            duration_before = time1 - chord_beginning_1
            if duration_before != 0:
                track.chords[i1].duration = duration_before
                i1 += 1

        track.chords = track.chords[:i1] + track.chords[i2:]
        return track

    def __init__(self, good_track_ratio=0.2, **kwargs):
        super().__init__(**kwargs)
        self.add_counters(['total pauses cut', 'big pauses track', 'normal pauses track', 'not enough tracks'])
        self.good_track_ratio = good_track_ratio

    # Неоптимально, но больших пауз мало, и так сойдёт.
    def process(self, song):
        # Если какой-то трек содержит очень много пауз, его лучше удалить.
        new_tracks = []
        for track in song.tracks:
            if track.duration() != 0 and track.pause_duration()/track.duration() > self.good_track_ratio:
                self.stats['big pauses track'] += 1
            else:
                self.stats['normal pauses track'] += 1
                new_tracks.append(track)
        if len(new_tracks) < 2:
            self.stats['not enough tracks'] += 1
            raise MapperError('not enough tracks')
        song.tracks = new_tracks

        # Дополняем треки паузами до одинаковой длины.
        track_durations = [track.duration() for track in song.tracks]
        max_track_duration = max(track_durations)
        for i in range(0, len(track_durations)):
            if track_durations[i] < max_track_duration:
                song.tracks[i].chords.append(Chord([], max_track_duration - track_durations[i], -1))

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
            self.increment_stat(self.stats, 'total pauses cut')
        return song


# Work in progress
# Кажется, что все дорожки должны быть одинаковой длины.
class MergeTracksMapper(BaseMapper):
    """Соединяет аккорды однотипных дорожек, удаляет лишние дорожки"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_counters(['tracks merged'])

    @staticmethod
    def get_not_melody(tracks):
        return np.array([track for track in tracks if not track.is_melody])

    def process(self, song):
        indices = self.get_mergeable_track_indices(song)
        tracks = self.get_not_melody(song.tracks)
        uni_indices = self.make_indices_for_merge(indices)
        assert (len(tracks) - len(uni_indices) >= 0)
        self.stats['tracks merged'] += len(tracks) - len(uni_indices)
        for indices in uni_indices:
            if len(indices) > 1:
                for i in range(1, len(indices)):
                    tracks[indices[0]].merge_track(tracks[indices[i]])
                    song.del_track_num(indices[i])
        return song

    def get_mergeable_track_indices(self, song):
        # возвращает массив из дорожек, которые можно смерджить
        tracks = self.get_not_melody(song.tracks)
        durations = np.array([])
        for track in tracks:
            chords = np.array(track.chords)
            durations = np.append(durations, chords[0].duration)
        u, indices = np.unique(durations, return_inverse=True)
        return indices

    def make_indices_for_merge(self, tracks_indices):
        if len(tracks_indices) == 0:
            return list()
        merge_indices = [[] for i in range(np.max(tracks_indices) + 1)]
        for i, index in enumerate(tracks_indices):
            merge_indices[index].append(i)
        return merge_indices
