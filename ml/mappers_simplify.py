from copy import deepcopy, copy

from structures import *
import numpy as np
import math

from base_mapper import BaseMapper, MapperError


class MelodyDetectionMapper(BaseMapper):
    """ Detects a melody according to strategy """

    def __init__(self, strategy='most probable', fun=np.min, **kwargs):
        super().__init__(**kwargs)
        self.stats['melody tracks count'] = dict()
        self.fun = fun
        self.strategy = strategy

    def process(self, song):
        probably_melody = [i for i, track in enumerate(song.tracks) if track.has_one_note_at_time()]
        if not probably_melody:
            self.increment_stat(0, self.stats['melody tracks count'])
            raise MapperError('no melody tracks')

        if len(probably_melody) == 1:
            song.tracks[0], song.tracks[probably_melody[0]] = song.tracks[probably_melody[0]], song.tracks[0]
            self.increment_stat(1, self.stats['melody tracks count'])
            return song

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
            song.tracks[0], song.tracks[melody_index] = song.tracks[melody_index], song.tracks[0]
            return song
        elif self.strategy == 'split':
            songs = []
            for melody_index in probably_melody:
                song_res = deepcopy(song)
                song_res.tracks[0], song_res.tracks[melody_index] = song_res.tracks[melody_index], song_res.tracks[0]
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

        gcds = []
        for track in tracks[1:]:
            track_durations = np.array(list(map(lambda chord: chord.duration, track.chords)))

            assert track_durations.size != 0

            track_gcd = self.gcd(track_durations)
            self.increment_stat(track_gcd, self.stats['gcd'])
            gcds.append(track_gcd)

        gcd = self.gcd(gcds)
        for track in tracks:
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

    def get_split_times(self, chords, index):
        time1 = 0
        for i in range(0, index):
            time1 += chords[i].duration
        return time1, time1 + chords[index].duration

    def cut_fragment_by_time_(self, track, time1, time2):
        i2, chord_beginning_2 = track.get_index_of_time(time2)

        # TODO: добавить тест-кейсы со входом в эти два if
        if i2 < len(track.chords):
            duration_after = track.chords[i2].duration - (time2 - chord_beginning_2)

            if duration_after != 0:
                track.chords[i2].duration = duration_after

        i1, chord_beginning_1 = track.get_index_of_time(time1)
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
        self.min_big_chord_duration = min_big_chord_duration
        self.strategy = strategy
        self.min_duration = min_track_duration

    def clear_songs(self, songs):
        new_songs = []
        for song in songs:
            new_tracks = []
            for track in song.tracks:
                if track.nonpause_duration() == 0 or track.duration() < self.min_duration:
                    self.increment_stat('too short cut')
                    continue
                else:
                    new_tracks.append(track)
            song.tracks = new_tracks

            if len(song.tracks) <= 1:
                self.increment_stat('not enough tracks')
            else:
                new_songs.append(song)

        return new_songs

    def get_times(self, song):
        for track in song.tracks:
            for i, chord in enumerate(track.chords):
                if chord.duration > self.min_big_chord_duration:
                    return self.get_split_times(track.chords, i)
        return None

    def process_split(self, song):
        songs = []
        changing = True
        while changing:
            times = self.get_times(song)

            changing = False if times is None else True

            if changing:

                song1, song2 = deepcopy(song), deepcopy(song)
                track_pairs = list(map(lambda track:
                                       self.cut_fragment_by_time_split(track, times[0], times[1]),
                                       song.tracks))
                song1.tracks = [pair[0] for pair in track_pairs]
                song2.tracks = [pair[1] for pair in track_pairs]
                self.increment_stat('total pauses cut')
                songs += self.clear_songs([song1])
                song = song2
            else:
                songs += self.clear_songs([song])
                break

        return self.clear_songs(songs)

    def process_cat(self, song):
        changing = True
        while changing:
            times = self.get_times(song)

            changing = False if times is None else True

            if changing:
                new_tracks = []
                for track in song.tracks:
                    new_track = self.cut_fragment_by_time_cat(track, times[0], times[1])
                    if new_track.duration() != 0:
                        new_tracks.append(new_track)
                song.tracks = new_tracks
                self.increment_stat('total pauses cut')
            else:
                break

        return self.clear_songs([song])

    def process_drop(self, song):
        new_tracks = []
        for track in song.tracks:
            has_big_chords = False
            for i, chord in enumerate(track.chords):
                if chord.duration > self.min_big_chord_duration:
                    has_big_chords = True
                    self.increment_stat('has big chords')
                    break

            if not has_big_chords:
                self.increment_stat('no big chords')
                new_tracks.append(track)

        song.tracks = new_tracks

        return self.clear_songs([song])

    def remove_tracks_with_lot_of_pauses(self, song):
        """ If track contains too many pauses, it is better to remove track rather than cutting all song. """
        new_tracks = []
        for track in song.tracks:
            assert track.duration() != 0
            long_chords_duration = sum(chord.duration for chord in track.chords
                                       if chord.duration > self.min_big_chord_duration)
            if long_chords_duration/track.duration() > self.good_track_ratio:
                self.increment_stat('track with many pauses')
            else:
                self.increment_stat('normal pauses track')
                new_tracks.append(track)
        if len(new_tracks) < 2:
            self.increment_stat('not enough tracks')
            raise MapperError('not enough tracks')
        song.tracks = new_tracks
        return song

    def pad_tracks_to_same_duration(self, song):
        track_durations = [track.duration() for track in song.tracks]
        max_track_duration = max(track_durations)
        for i in range(0, len(track_durations)):
            if track_durations[i] < max_track_duration:
                song.tracks[i].chords.append(Chord([], max_track_duration - track_durations[i], -1))
        assert len(set(track.duration() for track in song.tracks)) == 1
        return song

    # Неоптимально, но больших пауз мало, и так сойдёт.
    def process(self, song):
        self.pad_tracks_to_same_duration(song)
        self.remove_tracks_with_lot_of_pauses(song)

        if self.strategy == 'drop':
            return self.process_drop(song)
        elif self.strategy == 'cat':
            return self.process_cat(song)
        elif self.strategy == 'split':
            return self.process_split(song)


