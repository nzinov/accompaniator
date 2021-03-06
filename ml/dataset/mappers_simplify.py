from copy import deepcopy

from ml.structures import *
import numpy as np
import math

from ml.dataset.base_mapper import BaseMapper, MapperError
from ml.dataset.corpus import in_ipynb

if in_ipynb():
    import matplotlib.pyplot as plt


class MelodyDetectionMapper(BaseMapper):
    """ Detects a melody according to strategy """

    def __init__(self, strategy='most probable', fun=np.min, min_unique_notes=5, **kwargs):
        """
        :param strategy: 'most probable' to leave only the most probable melody or 'split' to leave all combinations.
        :param fun: function of note numbers. The biggest value indicates 'most probable' melody.
        :param min_unique_notes: minimum number of unique note heights to consider the track a valid melody.
        """
        super().__init__(**kwargs)
        self.stats['melody tracks count per song'] = dict()
        self.stats['chord tracks count per song'] = dict()
        self.stats['melody and chord'] = dict()
        self.stats['unique notes in melody track'] = dict()
        self.stats['likely melody tracks count'] = dict()
        self.fun = fun
        self.strategy = strategy
        self.min_unique_notes = min_unique_notes

    def is_likely_melody(self, track):
        if not track.has_one_note_at_time():
            return False

        notes = sum([[note.number for note in chord.notes] for chord in track.chords], [])
        unique = set(notes)
        self.increment_stat(len(unique), self.stats['unique notes in melody track'])
        if len(unique) < self.min_unique_notes:
            return False

        return True

    @staticmethod
    def extract_melody(tracks):
        melody = tracks[0]
        not_melody = tracks[1:]
        return melody, not_melody

    def process(self, song):
        melodies_count = song.melodies_track_count()
        chords_count = len(song.tracks) - melodies_count

        self.increment_stat(melodies_count, self.stats['melody tracks count per song'])
        self.increment_stat(chords_count, self.stats['chord tracks count per song'])
        self.increment_stat(str((melodies_count, chords_count)), self.stats['melody and chord'])

        likely_melody = [i for i, track in enumerate(song.tracks) if self.is_likely_melody(track)]
        self.increment_stat(len(likely_melody), self.stats['likely melody tracks count'])

        if not likely_melody:
            raise MapperError('no melody tracks')

        if len(likely_melody) == 1:
            song.tracks[0], song.tracks[likely_melody[0]] = song.tracks[likely_melody[0]], song.tracks[0]
            return song

        if self.strategy == 'most probable':
            values = []
            for i in likely_melody:
                heights = []
                for chord in song.tracks[i].chords:
                    if chord.notes:
                        heights += list(map(lambda note: note.number, chord.notes))
                values.append(self.fun(heights))
            melody_index = likely_melody[np.argmax(values)]
            assert song.tracks[melody_index].has_one_note_at_time()
            song.tracks[0], song.tracks[melody_index] = song.tracks[melody_index], song.tracks[0]
            assert song.melody_track.has_one_note_at_time()
            return song
        elif self.strategy == 'split':
            songs = []
            for melody_index in likely_melody:
                song_res = deepcopy(song)
                song_res.tracks[0], song_res.tracks[melody_index] = song_res.tracks[melody_index], song_res.tracks[0]
                assert song_res.melody_track.has_one_note_at_time()
                songs.append(song_res)
            return songs
        else:
            assert False


class SplitNonMelodiesToGcdMapper(BaseMapper):
    """Gets the GCD of chords duration and splits all chords longer to pieces."""

    @staticmethod
    def pad_tracks_to_same_duration(song):
        track_durations = [track.duration() for track in song.tracks]
        max_track_duration = max(track_durations)
        for i in range(0, len(track_durations)):
            if track_durations[i] < max_track_duration:
                song.tracks[i].chords.append(Chord([], max_track_duration - track_durations[i], -1))
        assert len(set(track.duration() for track in song.tracks)) == 1
        return song

    @staticmethod
    def gcd(arr, use_unique=True):
        if use_unique:
            arr = np.unique(arr)
        gcd = arr[0]
        for a in arr[1:]:
            gcd = math.gcd(gcd, a)
        return int(gcd)

    def __init__(self, min_gcd=16, **kwargs):
        """
        :param min_gcd (in 1/128th): Minimal duration that can be considered as GCD.
        """
        super().__init__(**kwargs)
        self.stats['gcd'] = dict()
        self.min_gcd = min_gcd

    def process(self, song):
        SplitNonMelodiesToGcdMapper.pad_tracks_to_same_duration(song)

        melody, tracks = MelodyDetectionMapper.extract_melody(song.tracks)

        gcds = []
        new_tracks = []
        for track in tracks:
            track_durations = np.array(list(map(lambda chord: chord.duration, track.chords)))

            assert track_durations.size != 0

            track_gcd = self.gcd(track_durations)
            self.increment_stat(track_gcd, self.stats['gcd'])
            if track_gcd >= self.min_gcd:
                new_tracks.append(track)
                gcds.append(track_gcd)
        tracks = new_tracks

        if len(gcds) == 0:
            raise MapperError('not enough tracks')

        gcd = self.gcd(gcds)
        for track in tracks:
            new_chords = []
            for chord in track.chords:
                chord_duration = chord.duration
                chord.duration = gcd
                for i in range(0, int(chord_duration / gcd)):
                    new_chords.append(deepcopy(chord))
            track.chords = new_chords

        assert tracks

        song.tracks = [melody] + tracks

        assert song.melody_track.has_one_note_at_time()

        return song


