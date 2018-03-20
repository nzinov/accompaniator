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


def get_score_by_notes(chord_a_notes, chord_b_notes, bonus_for_matching_notes):
    score = 0
    full_equality = True
    for note_a in chord_a_notes:
        found_equal_for_note_a = False
        for note_b in chord_b_notes:
            if note_a == note_b:
                score += bonus_for_matching_notes
                found_equal_for_note_a = True
                break  # in case there're lots of same notes in the chord
        full_equality = full_equality and found_equal_for_note_a
    return score, full_equality


class Bar:
    def __init__(self, bar_chords, duration, continued_long_note=False):
        self.bar_chords = bar_chords
        self.continued_long_note = continued_long_note
        self.duration = duration
        self.max_velocity = self.find_max_velocity()
        self.first_chord = bar_chords[0]

    def len(self):
        return self.duration

    def find_max_velocity(self):
        max_velocity = 0
        for chord in self.bar_chords:
            if chord.velocity > max_velocity:
                max_velocity = chord.velocity
        return max_velocity

    def get_main_notes_of_first_chord(self):
        notes = []
        for note in self.first_chord.notes:
            notes.append(note.number % 12)
        return notes

    def get_duration_of_first_chord(self):
        return self.first_chord.duration


class TrackTimeSignatureAnalyzer:

    def __init__(self, bars, bar_length, bonuses):
        # self.indent = indent
        self.bar_length = bar_length
        # self.indent = indent
        self.bonuses = bonuses
        # self.cut_chords_by_indent()
        self.bars = bars
        self.score = self.count_track_score()

    def get_score(self):
        return self.score / len(self.bars)

    def print_bars(self):
        i = 0
        for bar in self.bars:
            print(f'bar #{i}, continued: {bar.continued_long_note}, velocity: {bar.max_velocity}')
            for chord in bar.bar_chords:
                print(str(chord))
            i += 1

    def count_track_score(self):
        previous_bar = self.bars[0]
        score = 0
        for bar in self.bars[1:]:
            if not bar.continued_long_note:
                score_for_notes, full_equality = get_score_by_notes(bar.get_main_notes_of_first_chord(),
                                                                    previous_bar.get_main_notes_of_first_chord(),
                                                                    self.bonuses["bonus_for_matching_notes"])
                score += score_for_notes
                if full_equality is True and bar.first_chord.velocity == bar.max_velocity:
                    score += self.bonuses["bonus_for_both"]

                if bar.first_chord.velocity == bar.max_velocity:
                    score += self.bonuses["bonus_for_max_velocity"]
                    previous_bar = bar
        return score


class SongTimeSignatureAnalyzer:
    def __init__(self, song, time_signature_guess, groups_coefficients, bonuses):
        self.song = song
        self.bar_length = int(128 * time_signature_guess)
        self.bonuses = bonuses
        self.groups_coefficients = groups_coefficients
        self.full_length_count = 0
        self.groups = self.divide_tracks_on_groups(song)
        self.score = self.count_song_score()
        self.score += self.find_simultaneous_max_velocity_score()

    def devide_track_by_bars(self, track):
        bars = []
        bar_sum = 0
        bar_chords = []
        for chord in track.chords:
            if chord.duration > (self.bar_length - bar_sum):
                duration = chord.duration
                if bar_sum > 0:
                    new_chord = Chord(chord.notes, self.bar_length - bar_sum, chord.velocity)
                    bar_chords.append(new_chord)
                    bar = Bar(bar_chords, self.bar_length)
                    bars.append(bar)
                    bar_chords = []
                    bar_sum = 0
                    duration -= (self.bar_length - bar_sum)
                while duration != 0:
                    if duration > self.bar_length:
                        new_chord = Chord(chord.notes, self.bar_length, chord.velocity)
                        bar_chords.append(new_chord)
                        bar = Bar(bar_chords, self.bar_length, True)
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
                bar = Bar(bar_chords, self.bar_length)
                bars.append(bar)
                bar_chords = []
                bar_sum = 0
        if bar_sum > 0:
            bar = Bar(bar_chords, bar_sum)
            bars.append(bar)
        else:
            self.full_length_count += 1
        return bars

    def divide_tracks_on_groups(self, song):
        groups = {"drums": [], "bass": [], "rhythm": [], "guitar": [], "etc": []}
        for track in song.tracks:
            if str(track).lower().find("drums") > -1 or str(track).lower().find("percussion") > -1 or \
                    track.program <= 0 or 9 <= track.program <= 16 or 113 <= track.program <= 120:
                groups["drums"].append(self.devide_track_by_bars(track))
                continue
            elif str(track).lower().find("bass") > -1 or 33 <= track.program <= 40:
                groups["bass"].append(self.devide_track_by_bars(track))
                continue
            elif str(track).lower().find("rhythm") > -1:
                groups["rhythm"].append(self.devide_track_by_bars(track))
                continue
            elif str(track).lower().find("guitar") > -1 or 25 <= track.program <= 32:
                groups["guitar"].append(self.devide_track_by_bars(track))
                continue
            else:
                groups["etc"].append(self.devide_track_by_bars(track))
                continue
        return groups

    def find_simultaneous_max_velocity_score(self):
        max_bars_len = 0
        for instrument in self.groups.keys():
            for track_bars in self.groups[instrument]:
                if len(track_bars) > max_bars_len:
                    max_bars_len = len(track_bars)

        score_addition = 0
        for i in range(max_bars_len):
            number_of_tracks_with_max_velocity = 0
            number_of_tracks_playing_for_i = 0
            for instrument in self.groups.keys():
                for track_bars in self.groups[instrument]:
                    if i < len(track_bars):
                        bar = track_bars[i]
                        if bar.first_chord.velocity != 0 and len(bar.first_chord.notes) != 0:
                            number_of_tracks_playing_for_i += 1
                            if bar.first_chord.velocity == bar.find_max_velocity():
                                number_of_tracks_with_max_velocity += 1
            if number_of_tracks_with_max_velocity > 0:
                number_of_tracks_with_max_velocity -= 1  # why simultaneous bonus if it's just one track's chord
                # that's strong
                score_addition += number_of_tracks_with_max_velocity / number_of_tracks_playing_for_i * self.bonuses[
                    "bonus_for_simultaneous_strong_accents"]
        return score_addition / max_bars_len

    def count_song_score(self):
        score = 0
        for instrument in self.groups.keys():
            track_coefficient = self.groups_coefficients[instrument]
            for track_bars in self.groups[instrument]:
                ta = TrackTimeSignatureAnalyzer(track_bars, self.bar_length, self.bonuses)
                score += ta.get_score() * track_coefficient

        score += self.full_length_count * self.bonuses["bonus_for_full_length"]
        return score

    def get_score(self):
        return self.score


