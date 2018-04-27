def interval(start, interval):
    return (start + interval)%12


def chord_notes(chord):
    natural_notes_numbers = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}
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
        return [first_note, interval(first_note, 3), interval(first_note, 7), interval(first_note, 10)]
    elif is_minor:
        return [first_note, interval(first_note, 3), interval(first_note, 7)]
    elif is_sept:  # мажорный септаккорд
        return [first_note, interval(first_note, 4), interval(first_note, 7), interval(first_note, 10)]
    elif is_sext:  # мажорный секстаккорд
        return [first_note, interval(first_note, 4), interval(first_note, 7), interval(first_note, 9)]
    else:  # major большая терция и чистая квинта
        return [first_note, interval(first_note, 4), interval(first_note, 7)]


def chords_dist_error(chord1, chord2):
    s = 0
    for i in range(len(chord1)):
        notes1 = sorted(chord_notes(chord1[i]))
        notes2 = sorted(chord_notes(chord2[i]))
        intersect = len(set(notes1) & set(notes2))
        s += min(len(notes1) - intersect, len(notes2) - intersect)
    return s/len(chord1)
