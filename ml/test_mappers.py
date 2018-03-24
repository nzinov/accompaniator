import unittest
from mappers import *
from copy import deepcopy


class TestPreToFinalConvertMapper(unittest.TestCase):

    def testConvertChords(self):
        note11 = PreNote(1, 8, 32)
        note12 = PreNote(2, 8, 64)
        note21 = PreNote(3, 16, 64)
        note22 = PreNote(4, 16, 128)
        chords = [PreChord(10, [note11, note12]),
                  PreChord(10, [note21, note22]),
                  PreChord(16, [note11, note12])]
        chords = PreToFinalConvertMapper.convert_chords(chords)
        self.assertEqual(str(chords),
                         '[{10 0 []}, {8 48.0 [1, 2]}, {2 0 []}, {16 96.0 [3, 4]}, {8 48.0 [1, 2]}]')

    def testProcess(self):
        note11 = PreNote(1, 8, 64)
        note12 = PreNote(2, 8, 64)
        note2 = PreNote(3, 16, 64)

        equal_durations = [PreChord(0, [note11, note12]), PreChord(24, [note11, note12])]
        not_equal_durations = [PreChord(0, [note11, note2]), PreChord(0, [note12, note2])]

        mapper = PreToFinalConvertMapper()

        song = Song()
        song.tracks = [Track(equal_durations), Track(equal_durations)]
        song = mapper.process(song)
        self.assertEqual(str(song.tracks[0].chords),
                         '[{8 64.0 [1, 2]}, {16 0 []}, {8 64.0 [1, 2]}]')
        # '[{0 [1 8 64, 2 8 64]}, {24 [1 8 64, 2 8 64]}]' - in raw

        song = Song()
        song.tracks = [Track(equal_durations), Track(not_equal_durations)]
        with self.assertRaises(MapperError):
            song = mapper.process(song)

        song = Song()
        song.tracks = [Track(equal_durations)]
        with self.assertRaises(MapperError):
            song = mapper.process(song)


class TestCutPausesMapper(unittest.TestCase):

    def testCutting(self):
        chord = Chord([Note(1)], 4, 127)
        pause = Chord([], 8, 127)
        big_pause = Chord([], 256, 127)

        chords = [chord, big_pause, chord, pause, chord]
        track = Track([deepcopy(chord) for chord in chords])
        song = Song([track])

        cpm = CutPausesMapper()
        self.assertEqual(cpm.get_index_of_time(track, 0), (0, 0))
        self.assertEqual(cpm.get_index_of_time(track, 3), (0, 0))
        self.assertEqual(cpm.get_index_of_time(track, 9), (1, 4))

        self.assertEqual(str(cpm.process(song).tracks[0].chords),
                         '[{4 127 [1]}, {4 127 [1]}, {8 127 []}, {4 127 [1]}]')

    def testSongCutting(self):
        chord = Chord([Note(1)], 4, 127)
        pause = Chord([], 8, 127)
        big_pause = Chord([], 256, 127)
        medium_pause = Chord([], 250, 127)

        chords_list = \
            [[chord, big_pause, chord, pause, chord],
             [pause, medium_pause, chord, pause, chord]]
        tracks = [Track([deepcopy(chord) for chord in chords]) for chords in chords_list]
        song = Song(tracks)

        cpm = CutPausesMapper()
        processed = cpm.process(song)
        self.assertEqual(str(processed.tracks[0].chords),
                         '[{4 127 [1]}, {4 127 [1]}, {8 127 []}, {4 127 [1]}]')
        self.assertEqual(str(processed.tracks[1].chords),
                         '[{4 127 []}, {2 127 [1]}, {8 127 []}, {4 127 [1]}, {2 -1 []}]')


if __name__ == '__main__':
    unittest.main()
