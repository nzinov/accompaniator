from collections import defaultdict

from ml.structures import *

"""
class Track_time_signature_analyzer:
    def __init__(self, track, time_signature_guess, bonus_for_full_length,
                 bonus_for_same_first_chords, bonus_for_max_velocity, bonus_for_both):
        self.track = track
        self.bar_length = int(128 * time_signature_guess)
        self.bonus_for_full_length = bonus_for_full_length
        self.bonus_for_same_first_chords = bonus_for_same_first_chords
        self.bonus_for_max_velocity = bonus_for_max_velocity
        self.bonus_for_both = bonus_for_both
        self.full_length = 0

        
        best_indent = 0
        best_score = 0
        for indent_base in range(int(128 / 8)):
            indent = indent_base * 8
            TABI = self.Track_time_signature_analyzer_by_indent(indent, track, time_signature_guess,
                                                                bonus_for_full_length, bonus_for_same_first_chords,
                                                                bonus_for_max_velocity, bonus_for_both)
            if TABI.full_length and indent_base == 0:
                self.full_length = 1
            print(f'indent: {indent}, score: {TABI.get_score()}')
            if TABI.get_score() > best_score:
                best_score = TABI.get_score()
                best_indent = indent
        self.score = best_score
    def get_score(self):
        return self.score + self.full_length * self.bonus_for_full_length
        """


class TrackTimeSignatureAnalyzer:
    class Bar:
        def __init__(self, bar_chords, duration, continued_long_note=False):
            self.bar_chords = bar_chords
            self.continued_long_note = continued_long_note
            self.duration = duration
            self.max_velocity = self.find_max_velocity(self.bar_chords)
            self.first_chord = bar_chords[0]

        def len(self):
            return self.duration

        @staticmethod
        def find_max_velocity(bar_chords):
            max_velocity = 0
            for chord in bar_chords:
                if chord.velocity > max_velocity:
                    max_velocity = chord.velocity
            return max_velocity

    def __init__(self, track, bar_length, bonus_for_full_length,
                 bonus_for_same_first_chords, bonus_for_max_velocity, bonus_for_both):
        # self.indent = indent
        self.track = track
        self.bar_length = bar_length
        # self.indent = indent
        self.bonus_for_full_length = bonus_for_full_length
        self.bonus_for_same_first_chords = bonus_for_same_first_chords
        self.bonus_for_max_velocity = bonus_for_max_velocity
        self.bonus_for_both = bonus_for_both
        self.full_length = 0
        # self.cut_chords_by_indent()
        self.bars = self.devide_track_by_bars()
        self.score = self.count_track_score()

    def get_score(self):
        return self.score / len(self.bars) + self.full_length * self.bonus_for_full_length

    def print_bars(self):
        i = 0
        for bar in self.bars:
            print(f'bar #{i}, continued: {bar.continued_long_note}, velocity: {bar.max_velocity}')
            for chord in bar.bar_chords:
                print(str(chord))
            i += 1

    """
    def cut_chords_by_indent(self):
        indent_left = self.indent
    
        for chord in self.track.chords:
            if indent_left == 0:
                break
            if chord.duration <= indent_left:
                self.track.chords = self.track.chords[1:]
                indent_left -= chord.duration
            else:
                new_chord = Chord(chord.notes, chord.duration - indent_left, chord.velocity)
                self.track.chords = self.track.chords[1:]
                self.track.chords.insert(0, new_chord)
                indent_left = 0
    """

    def devide_track_by_bars(self):
        bars = []
        bar_sum = 0
        bar_chords = []
        for chord in self.track.chords:
            if chord.duration > (self.bar_length - bar_sum):
                duration = chord.duration
                if bar_sum > 0:
                    new_chord = Chord(chord.notes, self.bar_length - bar_sum, chord.velocity)
                    bar_chords.append(new_chord)
                    bar = self.Bar(bar_chords, self.bar_length)
                    bars.append(bar)
                    bar_chords = []
                    bar_sum = 0
                    duration - (self.bar_length - bar_sum)
                while duration != 0:
                    if duration > self.bar_length:
                        new_chord = Chord(chord.notes, self.bar_length, chord.velocity)
                        bar_chords.append(new_chord)
                        bar = self.Bar(bar_chords, self.bar_length, True)
                        bars.append(bar)
                        bar_chords = []
                        bar_sum = 0
                        duration -= self.bar_length
                    else:
                        new_chord = Chord(chord.notes, duration, chord.velocity)
                        bar_chords.append(new_chord)
                        bar_sum = duration
                        duration = 0
                continue
            bar_sum += chord.duration
            bar_chords.append(chord)
            if bar_sum == self.bar_length:
                bar = self.Bar(bar_chords, self.bar_length)
                bars.append(bar)
                bar_chords = []
                bar_sum = 0
        if bar_sum > 0:
            bar = self.Bar(bar_chords, bar_sum)
            bars.append(bar)
        else:
            self.full_length = 1
        return bars

    def count_track_score(self):
        previous_first_bar_chord = self.bars[0].first_chord
        score = 0
        for bar in self.bars[1:]:
            if not bar.continued_long_note:
                if str(bar.first_chord) == str(previous_first_bar_chord):
                    score += self.bonus_for_same_first_chords
                    if bar.first_chord.velocity == bar.max_velocity:
                        score += self.bonus_for_both
                if bar.first_chord.velocity == bar.max_velocity:
                    score += self.bonus_for_max_velocity
            previous_first_bar_chord = bar.first_chord
        return score