class TimeSignatureClassifier:
    tested_time_signatures = {"3/4": 0.75, "4/4": 1.0}
    """
    groups_coefficients = {"drums": 1.1, "bass": 1.0, "rhythm": 0.9, "guitar": 0.5, "etc": 0.3}
    bonuses = {"bonus_for_full_length": 10, "bonus_for_matching_notes": 15, "bonus_for_max_velocity": 50,
               "bonus_for_both": 100, "bonus_for_simultaneous_strong_accents": 75}
    """

    def __init__(self, song, groups_coefficients, bonuses):
        self.song = song
        self.groups_coefficients = groups_coefficients
        self.bonuses = bonuses
        self.results = self.get_results()

    def get_results(self):

        results = defaultdict(float)
        for time_signature in self.tested_time_signatures.keys():
            analyzer = SongTimeSignatureAnalyzer(self.song, self.tested_time_signatures[time_signature],
                                                 self.groups_coefficients, self.bonuses)
            score = analyzer.get_score()
            results[time_signature] = score

        return results

    def predict(self):
        max_score = 0
        max_time_signature = ""

        for time_signature in self.results.keys():
            if self.results[time_signature] > max_score:
                max_score = self.results[time_signature]
                max_time_signature = time_signature

        # return f'Song: {self.song.name}, Time Signature: {max_time_signature}'
        return max_time_signature

    def print_all_results(self):
        ret = f'Song: {self.song.name}, results: \n'
        for time_signature in self.results.keys():
            ret += f'Time Signature: {time_signature}, Score: {self.results[time_signature]}\n'
        return ret


class TimeClassifierWrapper:

    def __init__(self, songs, targets, parameters):
        self.songs = songs
        self.targets = targets
        self.groups_coefficients = defaultdict(float)
        self.bonuses = defaultdict(float)
        self.get_parameters(parameters)

    def score(self):
        correct = 0
        for song, target in zip(self.songs, self.targets):
            tsc = TimeSignatureClassifier(song, self.groups_coefficients, self.bonuses)
            prediction = tsc.predict()
            if prediction == target:
                correct += 1
        return correct / len(self.targets)

    def get_parameters(self, parameters):
        self.groups_coefficients["drums"] = parameters[0]
        self.groups_coefficients["bass"] = parameters[1]
        self.groups_coefficients["rhythm"] = parameters[2]
        self.groups_coefficients["guitar"] = parameters[3]
        self.groups_coefficients["etc"] = parameters[4]
        self.bonuses["bonus_for_full_length"] = parameters[5]
        self.bonuses["bonus_for_matching_notes"] = parameters[6]
        self.bonuses["bonus_for_max_velocity"] = parameters[7]
        self.bonuses["bonus_for_both"] = parameters[8]
        self.bonuses["bonus_for_simultaneous_strong_accents"] = parameters[9]


class ClassifierTrainer:

    def __init__(self, songs, targets):
        self.songs = songs
        self.targets = targets

    def train_classifier(self, parameters):
        tsw = TimeClassifierWrapper(self.songs, self.targets, parameters)
        return 1 - tsw.score()


"""
TRAINING EXAMPLE BELOW

CT = ClassifierTrainer(sc.songs, targets)
res = minimize(CT.trainClassifier, parameters0, method='Nelder-Mead', options={'disp': True})
print(res.x)

"""
