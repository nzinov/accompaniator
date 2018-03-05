import mido
import os
import tqdm
from prestructures import *
import logging as log
import unittest

class PreSongCorpus:
    songs = []

    @staticmethod
    def get_duration(tpb, time):
        """
        Get duration in 128-th notes.
        :param tpb: tick per beat
        :param time: time in ticks
        :return:
        """
        return round(time/(tpb/(128/4)))

    @staticmethod
    def is_note_on(message):
        return message.type == 'note_on' and message.velocity != 0

    @staticmethod
    def is_note_off(message):
        return message.type == 'note_off' or (message.type == 'note_on' and message.velocity == 0)

    def get_chords(self, notes_list, tpb):
        # Dummy chord
        chords = [PreChord(0, [])]
        cur_chord_duration = 0
        for i, note in enumerate(notes_list):
            cur_chord_duration += self.get_duration(tpb, note.time)
            if self.is_note_on(note):
                cur_duration = 0

                # if note.time != 0:
                #     # PreNote precedes with pause
                #     chords += [PreChord([PreNote(-1, self.get_duration(tpb, note.time), 0)])]

                for j in range(i + 1, len(notes_list)):
                    cur_duration += self.get_duration(tpb, notes_list[j].time)

                    if notes_list[j].note == note.note and self.is_note_off(notes_list[j]):
                        # If note continues chord
                        if note.time == 0 and self.is_note_on(notes_list[i - 1]):
                            chords[-1].notes.append(PreNote(note.note, cur_duration, note.velocity))
                        else:  # If note is the first note of new chord
                            chords.append(PreChord(cur_chord_duration, [PreNote(note.note, cur_duration, note.velocity)]))
                            cur_chord_duration = 0
                        break
        # Dummy chord removal (if present)
        if chords[0] == PreChord(0, []):
            chords = chords[1:]
        return chords

    def process_file(self, filename, to_self=False):
        try:
            try:
                mid = mido.MidiFile(filename)
                tpb = mid.ticks_per_beat
            except Exception as e:
                log.warning('Broken midi %s: %s'%(filename, e))
                return

            song = PreSong()
            song.name = filename
            try:
                song.bpm = int(mido.tempo2bpm(list(filter(lambda msg: msg.type == 'set_tempo', mid))[0].tempo))
            except Exception as e:
                song.bpm = 196  # TODO: better default value?

            for mid_track in mid.tracks:
                try:
                    # Треки с метаданными не обрабатываем
                    if len(list(filter(lambda msg: msg.type == 'note_on', mid_track))) == 0:
                        continue

                    track = PreTrack()

                    try:
                        track.track_name = \
                            list(filter(lambda msg: msg.type == 'track_name', mid_track))[0].name
                    except Exception:
                        track.track_name = ''

                    try:
                        track.instrument_name = \
                            list(filter(lambda msg: msg.type == 'instrument_name', mid_track))[0].name
                    except Exception:
                        track.instrument_name = ''

                    try:
                        track.program = list(filter(lambda msg: msg.type == 'program_change', mid_track))[0].program
                    except Exception:
                        track.program = -1
                    # if program_change >= 97 or (33 <= program_change <= 40):
                    #    continue

                    try:
                        key_signature = list(filter(lambda msg: msg.type == 'key_signature', mid_track))[0].key
                        song.key_signature = key_signature
                    except Exception:
                        song.key_signature = ''

                    notes_list = list(filter(lambda msg: msg.type == 'note_on' or msg.type == 'note_off', mid_track))

                    track.chords = self.get_chords(notes_list, tpb)

                    song.add_track(track)

                except Exception as e:
                    log.warning('PreTracks broken', e)
                    break

            if to_self:
                self.songs.append(song)
            return song
        except Exception as e:
            log.warning('MIDI broken %s'%filename)
            log.warning(e)
            return None

    def process_recursive_from_directory(self, dirname, to_self=False):
        songs = []
        total = sum([len(files) for r, d, files in os.walk(dirname)])
        pb = tqdm.tqdm(total=total)
        for root, directories, filenames in os.walk(dirname):
            for filename in filenames:
                if filename[-4:].lower() == '.mid':
                    song = self.process_file(os.path.join(root, filename))
                    if song is not None:
                        songs.append(song)
                    pb.update(n=1)
                else:
                    log.warning("Non-midi file %s"%filename)
        if to_self:
            self.songs += songs


    def load_from_file(self, filename):
        with open(filename, 'rb') as inf:
            pb = tqdm.tqdm_notebook(total=128)
            while True:
                try:
                    song = PreSong()
                    song.undump(inf)
                    self.songs.append(song)
                    pb.update(n=1)
                except Exception as e:
                    log.warning(e)
                    break

    def save_to_file(self, filename):
        with open(filename, 'wb') as outf:
            for song in self.songs:
                song.dump(outf)

    def print(self):
        for song in self.songs:
            print("song: {}".format(str(song)))
            for track in song.tracks:
                print("track: {}".format(str(track)))
                for chord in track.chords:
                    print("chord: {}".format(str(chord)))

corpus=PreSongCorpus()
messages = \
[mido.Message('note_on', note=1, time=0),
 mido.Message('note_off', note=1, time=48),
 mido.Message('note_on', note=2, time=0),
 mido.Message('note_off', note=2, time=48)]
print(messages)
print(corpus.get_chords(notes_list=messages, tpb=192))

# class TestChords(unittest.TestCase):
#
#     def test1(self):
#
#
#     def test_upper(self):
#         self.assertEqual('foo'.upper(), 'FOO')
#
#     def test_isupper(self):
#         self.assertTrue('FOO'.isupper())
#         self.assertFalse('Foo'.isupper())
#
#     def test_split(self):
#         s = 'hello world'
#         self.assertEqual(s.split(), ['hello', 'world'])
#         # check that s.split fails when the separator is not a string
#         with self.assertRaises(TypeError):
#             s.split(2)
#
# if __name__ == '__main__':
#     unittest.main()