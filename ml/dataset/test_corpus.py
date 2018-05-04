import unittest
from ml.dataset.corpus import *


class TestChords(unittest.TestCase):
    corpus = SongCorpus()

    def test1(self):
        messages = \
            [mido.Message('note_on', note=1, time=0),
             mido.Message('note_off', note=1, time=48),
             mido.Message('note_on', note=2, time=0),
             mido.Message('note_off', note=2, time=48)]
        self.assertEqual("[{0 []}, {0.0 [1 8.0 64]}, {8.0 [2 8.0 64]}]",
                         str(self.corpus.get_chords(notes_list=messages, tpb=192)))

    def test3(self):
        messages = \
            [mido.Message('note_on', note=1, time=0),
             mido.Message('note_on', note=2, time=0),
             mido.Message('note_off', note=1, time=48),
             mido.Message('note_off', note=2, time=0)]
        self.assertEqual("[{0 []}, {0.0 [1 8.0 64, 2 8.0 64]}]",
                         str(self.corpus.get_chords(notes_list=messages, tpb=192)))

    def test4(self):
        messages = \
            [mido.Message('note_on', note=1, time=0),
             mido.Message('note_on', note=2, time=0),
             mido.Message('note_off', note=1, time=48),
             mido.Message('note_off', note=2, time=48)]
        self.assertEqual("[{0 []}, {0.0 [1 8.0 64, 2 16.0 64]}]",
                         str(self.corpus.get_chords(notes_list=messages, tpb=192)))

    def test5(self):
        messages = \
            [mido.Message('note_on', note=1, time=0),
             mido.Message('note_on', note=2, time=0),
             mido.Message('note_on', note=3, time=24),
             mido.Message('note_off', note=3, time=24),
             mido.Message('note_off', note=1, time=0),
             mido.Message('note_off', note=2, time=0)]
        self.assertEqual("[{0 []}, {0.0 [1 16.0 64, 2 16.0 64]}, {8.0 [3 8.0 64]}]",
                         str(self.corpus.get_chords(notes_list=messages, tpb=96)))

    def test6(self):
        messages = \
            [mido.Message('note_on', note=1, time=0),
             mido.Message('note_on', note=2, time=0),
             mido.Message('note_on', note=3, time=24),
             mido.Message('note_off', note=3, time=24),
             mido.Message('note_off', note=1, time=48),
             mido.Message('note_off', note=2, time=48)]
        self.assertEqual("[{0 []}, {0.0 [1 32.0 64, 2 48.0 64]}, {8.0 [3 8.0 64]}]",
                         str(self.corpus.get_chords(notes_list=messages, tpb=96)))


if __name__ == '__main__':
    unittest.main()
