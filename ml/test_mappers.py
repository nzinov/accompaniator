import unittest
from mappers import *


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


if __name__ == '__main__':
    unittest.main()
