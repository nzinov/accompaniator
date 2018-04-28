import mido
import os
import tqdm
import logging as log
from ml.prestructures import *
from ml.structures import *
from ml.dataset.pipeline import *
from multiprocessing.pool import Pool


def in_ipynb():
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True  # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False  # Probably standard Python interpreter


def get_progressbar(**kwargs):
    if in_ipynb():
        return tqdm.tqdm_notebook(**kwargs)
    else:
        return tqdm.tqdm(**kwargs)


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
        return time / (tpb / (128 / 4))

    @staticmethod
    def is_note_on(message):
        return message.type == 'note_on' and message.velocity != 0

    @staticmethod
    def is_note_off(message):
        return message.type == 'note_off' or (message.type == 'note_on' and message.velocity == 0)

    @staticmethod
    def get_chords(notes_list, tpb):
        # Dummy chord
        chords = [PreChord(0, [])]

        cur_chord_duration = 0
        for i, note in enumerate(notes_list):
            cur_chord_duration += SongCorpus.get_duration(tpb, note.time)
            if SongCorpus.is_note_on(note):
                cur_duration = 0

                for j in range(i + 1, len(notes_list)):
                    cur_duration += SongCorpus.get_duration(tpb, notes_list[j].time)

                    if notes_list[j].note == note.note and SongCorpus.is_note_off(notes_list[j]):

                        cur_duration = cur_duration
                        # If note continues chord
                        if SongCorpus.get_duration(tpb, note.time) == 0 and SongCorpus.is_note_on(notes_list[i - 1]):
                            chords[-1].notes.append(PreNote(note.note, cur_duration, note.velocity))
                        else:  # If note is the first note of new chord
                            chords.append(
                                PreChord(cur_chord_duration, [PreNote(note.note, cur_duration, note.velocity)]))
                            cur_chord_duration = 0
                        break
        return chords

    @staticmethod
    def process_file(filename, output_file):
        try:
            try:
                mid = mido.MidiFile(filename)
                tpb = mid.ticks_per_beat
            except Exception as e:
                log.warning('Broken midi %s: %s' % (filename, e))
                return

            song = Song()
            song.name = filename

            try:
                song.bpm = int(mido.tempo2bpm(list(filter(lambda msg: msg.type == 'set_tempo', mid))[0].tempo))
            except IndexError:
                song.bpm = 120  # Default by MIDI standard?

            time_signatures = []
            time = 0
            for msg in mid:
                if hasattr(msg, 'time'):
                    time += SongCorpus.get_duration(tpb, msg.time)
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

                    def get_item_or_default(track, name, func, default=''):
                        try:
                            vars(track)[name] = func(list(filter(lambda msg: msg.type == name, mid_track))[0])
                        except IndexError:
                            vars(track)[name] = default

                    get_item_or_default(track, 'track_name', lambda x: x.name)
                    get_item_or_default(track, 'instrument_name', lambda x: x.name)
                    get_item_or_default(track, 'program_change', lambda x: int(x.program), default=-1)
                    get_item_or_default(track, 'key_signature', lambda x: x.key)

                    notes_list = list(filter(lambda msg: msg.type == 'note_on' or msg.type == 'note_off', mid_track))

                    track.chords = SongCorpus.get_chords(notes_list, tpb)

                    song.add_track(track)

                except Exception as e:
                    log.warning('PreTracks broken', e)
                    break

            if output_file:
                song.dump(output_file)
            return song
        except Exception as e:
            log.warning('MIDI broken %s' % filename)
            log.warning(e)
            return None

    @staticmethod
    def process_recursive_from_directory(dirname, output_file, with_progressbar=True):
        total = sum([len(files) for r, d, files in os.walk(dirname)])
        pb = get_progressbar(total=total, disable=not with_progressbar)
        for root, directories, filenames in os.walk(dirname):
            for filename in filenames:
                if filename[-4:].lower() == '.mid':
                    SongCorpus.process_file(os.path.join(root, filename), output_file)
                    pb.update(n=1)

    @staticmethod
    def process_subdir(subdir):
        print(subdir)
        with open(os.path.join(subdir, 'out.pickle'), 'wb') as output_file:
            SongCorpus.process_recursive_from_directory(subdir, output_file, with_progressbar=False)

    @staticmethod
    def process_parallel_from_directory(dirname):
        pool = Pool(None)
        subdirs = [os.path.join(dirname, subdirname)
                   for subdirname in os.listdir(dirname) if os.path.isdir(os.path.join(dirname, subdirname))]
        print('Total:', len(subdirs))
        pool.map(SongCorpus.process_subdir, subdirs)
        pool.close()
        pool.join()

    def apply_pipeline(self, input_file_name, output_file_name, max_count=None):

        with open(input_file_name, 'rb') as input_file, open(output_file_name, 'wb+') as output_file:
            pb = get_progressbar()

            i = 0
            while True:
                try:
                    song = Song()
                    song.undump(input_file)
                    songs = self.pipeline.process([song])
                    if songs:
                        for song in songs:
                            song.dump(output_file)
                    pb.update(n=1)
                    i += 1
                    if max_count is not None and i >= max_count:
                        break
                except EOFError:
                    break
                # except Exception as e:
                #     log.warning(e)
        return self.pipeline.get_stats()

    def load_from_file(self, filename, max_count=None):
        with open(filename, 'rb') as input_file:
            pb = get_progressbar()

            i = 0
            while True:
                try:
                    song = Song()
                    song.undump(input_file)
                    self.songs.append(song)
                    pb.update(n=1)
                    i += 1
                    if max_count is not None and i >= max_count:
                        break
                except EOFError:
                    break
                except Exception as e:
                    log.warning(e)
                    break

    def save_to_file(self, filename, append=True):
        with open(filename, '%sb' % ('a' if append else 'w')) as output_file:
            for song in self.songs:
                song.dump(output_file)

    def print(self, **kwargs):
        for i, song in enumerate(self.songs):
            print(i, song.str(**kwargs), end='\n')
