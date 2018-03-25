import numpy as np

natural_notes_numbers = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}

def simplify_chord(ch):
    if ch[0] == '(':
        ch = ch[1:]
    if ch[-1] == ')':
        ch = ch[:-1]
    return ch.split("/")[0]

def cut_song(song): #3 arrays: notes, chords, beat
    notes = np.array(song[0])
    chords = np.array([simplify_chord(ch) for ch in song[1]])
    beat = np.array(song[2])
    n = len(song[0])
    n_items = len(song[0]) // 8 - 1
    X_notes = notes[:n_items * 8].reshape((n_items, 8))
    X_chords = chords[:n_items * 8].reshape((n_items, 8))
    X_beat = beat[:n_items * 8].reshape((n_items, 8))
    X = np.hstack([X_notes, X_chords, X_beat])
    y = np.array([chords[8 * (i + 2) - 1] for i in range(n_items)])
    return X, y

def get_notes_numbers(key):
    notes_numbers = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11, 'z': 12}
    flat_order = 'beadgcf'
    sharp_order = list(reversed(flat_order))
    flat_keys_shift = ['C', 'F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb', 'Cb']
    sharp_keys_shift = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#'] 
    minor_keys = {'Em': 'G', 'Am': 'C', 'Dm': 'F', 'Bm': 'D', 'Gm': 'Bb', 'Cm': 'Eb'}

    if key in minor_keys.keys():
        key = minor_keys[key]

    if key in flat_keys_shift:
        shift = flat_keys_shift.index(key)
        for i in range(shift):
            notes_numbers[flat_order[i]] -= 1
    elif key in sharp_keys_shift:
        shift = sharp_keys_shift.index(key)
        for i in range(shift):
            notes_numbers[sharp_order[i]] += 1
    else:
        raise ValueError("unknown key: " + key)
    return notes_numbers
 

def prepare(piece, key): #если циферка до слэша, это числитель, если после -- знаменатель
    notes_numbers = get_notes_numbers(key)
    res_notes = []
    res_chords = []
    notes_and_chords = piece.split('"')
    #print(notes_and_chords)
    chords = notes_and_chords[1::2]
    if len(chords) > 8:
        chords = chords[:8]
    elif len(chords) < 8:
        pass
    notes = notes_and_chords[::2]
    #print(chords)
    #print(notes)
    if notes[0] == '':
        notes = notes[1:]
    for n, c in zip(notes, chords):
        next_mod = 0
        l = 1/4
        cnt = 0
        sl = False
        up = 1
        down = 1
        first_note = True
        next_note = None
        ch_l = len(res_chords)
        for char in n+'a':
            if char == '=':
                next_mod = 0
            elif char == '_':
                next_mod -= 1
            elif char == '^':
                next_mod += 1
            elif 'a' <= char <= 'g':
                #print("SEE CHAR " + char) 
                num_notes_to_add = int((up / down * l) / (1/4))
                #print("MULTIPLIER FOR PREV NOTE " + str(num_notes_to_add))
                if not first_note:
                    for o in range(num_notes_to_add):
                        res_notes.append(next_note)
                next_note = notes_numbers[char] + next_mod
                next_mod = 0 # incorrect a bit
                up = 1
                down = 1
                cnt += num_notes_to_add * int(first_note)
                if first_note:
                    first_note = False
 
            elif '1' <= char <= '9':
                if sl:
                    down = int(char)
                else:
                    up = int(char)
            elif char == '/':
                sl = True
        res_chords += [c] * (len(res_notes) - ch_l)
    return res_notes, res_chords

fnames = ['jigs.abc', 'ashover.abc', 'hpps.abc', 'morris.abc', 'playford.abc', 'reelsa-c.abc', 'reelsd-g.abc', 'reelsh-l.abc', 'reelsm-q.abc', 'reelsr-t.abc', 'reelsu-z.abc', 'slip.abc', 'waltzes.abc', 'xmas.abc']

songs = []

for fname in fnames:
    flines = open(fname).readlines()

    current_key = 'C'
    current_meter = None
    current_pitches = np.zeros(8)
    current_song = [[], [], []]
    for l in flines:
        l = l.strip()
        if len(l) == 0:
            continue
        if l[0] == 'X':
            songs.append(current_song)
            current_song = [[], [], []]
        elif l[0] == 'K':
            current_key = l.split(":")[1]
        elif l[0] == 'M':
            current_meter = l.split(":")[1]
        elif l[0] not in ['X', 'T', '%', 'S', 'M', 'L', 'K', 'Q', 'P', 'Y', 'N', '\n']:
            line = list(filter(None, l.replace(':', "").replace('\\\\', '').lower().split("|")))
            prepared = [prepare(piece, current_key) for piece in line]
            for tact in prepared:
                current_song[0] += tact[0]
                current_song[1] += tact[1]
                current_song[2] += [1] + [0] * (len(tact[0]) - 1)

songs = songs[1:]
X, y = cut_song(songs[0])
for song in songs[1:]:
    if len(song[0]) > 16:
        X_, y_ = cut_song(song)
        X = np.vstack([X, X_])
        y = np.hstack([y, y_])
print(X, y)
print(X.shape, y.shape)
np.save("X.npy", X) 
np.save("y.npy", y)
