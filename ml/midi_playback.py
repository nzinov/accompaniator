import time
import mido
import numpy as np 
from mido import Message, MidiFile, MidiTrack

# ... data for test ...
# TODO: detect correctness of data
numbers = np.array([60, 60, 64, 67])
times = np.array([3, 3, 6, 9])
lengths = np.array([8, 4, 2, 1])
delta = 10

if __name__ == "__main__":
    mid = MidiFile()
    tracks = []
    
    for i in range(numbers.shape[0]):
        tracks.append(MidiTrack())
        mid.tracks.append(tracks[i])
        
        tracks[i].append(Message('program_change', program=33, time=delta))
        tracks[i].append(Message('note_on', note=numbers[i], velocity=124, time=times[i] * 1000))
        tracks[i].append(Message('note_off', note=numbers[i], velocity=0, time=lengths[i] * 1000)) 
    
    mid.save('tmp.mid')
