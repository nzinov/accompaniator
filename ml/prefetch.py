import mido
import os
import tqdm
from prestructures import *
import logging as log


class TimeSignature:
    def __init__(self, time, numerator, denominator, clocks_per_click, notated_32nd_notes_per_beat):
        self.time = time
        self.numerator = numerator
        self.denominator = denominator
        self.clocks_per_click = clocks_per_click
        self.notated_32nd_notes_per_beat = notated_32nd_notes_per_beat

    def __str__(self):
        return "%s (%s %s %s %s)"%(self.time,
                                   self.numerator, self.denominator,
                                   self.clocks_per_click, self.notated_32nd_notes_per_beat)

    def __repr__(self):
        return self.__str__()

class PreSongCorpus:

    def __init__(self):
        self.songs = []

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
            #print(song.name)
            try:
                song.bpm = int(mido.tempo2bpm(list(filter(lambda msg: msg.type == 'set_tempo', mid))[0].tempo))
            except Exception as e:
                song.bpm = 120  # Default by MIDI standard

            time_signatures = []
            time = 0
            for msg in mid:
                if hasattr(msg, 'time'):
                    #print(msg)
                    time += self.get_duration(tpb, msg.time)
                if msg.type == 'time_signature':
                    time_signatures.append(
                        TimeSignature(time,
                                      msg.numerator, msg.denominator,
                                      msg.clocks_per_click, msg.notated_32nd_notes_per_beat))
                    #print(time_signatures[-1])
            song.time_signatures = time_signatures
            # time_signatures = list(filter(lambda msg: msg.type == 'time_signature', mid))
            # #print(len(time_signatures))
            # if len(time_signatures) == 0:
            #     print('NO TIME SIGNATURE')
            #     pass
            # elif len(time_signatures) == 1:
            #     song.time_signature = (time_signatures[0].numerator, time_signatures[0].denominator)
            #     print('TIME SIGNATURE', song.time_signature)
            # else:
            #     split_indices = [index for index, value in enumerate(list(mid)) if value.type == 'time_signature']
            #     split_fractions = [(ts.numerator, ts.denominator, ts.clocks_per_click, ts.notated_32nd_notes_per_beat) for ts in time_signatures]
            #     print(split_indices, split_fractions)
            #
            #
            # num = map(lambda ts: ts.numerator, time_signatures)
            # den = map(lambda ts: ts.denominator, time_signatures)
            # print(set(num), set(den))

            # if 4 in set(num):
            #     print('#####################',time_signatures)
            #     print(set(num), set(den))
            #     print(list(num), list(den))
            #     print(set(list(zip(num,den))))
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

    def process_recursive_from_directory(self, dirname, to_self=True):
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

    def load_from_file(self, filename, with_tqdm=True):
        with open(filename, 'rb') as inf:
            if with_tqdm:
                pb = tqdm.tqdm_notebook()
            while True:
                try:
                    song = PreSong()
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
