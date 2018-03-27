import unittest
from mappers import *
from simplifier import *
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
        self.assertEqual('[{10 0 []}, {8 48.0 [1, 2]}, {2 0 []}, {16 96.0 [3, 4]}, {8 48.0 [1, 2]}]',
                         str(chords))

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
        self.assertEqual('[{8 64.0 [1, 2]}, {16 0 []}, {8 64.0 [1, 2]}]',
                         str(song.tracks[0].chords))
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

    def testIndexing(self):
        chord = Chord([Note(1)], 4, 127)
        pause = Chord([], 8, 127)
        big_pause = Chord([], 256, 127)

        chords = [chord, big_pause, chord, pause, chord]
        track = Track([deepcopy(chord) for chord in chords])

        cpm = CutPausesMapper(good_track_ratio=1)
        self.assertEqual(cpm.get_index_of_time(track, 0), (0, 0))
        self.assertEqual(cpm.get_index_of_time(track, 3), (0, 0))
        self.assertEqual(cpm.get_index_of_time(track, 9), (1, 4))

    def testSingleTrackCutting(self):
        chord = Chord([Note(1)], 4, 127)
        pause = Chord([], 8, 127)
        big_pause = Chord([], 256, 127)

        chords = [chord, big_pause, chord, pause, chord]
        track = Track([deepcopy(chord) for chord in chords])
        song = Song([deepcopy(track), deepcopy(track)])

        song1, song2 = deepcopy(song), deepcopy(song)

        cpm = CutPausesMapper(strategy='split', good_track_ratio=1)
        processed = cpm.process(song1)
        self.assertEqual('[{4 127 [1]}]',
                         str(processed[0].tracks[0].chords))
        self.assertEqual('[{4 127 [1]}, {8 127 []}, {4 127 [1]}]',
                         str(processed[1].tracks[0].chords))

        cpm = CutPausesMapper(strategy='cat', good_track_ratio=1)
        processed = cpm.process(song2)
        self.assertEqual('[{4 127 [1]}, {4 127 [1]}, {8 127 []}, {4 127 [1]}]',
                         str(processed.tracks[0].chords))

    def testMultipleTracksCutting(self):
        chord = Chord([Note(1)], 4, 127)
        pause = Chord([], 8, 127)
        big_pause = Chord([], 256, 127)
        medium_pause = Chord([], 250, 127)

        chords_list = \
            [[chord, big_pause, chord, pause, chord],
             [pause, medium_pause, chord, pause, chord]]
        tracks = [Track([deepcopy(chord) for chord in chords]) for chords in chords_list]
        song = Song(tracks)

        song1, song2 = deepcopy(song), deepcopy(song)

        cpm = CutPausesMapper(strategy='split', good_track_ratio=1)
        processed = cpm.process(song1)

        self.assertEqual('[{4 127 [1]}]',
                         str(processed[0].tracks[0].chords))
        self.assertEqual('[{4 127 [1]}, {8 127 []}, {4 127 [1]}]',
                         str(processed[1].tracks[0].chords))
        self.assertEqual('[{4 127 []}]',
                         str(processed[0].tracks[1].chords))
        self.assertEqual('[{2 127 [1]}, {8 127 []}, {4 127 [1]}, {2 -1 []}]',
                         str(processed[1].tracks[1].chords))

        cpm = CutPausesMapper(strategy='cat', good_track_ratio=1)
        processed = cpm.process(song2)

        self.assertEqual('[{4 127 [1]}, {4 127 [1]}, {8 127 []}, {4 127 [1]}]',
                         str(processed.tracks[0].chords))
        self.assertEqual('[{4 127 []}, {2 127 [1]}, {8 127 []}, {4 127 [1]}, {2 -1 []}]',
                         str(processed.tracks[1].chords))

    def testSongCuttingAtEdges(self):
        chord = Chord([Note(1)], 100, 127)
        medium_pause = Chord([], 160, 127)

        chords_list = \
            [[chord, chord, medium_pause],
             [medium_pause, chord, chord]]
        tracks = [Track([deepcopy(chord) for chord in chords]) for chords in chords_list]
        song = Song(tracks)

        song1, song2 = deepcopy(song), deepcopy(song)

        # cpm = CutPausesMapper(strategy='split', good_track_ratio=1)
        # processed = cpm.process(song1)
        #
        # self.assertEqual('[{10 127 [1]}]',
        #                  str(processed[0].tracks[0].chords))
        # self.assertEqual('[{10 127 [1]}]',
        #                  str(processed[0].tracks[1].chords))

        cpm = CutPausesMapper(strategy='cat', good_track_ratio=1)

        processed = cpm.process(song2)

        self.assertEqual('[{40 127 [1]}]',
                         str(processed.tracks[0].chords))
        self.assertEqual('[{40 127 [1]}]',
                         str(processed.tracks[1].chords))

    def testPausesInRow(self):
        chord = Chord([Note(1)], 4, 127)
        medium_pause = Chord([], 150, 127)

        chords_list = \
            [[chord, medium_pause, medium_pause],
             [chord, medium_pause, medium_pause]]
        tracks = [Track([deepcopy(chord) for chord in chords]) for chords in chords_list]
        song = Song(tracks)

        song1, song2 = deepcopy(song), deepcopy(song)

        # cpm = CutPausesMapper(strategy='split', good_track_ratio=1)
        # processed = cpm.process(song1)
        #
        # self.assertEqual('[{100 127 [1]}]',
        #                  str(processed[0].tracks[0].chords))
        # self.assertEqual('[{100 127 [1]}]',
        #                  str(processed[0].tracks[1].chords))

        cpm = CutPausesMapper(strategy='cat', good_track_ratio=1)
        processed = cpm.process(song2)

        self.assertEqual('[{4 127 [1]}]',
                         str(processed.tracks[0].chords))
        self.assertEqual('[{4 127 [1]}]',
                         str(processed.tracks[1].chords))

    def testCutToZero(self):
        medium_pause = Chord([], 150, 127)

        chords_list = \
            [[medium_pause, medium_pause],
             [medium_pause, medium_pause]]
        tracks = [Track([deepcopy(chord) for chord in chords]) for chords in chords_list]
        song = Song(tracks)

        song1, song2 = deepcopy(song), deepcopy(song)

        # cpm = CutPausesMapper(strategy='split', good_track_ratio=1)
        # processed = cpm.process(song1)
        #
        # self.assertEqual('[{100 127 [1]}]',
        #                  str(processed[0].tracks[0].chords))
        # self.assertEqual('[{100 127 [1]}]',
        #                  str(processed[0].tracks[1].chords))

        cpm = CutPausesMapper(strategy='cat', good_track_ratio=1)
        with self.assertRaises(MapperError):
            processed = cpm.process(song2)

