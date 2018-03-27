from copy import deepcopy, copy

from structures import *
import numpy as np
import math

from base_mapper import BaseMapper, MapperError


class MelodyDetectionMapper(BaseMapper):
    """ Detects a melody according to strategy and marks it with is_melody=True"""

    def __init__(self, strategy='most probable', fun=np.min, **kwargs):
        super().__init__(**kwargs)
        self.stats['melody tracks count'] = dict()
        self.fun = fun
        self.strategy = strategy

    def process(self, song):
        probably_melody = [i for i, track in enumerate(song.tracks) if track.has_one_note_at_time()]
        if not probably_melody:
            # self.increment_counter(song, 0)
            self.increment_stat(0, self.stats['melody tracks count'])
            raise MapperError('no melody tracks')

        for track in song.tracks:
            track.is_melody = False

        if len(probably_melody) == 1:
            song.tracks[0].is_melody = True
            # self.increment_counter(song, 1)
            self.increment_stat(1, self.stats['melody tracks count'])
            return song

        # self.increment_counter(song, len(probably_melody))
        self.increment_stat(len(probably_melody), self.stats['melody tracks count'])

        if self.strategy == 'most probable':
            vals = []
            for i in probably_melody:
                heights = []
                for chord in song.tracks[i].chords:
                    if chord.notes:
                        heights += list(map(lambda note: note.number, chord.notes))
                vals.append(self.fun(heights))
            melody_index = np.argmax(vals)
            song.tracks[melody_index].is_melody = True
            return song
        elif self.strategy == 'split':
            songs = []
            for i in probably_melody:
                song_res = copy(song)
                song_res.tracks[i].is_melody = True
                songs.append(song_res)
            return songs
        else:
            assert False


# Useless
class NonUniformChordsTracksRemoveMapper(BaseMapper):
    """ Removes tracks with non-uniform chords (where notes have different durations). """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
                self.increment_stat('non-uniform track')
                song.del_track(track)
            else:
                self.increment_stat('uniform track')
                durations = np.append(durations, unique_durations[0])

        if len(song.tracks) <= 1:
            self.increment_stat('not enough tracks')
            raise MapperError("Not enough tracks")
        return song


class SplitNonMelodiesToGcdMapper(BaseMapper):
    """Gets the GCD of chords duration and splits all chords longer to pieces."""

    @staticmethod
    def gcd(arr, use_unique=True):
        if use_unique:
            arr = np.unique(arr)
        gcd = arr[0]
        for a in arr[1:]:
            gcd = math.gcd(gcd, a)
        return gcd

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stats['gcd'] = dict()

    def process(self, song):
        tracks = np.array(song.tracks)

        for track in tracks:
            if track.is_melody:
                continue

            track_durations = np.array(list(map(lambda chord: chord.duration, track.chords)))

            assert track_durations.size != 0

            gcd = self.gcd(track_durations)
            self.increment_stat(gcd, self.stats['gcd'])

            new_chords = []
            for chord in track.chords:
                chord_duration = chord.duration
                chord.duration = gcd
                for i in range(0, int(chord_duration/gcd)):
                    new_chords.append(deepcopy(chord))
            track.chords = new_chords
        assert song.tracks
        return song