class MergeTracksMapper(BaseMapper):
    """ Merges chord of similar tracks.
    Warning: call after MelodyDetectionMapper and SplitNonMelodiesToGcdMapper. """

    def get_mergeable_track_indices(self, tracks):
        # возвращает массив из дорожек, которые можно смерджить
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
        self.stats['merging groups per song'] = dict()
        self.stats['merging group size'] = dict()

    def process(self, song):
        melody, tracks = MelodyDetectionMapper.extract_melody(song.tracks)
        indices = self.get_mergeable_track_indices(tracks)
        similar_tracks_indices = self.make_indices_for_merge(indices)
        assert (len(tracks) - len(similar_tracks_indices) >= 0)
        self.increment_stat('tracks merged', count=len(tracks) - len(similar_tracks_indices))
        new_tracks = []
        track_groups_per_song = 0
        for indices in similar_tracks_indices:
            self.increment_stat(len(indices), self.stats['merging group size'])
            if len(indices) > 1:
                track_groups_per_song += 1
                for i in range(1, len(indices)):
                    tracks[indices[0]].merge_track(tracks[indices[i]])
            new_tracks.append(tracks[indices[0]])
        song.tracks = ([melody] if melody else new_tracks) + new_tracks
        self.increment_stat(track_groups_per_song, self.stats['merging groups per song'])

        assert song.melody_track.has_one_note_at_time()

        return song


class GetSongStatisticsMapper(BaseMapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.stats['chord duration'] = dict()
        self.stats['most frequent chord duration'] = dict()
        self.stats['track nonpause duration'] = dict()
        self.stats['track pause duration'] = dict()
        self.stats['track duration'] = dict()
        self.stats['track pause to all ratio'] = dict()

    @staticmethod
    def majority(a):
        return int(np.argmax(np.bincount(a)))

    def process(self, song):
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
                self.increment_stat(track.pause_duration() / track.duration(), self.stats['track pause to all ratio'])

        assert song.melody_track.has_one_note_at_time()

        return song

    def make_histogram(self, name, plot=True):
        d = self.stats[name]
        heights, bins = np.histogram(list(d.keys()), weights=list(d.values()))
        if plot:
            plt.plot(bins[:-1], heights)
        return bins, heights
        # return dict([(k, v) for k, v in zip(bins, heights)])


class AdequateCutOutLongChordsMapper(BaseMapper):
    """Detects long chords and removes it splitting the song. """

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

    def cut_fragment_by_time_split(self, track, time1, time2):
        t1, t2 = self.cut_fragment_by_time_(track, time1, time2)
        chords = track.chords
        track.chords = None
        track1, track2 = deepcopy(track), deepcopy(track)
        track.chords = chords
        track1.chords = t1
        track2.chords = t2
        return [track1, track2]

    def __init__(self, min_big_chord_duration=128,
                 min_track_duration=10 * 128 / 4, **kwargs):
        """
        :param min_big_chord_duration (in 1/128th): chords from this duration are considered long
        :param min_track_duration (in 1/128th): tracks smaller than that are not considered after split
        """
        super().__init__(**kwargs)
        self.min_big_chord_duration = min_big_chord_duration
        self.min_duration = min_track_duration
        self.stats['melody pause duration'] = dict()
        self.stats['chord pause duration'] = dict()

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
                assert song.melody_track.has_one_note_at_time()
                new_songs.append(song)

        return new_songs

    def get_times_melody(self, track):
        time = 0
        for i, chord in enumerate(track.chords):
            if chord.duration > self.min_big_chord_duration:
                self.increment_stat(chord.duration, self.stats['melody pause duration'])
                return time, time + chord.duration
            time += chord.duration
        return None

    def get_times_chords(self, track):
        time = 0
        cur_chord_duration = 0
        time_beginning = 0
        for i, chord in enumerate(track.chords):
            cur_chord_duration += track.chords[i].duration
            time += track.chords[i].duration
            if i == len(track.chords) - 1 or track.chords[i] != track.chords[i + 1]:
                if cur_chord_duration >= self.min_big_chord_duration:
                    self.increment_stat(cur_chord_duration, self.stats['chord pause duration'])
                    return time_beginning, time_beginning + cur_chord_duration
                cur_chord_duration = 0
                time_beginning = time
        return None

    def process_split(self, song, track_num):
        songs = []
        changing = True
        while changing:
            if track_num == 0:
                times = self.get_times_melody(song.tracks[track_num])
            else:
                times = self.get_times_chords(song.tracks[track_num])

            changing = False if times is None else True
            if changing:
                tracks = song.tracks
                song.tracks = None
                song1, song2 = deepcopy(song), deepcopy(song)
                track_pairs = list(map(lambda track:
                                       self.cut_fragment_by_time_split(track, times[0], times[1]),
                                       tracks))
                song1.tracks = [pair[0] for pair in track_pairs]
                song2.tracks = [pair[1] for pair in track_pairs]
                self.increment_stat('total pauses cut')
                songs += self.clear_songs([song1])
                song = song2
            else:
                songs += self.clear_songs([song])
                break

        return self.clear_songs(songs)

    def process(self, song):
        songs = self.process_split(song, 0)
        res = sum([self.process_split(song, 1) for song in songs], [])
        return res
