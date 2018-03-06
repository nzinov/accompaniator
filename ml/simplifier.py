from structures import *
import numpy as np


def uniform_and_mergable(song):  # удаляет неравномерные треки и возвращает массив из дорожек, которые можно смерджить
    tracks = np.array(song.tracks)
    durations = np.array([])
    for track in tracks:
        chords = np.array(track.chords)
        duration = np.array([])
        for chord in chords:
            duration = np.append(duration, chord.duration)
        unique_durations = np.unique(duration)
        if len(unique_durations) != 1:
            song.del_track(track)
        durations = np.append(durations, unique_durations[0])
    u, indices = np.unique(durations, return_inverse=True)
    return indices


def make_indexes(indices):  # создает список списков, объединяя в один список индексы дорожек, которые можно соединить
    indexes = [[]]
    for index in range(np.max(indices)):
        indexes.insert(0, [])
    for i, index in enumerate(indices):
        indexes[index].append(i)
    return indexes


def merge_tracks(song):  # соединяет аккорды однотипных дорожек, удаляет лишние дорожки
    indices = uniform_and_mergable(song)
    tracks = song.tracks
    uni_indices = make_indexes(indices)
    for indices in uni_indices:
        if len(indices) > 1:
            for i in range(1, len(indices)):
                tracks[indices[0]].merge_track(tracks[indices[i]])
                song.del_track_num(indices[i])


def join_chords(song):  # соединяет два подряд идущих одинаковых аккорда
    for track in song.tracks:
        chords = track.chords
        deleted_indexes = np.array([])
        for i in np.range(len(chords)-1):
            if chords[i] == chords[i+1]:
                deleted_indexes = np.append(deleted_indexes, i+1)
        track.chords = np.delete(chords, deleted_indexes)


def cat_track(song):  # если на дорожке есть закономерность, обрезает дорожку
    for track in np.array(song.tracks):
        for i in np.range(len(track)/2 + 1):
            shaped_track = np.reshape(track, (i, -1))
            unique, counts = np.unique(shaped_track, return_counts=True)
            if counts == 1:
                track = track[:i]


def split_song(song):  # делит песню на несколько песен
    chords_len = np.array([])
    for track in song.tracks:
        curr_len = 0
        for chord in track.chords:
            curr_len += chord.duration
        chords_len = np.append(chords_len, curr_len)
    u, indices = np.unique(chords_len, return_inverse=True)
    uni_indices = make_indexes(indices)
    songs = []
    for indices in uni_indices:
        tracks = song.tracks[indices]
        new_song = Song(tracks)
        songs.append(new_song)
    return songs