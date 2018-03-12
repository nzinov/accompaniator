import time
import mido
import rtmidi
import numpy as np 
import multiprocessing.dummy as multiprocessing

# ... data for test ...
# TODO: detect correctness of data
# TODO: what numbers mean in this library?
numbers = np.array([60, 60, 64, 67])
times = np.array([3, 3, 6, 9])
lengths = np.array([8, 4, 2, 1])

def correctnessofdata(numbers, times, lengths):
    if numbers.shape(0) != times.shape(0):
        return false
    if numbers.shape(0) != times.shape(0):
        return false
    return tru

def ceatingnotes(notes, times, lengths):
    return zip(numbers, times, lengths)

def playingnote(notenumber, notelength):
    note_on = mido.Message('note_on', channel=9, note=notenumber, velocity=112).bytes()
    note_off = mido.Message('note_off', channel=8, note=notenumber, velocity=0).bytes()
    midiout.send_message(note_on)
    time.sleep(notelength)
    midiout.send_message(note_off) 

def newevent(notenumber, notetime, notelength):
    process = multiprocessing.Process(target=playingnote, args=(notenumber, notelength, ))
    time.sleep(notetime)
    process.start()
    process.join()

if __name__ == "__main__":
    midiout = rtmidi.MidiOut()
    available_ports = midiout.get_ports()

    if available_ports:
        midiout.open_port(0)
    else:
        midiout.open_virtual_port("My virtual output")
    
    # TODO: changing instrument do not work?
    program_change = mido.Message('program_change', channel=10, program=5).bytes()
    midiout.send_message(program_change)
    
    queue = multiprocessing.Queue()
    pool = multiprocessing.Pool(numbers.shape[0])
    pool.starmap(newevent, ceatingnotes(numbers, times, lengths))
    
    del midiout
