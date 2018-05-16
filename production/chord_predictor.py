import time
import numpy as np
import pandas as pd
from structures import Note, Chord
from multiprocessing import Queue, Process, Value

from keras.models import Sequential
from keras.layers import Embedding
from keras.layers import Merge
from keras.layers import LSTM
from keras.layers.core import Dense

defualt_predicted_len = 128
defualt_velocity = 100

prediction_time = 0.01


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
        return [first_note, interval(first_note, 3), interval(first_note, 7)]
    elif is_sept:  # мажорный септаккорд
        return [first_note, interval(first_note, 4), interval(first_note, 7),
                interval(first_note, 10)]
    elif is_sext:  # мажорный секстаккорд
        return [first_note, interval(first_note, 4), interval(first_note, 7),
                interval(first_note, 9)]
    else:  # major большая терция и чистая квинта
        return [first_note, interval(first_note, 4),
                interval(first_note, 7)]


def run_queue(predictor):
    predictor.load_model("NN_model")
    predictor.load_unique_chords("vocab.csv")

    while predictor.running.value:
        if not predictor.queue_in.empty():
            # print("predictor get")
            chord = predictor.try_predict()
            if chord is not None:
                predictor.queue_out.put(chord, defualt_predicted_len,
                                        defualt_velocity)
                # print("predictor put")


class ChordPredictor:
    model = None
    unique_chords = None

    def __init__(self, queue_in=Queue(), queue_out=Queue(),
                 deadline=Value('f', 0)):
        self.queue_in = queue_in
        self.queue_out = queue_out
        self.running = Value('i', False)
        self.chords_len = 0
        self.chords_count_before_4_4 = 0
        self.chords_len_before_4_4 = 0
        self.second_downbeat = False
        self.chords_list = []
        self.deadline = deadline
        self.prediction_for_beat = False
        self.current_chord_num = 0  # TODO

    def run(self):
        self.running.value = True
        self.process = Process(target=run_queue, args=(self, ))
        self.process.start()

    def stop(self):
        self.running.value = False
        self.process.join()

    def create_coded(self, X):
        return np.zeros(len(X))

    def encode(self, X, coded_X):
        for j, k in enumerate(X):
            for i, unique_chord in enumerate(self.unique_chords):
                if np.array_equal(k, unique_chord):
                    coded_X[j] = i

    def load_model(self, filename):
        model_chords = Sequential()
        model_notes = Sequential()

        model_chords.add(Embedding(10000, 20, input_length=1,
                                   batch_input_shape=(1, 1)))
        model_notes.add(Embedding(128, 20, input_length=1,
                                  batch_input_shape=(1, 1)))

        self.model = Sequential()
        merged = Merge([model_chords, model_notes])
        self.model.add(merged)
        self.model.add(LSTM(20, stateful=True))
        self.model.add(Dense(10000, activation='softmax'))

        self.model.load_weights("NN_model.h5")
        self.model.compile(optimizer='adam',
                           loss='sparse_categorical_crossentropy',
                           metrics=['accuracy'])

    def load_unique_chords(self, filename):
        self.unique_chords = pd.read_csv(filename)
        self.unique_chords = self.unique_chords.values.T[1:].T

    def make_suitable(self, notes_list):
        new_list = list(filter(lambda x: x != -1, notes_list))
        # TODO
        if len(new_list) == 1:
            note = new_list[0]
            new_list.extend([note + 4, note + 7, note + 12])  # major triad
        elif len(new_list) == 2:
            note1 = new_list[0]
            note2 = new_list[1]
            new_list.extend([note1 + 12, note2 + 12])
        elif len(new_list) == 3:
            note = new_list[0]
            if note + 12 < new_list[2]:
                new_list.append(note + 12)
            else:
                new_list.append(new_list[2] + 3)
        else:
            new_list = new_list[:4]
        return list(map(lambda x: Note(int(x)), new_list))

    def try_predict(self):
        notes = self.queue_in.get()
        print(notes.duration)
        # what TODO if more then one notes?
        note = notes.notes[0]
        self.current_chord_num = self.model.predict([
                                 np.array([self.current_chord_num]),
                                 np.array([note.number])],
                                                    batch_size=1,
                                                    verbose=1).argmax()
        if notes.downbeat:
            self.prediction_for_beat = False
        if (time.monotonic() > self.deadline.value - prediction_time and
                self.prediction_for_beat is False):
            chord_notes = self.unique_chords[self.current_chord_num]
            self.prediction_for_beat = True
            return Chord(self.make_suitable(chord_notes), 128, notes.velocity)
        return None
