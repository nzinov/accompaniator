import time
import mido
import numpy as np 
from mido import Message, MidiFile, MidiTrack

# ... data for test ...
# IMPORTANT time is measured in milliseconds
# TODO: detect correctness of data
numbers = np.array([60, 60, 64, 67])
times = np.array([3000, 3000, 6000, 9000])
lengths = np.array([8000, 4000, 2000, 1000])
delta = 10

if __name__ == "__main__":
    mid = MidiFile()
    tracks = []
    
    for i in range(numbers.shape[0]):
        tracks.append(MidiTrack())
        mid.tracks.append(tracks[i])
        
        tracks[i].append(Message('program_change', program=33, time=delta))
        tracks[i].append(Message('note_on', note=numbers[i], velocity=124, time=times[i]))
        tracks[i].append(Message('note_off', note=numbers[i], velocity=0, time=lengths[i])) 
    
    mid.save('tmp.mid')
