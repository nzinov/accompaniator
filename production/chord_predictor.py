from structures import *
import numpy as np
import pickle
import time
from multiprocessing.dummy import Queue, Process, Value

def chord_notes(chord):

    def interval(start, interval):             
        return (start + interval) % 12     

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

    if is_minor and is_sept: #major seventh chord
        return [first_note, interval(first_note, 3), interval(first_note, 7), interval(first_note, 10)]
    elif is_minor:
        return [first_note, interval(first_note, 3), interval(first_note, 7)]
    elif is_sept: #Ð¼Ð°Ð¶Ð¾Ñ€Ð½Ñ‹Ð¹ Ñ�ÐµÐ¿Ñ‚Ð°ÐºÐºÐ¾Ñ€Ð´
        return [first_note, interval(first_note, 4), interval(first_note, 7), interval(first_note, 10)]
    elif is_sext: #Ð¼Ð°Ð¶Ð¾Ñ€Ð½Ñ‹Ð¹ Ñ�ÐµÐºÑ�Ñ‚Ð°ÐºÐºÐ¾Ñ€Ð´
        return [first_note, interval(first_note, 4), interval(first_note, 7), interval(first_note, 9)]
    else: #major Ð±Ð¾Ð»ÑŒÑˆÐ°Ñ� Ñ‚ÐµÑ€Ñ†Ð¸Ñ� Ð¸ Ñ‡Ð¸Ñ�Ñ‚Ð°Ñ� ÐºÐ²Ð¸Ð½Ñ‚Ð°
        return [first_note, interval(first_note, 4), interval(first_note, 7)]

def run_queue(predictor):
    predictor.load_model("rf_nottingham.pkl")

    while predictor.running.value:
        if not predictor.queue_in.empty():
            chord = predictor.try_predict()
            if chord is not None:
                predictor.queue_out.put(chord) # Ð´Ð»Ð¸Ñ‚ÐµÐ»ÑŒÐ½Ð¾Ñ�Ñ‚ÑŒ Ð°ÐºÐºÐ¾Ñ€Ð´Ð° Ð²Ñ‹Ñ�Ñ‚Ð°Ð²Ð»Ñ�Ñ‚ÑŒ Ñ‚ÑƒÑ‚

class ChordPredictor:
    model = None

    def __init__(self, queue_in, queue_out):
        self.queue_in = queue_in
        self.queue_out = queue_out
        self.running = Value('i', False)
        self.chord_len = 0
        self.chords_list = []

    def run(self):
        self.running.value = True
        self.process = Process(target=run_queue, args=(self, ))
        self.process.start()

    def stop(self):
        self.running.value = False
        self.process.join()

    def load_model(self, filename):
        with open(filename, 'rb') as fid:
            self.model = pickle.load(fid)

    def try_predict(self):
        chord = self.queue_in.get() 
        self.chords_list.append(chord)
        self.chord_len += chord.duration
        if self.chord_len > 128 * 2 * 7/8:
            prediction = self.predict(self.chords_list)
            self.chords_list.clear()
            self.chord_len = 0
            return prediction
        else:
            return None


    def predict(self, chords_list): # Ð¿ÐµÑ€ÐµÐ´Ð°Ñ‘Ñ‚Ñ�Ñ� Ð´Ð²Ð° Ñ‚Ð°ÐºÑ‚Ð°, ÐºÑ€Ð¾Ð¼Ðµ Ð¿Ð¾Ñ�Ð»ÐµÐ´Ð½ÐµÐ¹ Ð´Ð¾Ð»Ð¸ (Ñ‚Ð¾ ÐµÑ�Ñ‚ÑŒ Ð¾Ñ‚ Ð´Ð²ÑƒÑ… Ñ‚Ð°ÐºÑ‚Ð¾Ð² Ð´Ð¾Ñ�Ñ‚ÑƒÐ¿Ð½Ð¾ 7/8 Ð¸Ð»Ð¸ 14/16 Ð¸Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ð¸Ð¸)
        numbers = np.array([]) # midi numbers!
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
            #print("Number of notes is wrong: " + str(numbers_size))
            if numbers.size < 28:
                numbers = np.hstack([numbers, np.zeros(28 - len(numbers)) + 12])
            else:
                numbers = numbers[:28]
        #Ñ�Ð½Ð°Ñ‡Ð°Ð»Ð° Ð½Ð¾Ð¼ÐµÑ€Ð°, Ð¿Ð¾Ñ‚Ð¾Ð¼ Ð±Ð¸Ñ‚Ñ‹
        chord = self.model.predict(np.hstack([numbers, beat]).reshape(1, -1))
        #print(chord)
        notes = chord_notes(chord[0])
        list_notes = []
        for note in notes:
            list_notes.append(Note(note + 12 * 4))
        return Chord(list_notes, 32, 100) 
