from structures import *

def write_songs_to_file(songs, filename):
    # Записать объекты класса Song из массива songs в файл filename
    fout = open(filename, "w")
    for song in songs:
        print("SONG", song.bpm, song.name, file = fout)
        for instrument in song.instruments:
            print("INSTRUMENT", instrument.name, file = fout)
            for track in instrument.tracks:
                print("TRACK", file = fout)
                for chord in track.chords:
                    print("CHORD", velocity, duration, file = fout)
                    print(" ".join(map(str, chord.notes)), file = fout)
                print("ENDTRACK")
            print("ENDINSTRUMENT")
        print("ENDSONG")
    fout.close()
    return true

def read_songs_from_file(filename):
    #Прочитать песни из файла. Возвращает массив объектов класса Song
    songs = []
    fin = open(filename, "r")
    file_string = fin.readline()
    while file_string:
        string = file_string.split() + ["", ""]
        if string[0] == "SONG":
            instruments = []
            bpm = int(string[1])
            song_name = string[2]
        elif string[0] == "ENDSONG":
            songs.append(Song(instruments, bpm, song_name))
        elif string[0] == "INSTRUMENT":
            tracks = []
            instrument_name = string[1]
        elif string[0] == "ENDINSTRUMENT":
            instruments.append(Instrument(tracks, instrument_name))
        elif string[0] == "TRACK":
            chords = []
        elif string[0] == "ENDTRACK":
            tracks.append(Track(chords))
        elif string[0] == "CHORD":
            notes = list(map(int, fin.readline().split()))
            velocity = int(string[1])
            duration = int(string[2])
            chords.append(Chord(notes, velocity, duration))
        file_string = fin.readline()
    fin.close()
    return songs
