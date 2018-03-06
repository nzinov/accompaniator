from prestructures import *
from prefetch import *

from structures import *
from fetch import *

class BaseHandler:
    def __init__(self):
        pass

    def process(self, song):
        pass

    def log(self, param, value):
        self.stats[param] = value

    def get_stats(self):
        return self.stats

    stats = {}

# Convention: dummy chord should persist.
# This method is quite rough, and some small notes could be appended to wrong chords.
class NoizeReductionHandler(BaseHandler):
    @staticmethod
    def myround(x, base=5):
        return int(base*round(float(x)/base))

    def process(self, song):
        for track in song.tracks:
            # Round notes durations.
            for chord in track.chords:
                chord.delta = self.myround(chord.delta, 4)
                for note in chord.notes:
                    note.duration = self.myround(note.duration, 4)

            # Concatenate chords.
            new_chords = [PreChord(0, [])]
            for chord in track.chords[1:]:
                if chord.delta != 0:
                    new_chords.append(chord)
                else:
                    new_chords[-1].notes += chord.notes

            # Persist dummy chord.
            if new_chords[0] != PreChord(0, []):
                new_chords.insert(0, PreChord(0, []))
            track.chords = new_chords
        return song

class UnneededInstrumentsHandler(BaseHandler):
    def process(self, song):
        new_tracks = []
        stats = {'sound_effects':0, 'drums':0, 'synth':0, 'normal':0}
        for track in song.tracks:
            if track.program >= 112:
                stats['sound_effects'] += 1
            elif 80 <= track.program <= 103:
                stats['synth'] += 1
            elif track.program == 9:
                stats['drums'] += 1
            else:
                stats['normal'] += 1
                new_tracks.append(track)
        song.tracks = new_tracks
        return song

