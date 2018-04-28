from ml.structures import *


def chord_notes(chord):
    def interval(start, interval):
        return (start + interval) % 12

    natural_notes_numbers = {'c': 0, 'd': 2, 'e': 4, 'f': 5,
                             'g': 7, 'a': 9, 'b': 11}
    note = chord[0]
    first_note = natural_notes_numbers[note]

    is_sharp = chord.find('#') != -1
    is_flat = chord[1:].find('b') != -1
    is_minor = chord.find('m') != -1
    is_sept = chord.find('7') != -1
    is_sext = chord.find('6') != -1

    if is_sharp:
        first_note += 1
    elif is_flat:
        first_note -= 1

    if is_minor and is_sept:  # минорный септаккорд
        return [first_note, interval(first_note, 3), interval(first_note, 7),
                interval(first_note, 10)]
    elif is_minor:
        return [first_note, interval(first_note, 3),
                interval(first_note, 7)]
    elif is_sept:  # мажорный септаккорд
        return [first_note, interval(first_note, 4), interval(first_note, 7),
                interval(first_note, 10)]
    elif is_sext:  # мажорный секстаккорд
        return [first_note, interval(first_note, 4), interval(first_note, 7),
                interval(first_note, 9)]
    else:  # major большая терция и чистая квинта
        return [first_note, interval(first_note, 4),
                interval(first_note, 7)]


class ChordPredictor:
    model = None

    def __init__(self):
        pass

    def load_model(self, filename):
        with open(filename, 'rb') as fid:
            self.model = pickle.load(fid)

    def predict(self,
                chords_list):
        # передаётся два такта, кроме последней доли (то есть от двух тактов доступно 7/8 или 14/16 информации)
        numbers = np.array([])  # midi numbers!
        for chord in chords_list:
            num_notes_to_add = round(chord.len() / 8)
            note = chord.notes[0]
            for i in range(num_notes_to_add):
                numbers = np.append(numbers, note.number)
        # shift midi notes to our notes
        numbers = numbers % 12
        # generate beat
        beat = np.hstack([np.ones(4), np.zeros(12), np.ones(4), np.ones(8)])
        if numbers.size != 28:
            print("Number of notes is wrong: " + str(numbers_size))
            if numbers.size < 28:
                numbers = np.hstack([numbers,
                                     np.zeros(28 - len(numbers)) + 12])
            else:
                numbers = numbers[:28]
        # сначала номера, потом биты
        chord = self.model.predict(np.hstack([numbers, beat]).reshape(1, -1))
        # print(chord)
        notes = chord_notes(chord[0])
        list_notes = []
        for note in notes:
            list_notes.append(Note(note + 12 * 4))
        return Chord(list_notes, 128, 1)