class TestMergeTracksMapper(unittest.TestCase):
    def test1(self):
        chord1 = Chord([Note(1), Note(1)], 4, 127)
        chord2 = Chord([Note(2), Note(2)], 4, 127)
        pause = Chord([], 4, 127)

        chords_list = \
            [[chord1, chord1, chord1, pause, chord1],
             [pause, chord2, chord2, pause, chord2]]
        tracks = [Track([deepcopy(chord) for chord in chords], is_melody=False) for chords in chords_list]
        song = Song(tracks)

        mtm = MergeTracksMapper()
        self.assertEqual(
            '[{4 127 [1, 1]}, {4 127 [1, 1, 2, 2]}, {4 127 [1, 1, 2, 2]}, {4 127 []}, {4 127 [1, 1, 2, 2]}]',
            str(mtm.process(song).tracks[0].chords))


class TestSplitChordsToGcdMapper(unittest.TestCase):
    def test(self):
        chord1 = Chord([Note(1), Note(1)], 4, 127)
        chord2 = Chord([Note(1), Note(1)], 8, 127)
        chord3 = Chord([Note(1), Note(1)], 12, 127)

        track = Track([chord1, chord2, chord3])
        song = Song([track])

        tscgm = SplitNonMelodiesToGcdMapper()
        self.assertEqual(
            '[{4 127 [1, 1]}, {4 127 [1, 1]}, {4 127 [1, 1]}, {4 127 [1, 1]}, {4 127 [1, 1]}, {4 127 [1, 1]}]',
            str(tscgm.process(song).tracks[0].chords))


if __name__ == '__main__':
    unittest.main()
