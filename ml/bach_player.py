from structures import *
from player import *


if __name__ == '__main__':
    q = Player(240000000)
    q.run()
    song = Song()
    song.load("bach")
    for chord in song.tracks[0].chords:
        q.put(chord)
        sleep(1)
    q.stop()
