import mido
import os
import tqdm
from prestructures import *
from structures import *
import logging as log
from pipeline import *


class SongCorpus:

    def __init__(self):
        self.songs = []
        self.pipeline = Pipeline([])

    @staticmethod
    def get_duration(tpb, time):
        """
        Get duration in 128-th notes.
        :param tpb: tick per beat
        :param time: time in ticks
        :return: float
        """
        return time/(tpb/(128/4))

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

                for j in range(i + 1, len(notes_list)):
                    cur_duration += self.get_duration(tpb, notes_list[j].time)

                    if notes_list[j].note == note.note and self.is_note_off(notes_list[j]):

                        cur_duration = cur_duration
                        # If note continues chord
                        if self.get_duration(tpb, note.time) == 0 and self.is_note_on(notes_list[i - 1]):
                            chords[-1].notes.append(PreNote(note.note, cur_duration, note.velocity))
                        else:  # If note is the first note of new chord
                            chords.append(
                                PreChord(cur_chord_duration, [PreNote(note.note, cur_duration, note.velocity)]))
                            cur_chord_duration = 0
                        break
        return chords

    def process_file(self, filename, to_self=False, outf=None):
        try:
            try:
                mid = mido.MidiFile(filename)
                tpb = mid.ticks_per_beat
                # print(tpb)
                # mid.ticks_per_beat = 480
            except Exception as e:
                log.warning('Broken midi %s: %s'%(filename, e))
                return

            song = Song()
            song.name = filename

            try:
                song.bpm = int(mido.tempo2bpm(list(filter(lambda msg: msg.type == 'set_tempo', mid))[0].tempo))
            except Exception:
                song.bpm = 120  # Default by MIDI standard?

            time_signatures = []
            time = 0
            for msg in mid:
                if hasattr(msg, 'time'):
                    time += self.get_duration(tpb, msg.time)
                if msg.type == 'time_signature':
                    time_signatures.append(
                        TimeSignature(time,
                                      msg.numerator, msg.denominator,
                                      msg.clocks_per_click, msg.notated_32nd_notes_per_beat))

            song.time_signature = time_signatures

            for mid_track in mid.tracks:
                try:
                    # Треки с метаданными не обрабатываем
                    if len(list(filter(lambda msg: msg.type == 'note_on', mid_track))) == 0:
                        continue

                    track = Track()

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
            if outf:
                song.dump(outf)
            return song
        except Exception as e:
            log.warning('MIDI broken %s'%filename)
            log.warning(e)
            return None

    def process_recursive_from_directory(self, dirname, to_memory=True, to_self=True, outf=None):
        songs = []
        total = sum([len(files) for r, d, files in os.walk(dirname)])
        pb = tqdm.tqdm_notebook(total=total)
        for root, directories, filenames in os.walk(dirname):
            for filename in filenames:
                if filename[-4:].lower() == '.mid':
                    song = self.process_file(os.path.join(root, filename), to_self=to_self, outf=outf)
                    if song is not None:
                        if to_memory:
                            songs.append(song)
                    pb.update(n=1)
                else:
                    log.warning("Non-midi file %s"%filename)
        return songs

    def apply_pipeline(self, inf_name, outf_name, with_tqdm=True):
        with open(inf_name, 'rb') as inf, open(outf_name, 'wb+') as outf:
            if with_tqdm:
                pb = tqdm.tqdm_notebook()
            while True:
                try:
                    song = Song()
                    song.undump(inf)
                    songs = self.pipeline.process([song])
                    if songs:
                        for song in songs:
                            song.dump(outf)
                    if with_tqdm:
                        pb.update(n=1)
                except EOFError:
                    break
                # except Exception as e:
                #     log.warning(e)
                #     break
                # TODO: раскомментить в продакшене.
        return self.pipeline.get_stats()

    def load_from_file(self, filename, with_tqdm=True):
        with open(filename, 'rb') as inf:
            if with_tqdm:
                pb = tqdm.tqdm_notebook()
            while True:
                try:
                    song = Song()
                    song.undump(inf)
                    self.songs.append(song)
                    if with_tqdm:
                        pb.update(n=1)
                except Exception as e:
                    log.warning(e)
                    break

    def save_to_file(self, filename, append=True):
        with open(filename, '%sb'%('a' if append else 'w')) as outf:
            for song in self.songs:
                song.dump(outf)

    def print(self):
        for song in self.songs:
            print("song: {}".format(str(song)))
            for track in song.tracks:
                print("track: {}".format(str(track)))
                for chord in track.chords:
                    print("chord: {}".format(str(chord)))