class SongTimeSignatureAnalyzer:
    def __init__(self, song, time_signature_guess, bonus_for_full_length,
                 bonus_for_same_first_chords, bonus_for_max_velocity, bonus_for_both, group_coefficients):
        self.song = song
        self.bar_length = int(128 * time_signature_guess)
        self.bonus_for_full_length = bonus_for_full_length
        self.bonus_for_same_first_chords = bonus_for_same_first_chords
        self.bonus_for_max_velocity = bonus_for_max_velocity
        self.bonus_for_both = bonus_for_both
        self.full_length = 0
        self.groups_coefficients = group_coefficients

        self.groups = self.divide_tracks_on_groups(song)
        self.score = self.count_song_score()

    @staticmethod
    def divide_tracks_on_groups(song):
        groups = {"drums": [], "bass": [], "rhythm": [], "guitar": [], "etc": []}
        for track in song.tracks:
            if str(track).lower().find("drums") > -1 or str(track).lower().find("percussion") > -1 or \
                    track.program <= 0 or 9 <= track.program <= 16 or 113 <= track.program <= 120:
                groups["drums"].append(track)
                continue
            elif str(track).lower().find("bass") > -1 or 33 <= track.program <= 40:
                groups["bass"].append(track)
                continue
            elif str(track).lower().find("rhythm") > -1:
                groups["rhythm"].append(track)
                continue
            elif str(track).lower().find("guitar") > -1 or 25 <= track.program <= 32:
                groups["guitar"].append(track)
                continue
            else:
                groups["etc"].append(track)
                continue
        return groups

    def count_song_score(self):

        score = 0
        for instrument in self.groups.keys():
            coefficient = self.groups_coefficients[instrument]
            for track in self.groups[instrument]:
                ta = TrackTimeSignatureAnalyzer(track, self.bar_length, self.bonus_for_full_length,
                                                self.bonus_for_same_first_chords, self.bonus_for_max_velocity,
                                                self.bonus_for_both)
                score += ta.get_score() * coefficient
        return score

    def get_score(self):
        return self.score


class TimeSignatureClassifier:
    groups_coefficients = {"drums": 1.1, "bass": 1.0, "rhythm": 0.9, "guitar": 0.5, "etc": 0.3}
    bonus_for_full_length = 7
    bonus_for_same_first_chords = 15
    bonus_for_max_velocity = 20
    bonus_for_both = 50

    tested_time_signatures = {"3/4": 0.75, "4/4": 1.0}

    def __init__(self, song):
        self.song = song
        self.results = self.predict()

    def predict(self):

        results = defaultdict(float)
        for time_signature in self.tested_time_signatures.keys():
            analyzer = SongTimeSignatureAnalyzer(self.song, self.tested_time_signatures[time_signature],
                                                 self.bonus_for_full_length, self.bonus_for_same_first_chords,
                                                 self.bonus_for_max_velocity, self.bonus_for_both,
                                                 self.groups_coefficients)
            score = analyzer.get_score()
            results[time_signature] = score

        return results

    def print_result(self):
        max_score = 0
        max_time_signature = ""

        for time_signature in self.results.keys():
            if self.results[time_signature] > max_score:
                max_score = self.results[time_signature]
                max_time_signature = time_signature

        return f'Song: {self.song.name}, Time Signature: {max_time_signature}'

    def print_all_results(self):
        ret = f'Song: {self.song.name}, results: \n'
        for time_signature in self.results.keys():
            ret += f'Time Signature: {time_signature}, Score: {self.results[time_signature]}\n'
        return ret
