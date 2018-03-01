from ml.structures import *


def find_entries(main_chords, sub_chords):
    """
    Finds entries of sub_chords in main_chords.

    Parameteres
    -----------
        main_chords: a list of Chord objects to find entries in.

        sub_chords: a smaller list of Chord objects.

    Returns
    -------
        entries: a list of tuples (start, end), where
        start is the starting point of an entry(included) and
        end is the end of the entry(not included).
    """
    entries = []
    for i in range(len(main_chords)):
        is_equal = 1
        j = 0
        for main_chord, sub_chord in zip(main_chords[i: i + len(sub_chords)], sub_chords):
            if str(main_chord) != str(sub_chord):
                is_equal = 0
                break
            j += 1
        if is_equal and j == len(sub_chords):
            entries.append((i, i + j))
            i += len(sub_chords)
    return entries


def get_check_chords(chords, bar_length):
    """
    Finds a Chord  sequence of given length.

    Parameteres
    -----------
        chords: a list of Chords to find a continuing
        Chord sequence in.

        bar_length: the musical length of needed Chord
        sequence(in 1/128ths).

    Returns
    -------
        check_chords: a list of Chord objects of given musical length.
    """
    bar_sum = 0
    check_chords = []
    for chord in chords:
        bar_sum += chord.duration
        check_chords.append(chord)
        if bar_sum == bar_length:
            break
        elif bar_sum > bar_length:
            check_chords = None
            break
    return check_chords


def check_time_signature(track, bar_length):
    """
    Gets the number of repeats of different Chord sequences
    of certain length.

    Parameters
    ----------
        track: the Track object to check.

        bar_length: the musical length of all Chord sequences
        in question.

    Returns
    -------
        num_of_appearances: the number of repeats.
    """
    bar_length = bar_length * 128
    num_of_appearances = 0
    i = 0
    while i < len(track.chords):
        check_chords = get_check_chords(track.chords[i:], bar_length)
        if check_chords == None:
            i += 1
            continue
        entries = find_entries(track.chords, check_chords)
        num_of_appearances += len(entries) - 1  # substract 1 because the
        # find_entries function will count the check_chords too.
        i += len(check_chords)
    return num_of_appearances


def find_time_signature(track):
    """
    CAUTION, WILL MOST CERTAINLY WORK NOT CORRECTLY(at this time).
    Gets the time signature of the track.

    Parameters
    ----------
        track: a track object to find time signature of.

    Returns
    -------
        output: string with the time signature.
    """
    whole = 1.0
    waltz = 3 / 4
    if check_time_signature(track, whole) > 0:
        return "4/4"
    if check_time_signature(track, waltz) > 0:
        return "3/4"


"""

EXAMPLES BELOW

"""

tmp_chords_whole = [[16, 0, [1, 2, 3]], [16, 0, [4, 5, 6]], [8, 0, [2, 3]],
                         [8, 0, [2, 3]], [16, 0, [1, 2, 3]], [32, 0, [10, 11, 12]],
                         [16, 0, [1, 2, 3]], [16, 0, [4, 5, 6]], [32, 0, [14, 15, 16]],
                         [32, 0, [17, 18, 19]], [32, 0, [20, 21, 22]], [32, 0, [23, 24, 25]],
                         [16, 0, [1, 2, 3]], [16, 0, [4, 5, 6]], [8, 0, [2, 3]],
                         [8, 0, [2, 3]], [16, 0, [1, 2, 3]], [32, 0, [10, 11, 12]],
                         [16, 0, [1, 2, 3]], [16, 0, [4, 5, 6]]]
tmp_sub = [[16, 0, [1, 2, 3]], [16, 0, [4, 5, 6]]]

chords_whole = []
for x in tmp_chords_whole:
    chord = Chord(x[2], x[0], x[1])
    chords_whole.append(chord)

sub = []
for x in tmp_sub:
    chord = Chord(x[2], x[0], x[1])
    sub.append(chord)

entries = find_entries(chords_whole, sub)

for entry in entries:
    print(entry)

hard_track_whole = Track(chords_whole, 'Vocals')
print(f'time signature: {find_time_signature(hard_track_whole)}')
