from structures import *
import numpy as np

from base_mapper import BaseMapper, MapperError


# удаляет неравномерные треки и возвращает массив из дорожек, которые можно смерджить
class NonUniformTracksRemoveMapper(BaseMapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_stats(['non-uniform track', 'uniform track', 'not enough tracks'])

    def process(self, song):
        tracks = np.array(song.tracks)
        durations = np.array([])
        for track in tracks:
            chords = np.array(track.chords)
            track_durations = np.array([])
            for chord in chords:
                track_durations = np.append(track_durations, chord.duration)
            unique_durations = np.unique(track_durations)
            unique_durations = unique_durations[unique_durations < 128]  # TODO: так можно не рассматривать паузы.

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


# соединяет аккорды однотипных дорожек, удаляет лишние дорожки
# Work in progress
class MergeTracksMapper(BaseMapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_stats(['non-uniform track', 'uniform track', 'not enough tracks', 'tracks merged'])

    def process(self, song):
        indices = self.get_mergeable_track_indices(song)
        tracks = song.tracks
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
        # удаляет неравномерные треки и возвращает массив из дорожек, которые можно смерджить
        tracks = np.array(song.tracks)
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