# Возможно, будут проблемы, если две больших паузы будут накладываться
class CutOutLongChordsMapper(BaseMapper):
    """Detects long chords and removes it according to strategy. """

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
    # Пользуемся тем, что удаляем самую большую паузу (но не самый большой аккорд!!!!11),
    # т. е. начало и конец попадают в разные аккорды.
    def cut_fragment_by_time_(self, track, time1, time2):
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

        return track.chords[:i1], track.chords[i2:]

    def cut_fragment_by_time_cat(self, track, time1, time2):
        t1, t2 = self.cut_fragment_by_time_(track, time1, time2)
        track.chords = t1 + t2
        return track

    def cut_fragment_by_time_split(self, track, time1, time2):
        t1, t2 = self.cut_fragment_by_time_(track, time1, time2)
        track1, track2 = deepcopy(track), deepcopy(track)
        track1.chords = t1
        track2.chords = t2
        # if you return tuple instead of list, song1 gets only one track at testMultipleTracksCutting
        return [track1, track2]

    def __init__(self, strategy='split', good_track_ratio=0.2, min_big_chord_duration=128, min_track_duration=10*128/4,
                 **kwargs):
        """
        :param strategy: 'split' or 'cat'
        :param good_track_ratio: ratio of long chords duration to track duration in tracks we consider
        :param min_big_chord_duration: chords from this duration are considered long
        :param min_track_duration: tracks smaller than that are not considered after split
        """
        super().__init__(**kwargs)
        self.good_track_ratio = good_track_ratio
        self.min_big_pause_duration = min_big_chord_duration
        self.strategy = strategy
        self.min_duration = min_track_duration

    def clear_songs(self, songs):
        new_songs = []
        for song in songs:
            new_tracks = []
            for track in song.tracks:
                if track.nonpause_duration() != 0 and track.duration() >= self.min_duration:
                    new_tracks.append(track)
            song.tracks = new_tracks

            if len(song.tracks) <= 1:
                self.increment_stat('not enough tracks')
            else:
                new_songs.append(song)
        return new_songs

    def process_split(self, song):
        changing = True
        while changing:
            changing = False
            duration_biggest, times_biggest = 0, None
            for track_num, track in enumerate(song.tracks):
                for i, chord in enumerate(track.chords):
                    if chord.duration > self.min_big_pause_duration \
                            and chord.duration > duration_biggest:
                        time1, time2 = self.get_split_times(track.chords, i)
                        changing = True
                        duration_biggest = chord.duration
                        times_biggest = (time1, time2)
            if not changing:
                break
            song1, song2 = copy(song), copy(song)
            track_pairs = list(map(lambda track:
                                   self.cut_fragment_by_time_split(track, times_biggest[0], times_biggest[1]),
                                   song.tracks))
            # These lines somehow fixed the bug with tuple described above
            #  for pair in track_pairs:
            #     pass
            song1.tracks = [pair[0] for pair in track_pairs]
            song2.tracks = [pair[1] for pair in track_pairs]
            self.increment_stat('total pauses cut')

            return sum([self.process(song) for song in self.clear_songs([song1]) + self.clear_songs([song2])], [])

        return self.clear_songs([song])

    def process_cat(self, song):
        changing = True
        while changing:
            changing = False
            duration_biggest, times_biggest = 0, None
            for track_num, track in enumerate(song.tracks):
                for i, chord in enumerate(track.chords):
                    if chord.duration > self.min_big_pause_duration \
                            and chord.duration > duration_biggest:
                        time1, time2 = self.get_split_times(track.chords, i)
                        changing = True
                        duration_biggest = chord.duration
                        times_biggest = (time1, time2)
            if not changing:
                break

            new_tracks = []
            for track in song.tracks:
                new_track = self.cut_fragment_by_time_cat(track, times_biggest[0], times_biggest[1])
                if new_track.duration() != 0:
                    new_tracks.append(new_track)
            song.tracks = new_tracks
            self.increment_stat('total pauses cut')
        if len(song.tracks) == 0:
            raise MapperError('not enough tracks')
        assert len(set(track.duration() for track in song.tracks)) == 1

        return self.clear_songs([song])[0]

    # Неоптимально, но больших пауз мало, и так сойдёт.
    def process(self, song):
        # Если какой-то трек содержит очень много пауз, его лучше удалить.
        new_tracks = []
        for track in song.tracks:
            assert track.duration() != 0
            long_chords_duration = sum(chord.duration for chord in track.chords
                                       if chord.duration > self.min_big_pause_duration)
            if long_chords_duration/track.duration() > self.good_track_ratio:
                self.increment_stat('track with many pauses')
            else:
                self.increment_stat('normal pauses track')
                new_tracks.append(track)
        if len(new_tracks) < 2:
            self.increment_stat('not enough tracks')
            raise MapperError('not enough tracks')
        song.tracks = new_tracks

        # Дополняем треки паузами до одинаковой длины.
        track_durations = [track.duration() for track in song.tracks]
        max_track_duration = max(track_durations)
        for i in range(0, len(track_durations)):
            if track_durations[i] < max_track_duration:
                song.tracks[i].chords.append(Chord([], max_track_duration - track_durations[i], -1))
        assert len(set(track.duration() for track in song.tracks)) == 1

        if self.strategy == 'drop':
            assert False  # TODO
        elif self.strategy == 'cat':
            return self.process_cat(song)
        elif self.strategy == 'split':
            return self.process_split(song)


class MergeTracksMapper(BaseMapper):
    """Соединяет аккорды однотипных дорожек, удаляет лишние дорожки
    Warning: call after CutOutLongChordsMapper and SplitNonMelodiesToGcdMapper. """

    @staticmethod
    def extract_melody(tracks):
        melodies = [track for track in tracks if track.is_melody]
        melody = melodies[0] if melodies else None
        not_melody = [track for track in tracks if not track.is_melody]
        return melody, not_melody

    def get_mergeable_track_indices(self, song):
        # возвращает массив из дорожек, которые можно смерджить
        melody, tracks = self.extract_melody(song.tracks)
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def process(self, song):
        indices = self.get_mergeable_track_indices(song)
        melody, tracks = self.extract_melody(song.tracks)
        similar_tracks_indices = self.make_indices_for_merge(indices)
        assert (len(tracks) - len(similar_tracks_indices) >= 0)
        self.increment_stat('tracks merged', count=len(tracks) - len(similar_tracks_indices))
        new_tracks = []
        for indices in similar_tracks_indices:
            if len(indices) > 1:
                for i in range(1, len(indices)):
                    tracks[indices[0]].merge_track(tracks[indices[i]])
            new_tracks.append(tracks[indices[0]])
        song.tracks = new_tracks + [melody] if melody else new_tracks
        return song
