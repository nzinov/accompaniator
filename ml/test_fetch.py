import unittest
from prestructures import *

class TestChords(unittest.TestCase):
    corpus = PreSongCorpus()

    def test1(self):
        messages = \
            [mido.Message('note_on', note=1, time=0),
             mido.Message('note_off', note=1, time=48),
             mido.Message('note_on', note=2, time=0),
             mido.Message('note_off', note=2, time=48)]
        self.assertEqual(str(self.corpus.get_chords(notes_list=messages, tpb=192)),
                         "[{0 [1 8 64]}, {8 [2 8 64]}]")

    def test3(self):
        messages = \
            [mido.Message('note_on', note=1, time=0),
             mido.Message('note_on', note=2, time=0),
             mido.Message('note_off', note=1, time=48),
             mido.Message('note_off', note=2, time=0)]
        self.assertEqual(str(self.corpus.get_chords(notes_list=messages, tpb=192)),
                         "[{0 [1 8 64, 2 8 64]}]")

    def test4(self):
        messages = \
            [mido.Message('note_on', note=1, time=0),
             mido.Message('note_on', note=2, time=0),
             mido.Message('note_off', note=1, time=48),
             mido.Message('note_off', note=2, time=48)]
        self.assertEqual(str(self.corpus.get_chords(notes_list=messages, tpb=192)),
                         "[{0 [1 8 64, 2 16 64]}]")

    def test5(self):
        messages = \
            [mido.Message('note_on', note=1, time=0),
             mido.Message('note_on', note=2, time=0),
             mido.Message('note_on', note=3, time=24),
             mido.Message('note_off', note=3, time=24),
             mido.Message('note_off', note=1, time=0),
             mido.Message('note_off', note=2, time=0)]
        self.assertEqual(str(self.corpus.get_chords(notes_list=messages, tpb=96)),
                         "[{0 [1 16 64, 2 16 64]}, {8 [3 8 64]}]")

    def test6(self):
        messages = \
            [mido.Message('note_on', note=1, time=0),
             mido.Message('note_on', note=2, time=0),
             mido.Message('note_on', note=3, time=24),
             mido.Message('note_off', note=3, time=24),
             mido.Message('note_off', note=1, time=48),
             mido.Message('note_off', note=2, time=48)]
        self.assertEqual(str(self.corpus.get_chords(notes_list=messages, tpb=96)),
                         "[{0 [1 32 64, 2 48 64]}, {8 [3 8 64]}]")

if __name__ == '__main__':
    unittest.main()
