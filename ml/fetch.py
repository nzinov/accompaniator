import mido
import os
import tqdm
from structures import *
import logging as log

class SongCorpus:
    songs = []

    @staticmethod
    def get_duration(tpb, time):
        return round(time/(tpb/(128/4)))

    @staticmethod
    def is_note_on(message):
        return message.type == 'note_on' and message.velocity != 0

    @staticmethod
    def is_note_off(message):
        return message.type == 'note_off' or (message.type == 'note_on' and message.velocity == 0)

    def get_chords(self, notes_list, tpb):
        # Dummy chord
        chords = [Chord([], 0, 0)]
        for i, note in enumerate(notes_list):
            if self.is_note_on(note):
                cur_duration = 0

                if note.time != 0:
                    # Note precedes with pause
                    chords += [Chord([], self.get_duration(tpb, note.time), 0)]

                for j in range(i + 1, len(notes_list)):
                    cur_duration += self.get_duration(tpb, notes_list[j].time)
                    if notes_list[j].note == note.note and self.is_note_off(notes_list[j]):
                        # If note continues chord
                        if note.time == 0 and self.is_note_on(notes_list[i - 1]):
                            chords[-1].notes.append(Note(note.note))
                            # TODO: what if length of notes in chord is different (arpeggio?) ?
                            # if chords[-1].duration != cur_duration
                            #    or chords[-1].velocity != note.velocity:
                            #    log.warning("No")
                            chords[-1].duration = cur_duration
                            chords[-1].velocity = note.velocity
                        else:  # If note is the first note of new chord
                            chords.append(Chord([Note(note.note)], cur_duration, note.velocity))
                        break
        # Dummy chord removal (if present)
        if chords[0] == Chord([], 0, 0):
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

            song = Song()
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
                    log.warning('Track broken', e)
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
                    song = Song()
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

