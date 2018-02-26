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



'''
note1 = Note(440)
note2 = Note(330)

chord1 = Chord([note1, note2], 5, 0)
chord2  = Chord([], 5, 0)
chord1_ = Chord([note1, note2], 3, 0)
chord2_  = Chord([], 3, 0)
chord1_1 = Chord([note1, note2], 5, 0)
chord2_1  = Chord([], 5, 0)

track1 = Track([chord1, chord2], 'guitar')
track2 = Track([chord1_, chord2_], 'voice')
track3 = Track([chord1_1, chord2_1], 'drums')

song = Song([track1, track2, track3], 5, "test song")
print(song)

merge_tracks(song)
print(song)
'''
