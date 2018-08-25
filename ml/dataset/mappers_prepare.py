from ml.dataset.base_mapper import BaseMapper, MapperError
import numpy as np

class VarietyMapper(BaseMapper):
    """Removes songs with too many repeating chords."""

    def __init__(self, min_variety=0.5, **kwargs):
        super().__init__(**kwargs)
        self.min_variety = min_variety
        self.stats['variety'] = dict()

    def process(self, song):
        equal, non_equal = 0, 0
        for track in song.tracks:
            for i in range(len(track.chords)-1):
                if track.chords[i] == track.chords[i+1]:
                    equal += 1
                else:
                    non_equal += 1

        variety = non_equal/(equal + non_equal)
        self.increment_stat(variety, self.stats['variety'])
        if variety < self.min_variety:
            raise MapperError('Small variety')

        return song


class ClassifyChordsMapper(BaseMapper):

    @staticmethod
    def map_many(iterable, function, *other):
        if other:
            return ClassifyChordsMapper.map_many(map(function, iterable), *other)
        return map(function, iterable)

    @staticmethod
    def apply_many(elem, function, *other):
        if other:
            return ClassifyChordsMapper.apply_many(function(elem), *other)
        return function(elem)

    def __init__(self, min_variety=0.5, **kwargs):
        super().__init__(**kwargs)
        self.chords_set = set()
        self.cache = dict()
        self. final_dict = dict()

        self.stats['variety'] = dict()

    def process(self, song):
        for chord in song.chord_track.chords:
            if chord.notes != []:
                if tuple(chord.notes) not in self.cache:
                    s = chord.get_music21_repr().pitchedCommonName
                    final_s = ClassifyChordsMapper.apply_many(s,
                                         lambda s: s.split(' ')[0],
                                         lambda s: s[:3],
                                         lambda s: s[:2] if s[2] == '-' else s,
                                         lambda s: s.replace('-', 'b'))
                    self.final_dict[tuple(chord.notes)] = final_s
                    self.cache[tuple(chord.notes)] = s
                    self.chords_set.add(final_s)

        melody = [0 if not chord.notes else chord.notes[0].number for chord in song.melody_track.chords]
        rhythm = ['' if not chord.notes else self.final_dict[tuple(chord.notes)] for chord in song.chord_track.chords]

        return [[melody, rhythm]]