class MergeTracksMapper(BaseMapper):
    """Соединяет аккорды однотипных дорожек, удаляет лишние дорожки
    Warning: call after CutOutLongChordsMapper and SplitNonMelodiesToGcdMapper. """

    @staticmethod
    def extract_melody(tracks):
        melody = tracks[0]
        not_melody = tracks[1:]
        return melody, not_melody

    def get_mergeable_track_indices(self, song):
        # возвращает массив из дорожек, которые можно смерджить
        melody, tracks = self.extract_melody(song.tracks)
        durations = np.array([])
        for track in tracks:
            chords = np.array(track.chords)
            durations = np.append(durations, chords[0].duration)
        _, indices = np.unique(durations, return_inverse=True)
        return indices

    def make_indices_for_merge(self, tracks_indices):
        if len(tracks_indices) == 0:
            return list()
        merge_indices = [[] for _ in range(np.max(tracks_indices) + 1)]
        for adding_track_index, base_track_index in enumerate(tracks_indices):
            merge_indices[base_track_index].append(adding_track_index)
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


class GetResultMapper(BaseMapper):
    """ Filters only suitable songs. """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def process(self, song):
        melodies_count = song.melodies_track_count()
        chords_count = len(song.tracks) - melodies_count
        if melodies_count == 1 and chords_count == 1:
            return song
        else:
            raise MapperError('melodies and chords not (1,1)')


class GetSongStatisticsMapper(BaseMapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stats['tracks count per song'] = dict()
        # self.stats['chord duration'] = dict()
        self.stats['most frequent chord duration'] = dict()
        self.stats['melody tracks count per song'] = dict()
        self.stats['chord tracks count per song'] = dict()
        self.stats['melody and chord'] = dict()
        self.stats['track nonpause duration'] = dict()
        self.stats['track pause duration'] = dict()
        self.stats['track duration'] = dict()
        self.stats['track pause to all ratio'] = dict()

    @staticmethod
    def majority(a):
        return int(np.argmax(np.bincount(a)))

    def process(self, song):
        self.increment_stat(len(song.tracks), self.stats['tracks count per song'])
        for track in song.tracks:
            self.increment_stat(GetSongStatisticsMapper.majority([int(chord.duration) for chord in track.chords]),
                                self.stats['most frequent chord duration'])
            # Too slow
            # for chord in track.chords:
            #     self.increment_stat(self.stats['chord duration'],
            #                         GetSongStatisticsMapper.majority([int(chord.duration) for chord in track.chords]))
            self.increment_stat(track.nonpause_duration(), self.stats['track nonpause duration'])
            self.increment_stat(track.pause_duration(), self.stats['track pause duration'])
            self.increment_stat(track.duration(), self.stats['track duration'])
            if track.duration() != 0:
                self.increment_stat(track.pause_duration()/track.duration(), self.stats['track pause to all ratio'])

        melodies_count = song.melodies_track_count()
        chords_count = len(song.tracks) - melodies_count

        self.increment_stat(melodies_count, self.stats['melody tracks count per song'])
        self.increment_stat(chords_count, self.stats['chord tracks count per song'])
        self.increment_stat(str((melodies_count, chords_count)), self.stats['melody and chord'])

        return song
