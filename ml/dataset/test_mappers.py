import unittest
from ml.dataset.mappers_preprocess import *
from ml.dataset.mappers_simplify import *
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


class TestMergeTracksMapper(unittest.TestCase):
    def test1(self):
        chord1 = Chord([Note(1), Note(1)], 4, 127)
        chord2 = Chord([Note(2), Note(2)], 4, 127)
        pause = Chord([], 4, 127)

        chords_list = \
            [[chord1, chord1, chord1, pause, chord1],
             [pause, chord2, chord2, pause, chord2]]
        tracks = [Track([])] + [Track([deepcopy(chord) for chord in chords]) for chords in chords_list]
        song = Song(tracks)

        mtm = MergeTracksMapper()
        self.assertEqual(
            '[{4 127 [1, 1]}, {4 127 [1, 1, 2, 2]}, {4 127 [1, 1, 2, 2]}, {4 127 []}, {4 127 [1, 1, 2, 2]}]',
            str(mtm.process(song).tracks[1].chords))


class TestSplitChordsToGcdMapper(unittest.TestCase):
    def test(self):
        chord1 = Chord([Note(1)], 4, 127)
        chord2 = Chord([Note(1)], 8, 127)
        chord3 = Chord([Note(1)], 12, 127)

        track = Track([chord1, chord2, chord3])
        song = Song([track, track])

        tscgm = SplitToGcdMapper(min_gcd=1)
        self.assertEqual(
            '[{4 127 [1]}, {4 127 [1]}, {4 127 [1]}, {4 127 [1]}, {4 127 [1]}, {4 127 [1]}]',
            str(tscgm.process(song).tracks[0].chords))


class TestAdequateCutOutLongChordsMapper(unittest.TestCase):
    def test_cut_chords(self):
        chord1 = Chord([Note(1)], 4, 127)
        chord2 = Chord([Note(2)], 4, 127)
        pause1 = Chord([], 4, 127)
        pause2 = Chord([], 8, 127)

        chords_list = \
            [[chord1, chord1, chord1, chord2],
             [chord1, pause1, pause1, chord2]]
        tracks = [Track([deepcopy(chord) for chord in chords]) for chords in chords_list]
        song = Song(tracks)

        acolcm = AdequateCutOutLongChordsMapper(min_track_duration=0, min_big_chord_duration=5)
        processed = acolcm.process(song)

        self.assertEqual(
            """Song '', 2 tracks, bpm 0
Track '', instrument '' , program -1, with 1 chords 
{4 127 [1]}

Track '', instrument '' , program -1, with 1 chords 
{4 127 [1]}

""", processed[0].str(with_chords=True))
        self.assertEqual(
            """Song '', 2 tracks, bpm 0
Track '', instrument '' , program -1, with 1 chords 
{4 127 [2]}

Track '', instrument '' , program -1, with 1 chords 
{4 127 [2]}

""", processed[1].str(with_chords=True))

    def test_cut_melody(self):
        chord0 = Chord([Note(1)], 2, 127)
        chord1 = Chord([Note(1)], 4, 127)
        chord2 = Chord([Note(2)], 12, 127)
        pause1 = Chord([], 4, 127)
        pause2 = Chord([], 8, 127)

        chords_list = \
            [[chord0, chord1, pause2, chord1],
             [chord0, chord1, pause1, pause1, chord1]]
        tracks = [Track([deepcopy(chord) for chord in chords]) for chords in chords_list]
        song = Song(tracks)

        acolcm = AdequateCutOutLongChordsMapper(min_track_duration=0, min_big_chord_duration=5)
        processed = acolcm.process(song)

        self.assertEqual(
            """Song '', 2 tracks, bpm 0
Track '', instrument '' , program -1, with 2 chords 
{2 127 [1]} {4 127 [1]}

Track '', instrument '' , program -1, with 2 chords 
{2 127 [1]} {4 127 [1]}

""",
            processed[0].str(with_chords=True))
        self.assertEqual(
            """Song '', 2 tracks, bpm 0
Track '', instrument '' , program -1, with 1 chords 
{4 127 [1]}

Track '', instrument '' , program -1, with 1 chords 
{4 127 [1]}

""",
            processed[1].str(with_chords=True))

    def test_cut_melody_at_end(self):
        chord0 = Chord([Note(1)], 2, 127)
        chord1 = Chord([Note(1)], 4, 127)
        chord2 = Chord([Note(2)], 12, 127)
        pause1 = Chord([], 4, 127)
        pause2 = Chord([], 8, 127)

        chords_list = \
            [[chord0, chord1, pause2],
             [chord0, chord1, pause1, chord1]]
        tracks = [Track([deepcopy(chord) for chord in chords]) for chords in chords_list]
        song = Song(tracks)

        acolcm = AdequateCutOutLongChordsMapper(min_track_duration=0, min_big_chord_duration=5)
        processed = acolcm.process(song)
        self.assertEqual("""[{2 127 [1]}, {4 127 [1]}]""",
                         str(processed[0].tracks[0].chords))

    def test_cut_at_end(self):
        chord0 = Chord([Note(1)], 2, 127)
        chord1 = Chord([Note(1)], 4, 127)
        chord2 = Chord([Note(2)], 12, 127)
        pause1 = Chord([], 4, 127)
        pause2 = Chord([], 8, 127)

        chords_list = \
            [[chord0, chord1, pause1, pause1],
             [chord0, chord1, pause2]]
        tracks = [Track([deepcopy(chord) for chord in chords]) for chords in chords_list]
        song = Song(tracks)

        acolcm = AdequateCutOutLongChordsMapper(min_track_duration=0, min_big_chord_duration=5)
        processed = acolcm.process(song)
        self.assertEqual("""[{2 127 [1]}, {4 127 [1]}]""",
                         str(processed[0].tracks[0].chords))

    # def test_fail(self):
    #     corpus = SongCorpus()
    #     corpus.load_from_file('gtp_dataset5.pickle', max_count=10)
    #
    #     song = corpus.songs[1]
    #     acolcm = AdequateCutOutLongChordsMapper(min_track_duration=0, min_big_chord_duration=256)
    #     processed = acolcm.process(song)
    #     print(processed[0].str(with_chords=True))


if __name__ == '__main__':
    unittest.main()
