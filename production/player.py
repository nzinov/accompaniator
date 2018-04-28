import sys
import time
from multiprocessing.dummy import Queue, Process, Value
from time import sleep

from mido import Message, MidiFile, MidiTrack
from rtmidi import MidiOut
from ml.structures import Note, Chord

"""
1 beat in bpm is 1/4 of musical beat
distance_between_peaks is the time in seconds
deadline is the time in seconds since the beginning of the era, float
delay is needed to change deadline
"""

distance_between_peaks = 2
default_peak_time = 0.1
default_peak_number = 60
default_peak_velocity = 120
default_channel = 0
default_ultrasound_channel = 1
default_tempo = 124
default_instrument = 30
default_ultrasound_instrument = 48
min_velocity = 0
default_port = 0
delay = 0.000000001
sec_in_hour = 3600
max_time = sys.float_info.max
empty_chord = Chord([], 0, 0)


def len_in_s(duration, bpm):
    """ Returns length of chord in s given beats per minute"""
    return duration * 60 / (bpm * 32)


def run_peak(player):
    while (player.runing.value):
        sleep(distance_between_peaks)
        player.start.value = time.time()
        player.play_peak()


def run_queue_out(player):
    while (player.runing.value):
        sleeping_time = player.get_sleeping_time()
        if sleeping_time < sec_in_hour:
            if sleeping_time > 0:
                sleep(sleeping_time)
            if (not player.queue_out.empty()):
                player.play_chord()


class Player:
    def __init__(self, queue=Queue(), runing=Value('i', False),
                 tempo=Value('i', default_tempo),
                 deadline=Value('f', max_time)):
        self.midiout = MidiOut()
        self.midi_for_file = MidiFile()
        self.last_chord = empty_chord

        self.queue_out = queue
        self.runing = runing
        self.tempo = tempo
        self.deadline = deadline
        self.start = Value(float, max_time)

    def play_peak(self, number=default_peak_number,
                  velocity=default_peak_velocity):
        note_on = Message('note_on', note=number, velocity=velocity,
                          channel=default_ultrasound_channel).bytes()
        self.midiout.send_message(note_on)
        sleep(default_peak_time)
        note_off = Message('note_off', note=number, velocity=min_velocity,
                           channel=default_ultrasound_channel).bytes()
        self.midiout.send_message(note_off)

    def play_chord(self):

        chord = self.queue_out.get()

        if self.last_chord != empty_chord:
            for note in self.last_chord.notes:
                note_off = Message('note_off', note=note.number,
                                   velocity=min_velocity,
                                   channel=default_channel).bytes()
                self.midiout.send_message(note_off)

        for note in chord.notes:
            note_on = Message('note_on', note=note.number,
                              velocity=chord.velocity,
                              channel=default_channel).bytes()
            self.midiout.send_message(note_on)

        self.last_chord = chord

        if chord.duration > 0:
            sleep(len_in_s(chord.duration, self.tempo.value))

        if self.last_chord == chord:
            for note in chord.notes:
                note_off = Message('note_off', note=note.number,
                                   velocity=min_velocity,
                                   channel=default_channel).bytes()
                self.midiout.send_message(note_off)

    def put(self, chord):
        if type(chord) == Chord:
            self.queue_out.put(chord)
            return True
        return False

    def set_up_ports(self):
        """ This is necessary to HEAR the music """
        available_ports = self.midiout.get_ports()
        if available_ports:
            self.midiout.open_port(default_port)
        else:
            self.midiout.open_virtual_port("Tmp virtual output")

    def set_up_instrument(self, program=default_instrument):
        program_change = Message('program_change', program=program,
                                 channel=default_channel).bytes()
        self.midiout.send_message(program_change)

    def set_up_ultrasound_instrument(self,
                                     program=default_ultrasound_instrument):
        program_change = Message('program_change', program=program,
                                 channel=default_ultrasound_channel).bytes()
        self.midiout.send_message(program_change)

    def set_up_midi_for_file(self):
        self.midi_for_file.tracks.append(MidiTrack())

    def set_tempo(self, tempo=default_tempo):
        self.tempo.value = tempo

    def set_deadline(self, deadline=max_time):
        self.deadline.value = deadline

    def set_start(self, start=max_time):
        self.start.value = start

    def get_sleeping_time(self):
        return self.deadline.value - time.time()

    def get_track(self):
        return self.midi_for_file.tracks[0]

    def save_file(self, filename='my track.mid'):
        self.midi_for_file.save(filename)
        return filename

    def run(self):
        self.runing.value = True
        self.set_up_ports()
        self.set_up_midi_for_file()
        self.set_up_instrument()
        self.set_up_ultrasound_instrument()

        self.queue_process = Process(target=run_queue_out, args=(self,))
        self.queue_process.start()

        self.queue_process = Process(target=run_peak, args=(self,))
        self.queue_process.start()

    def stop(self):
        """ All chords that already sound will continue to sound """
        self.runing.value = False
        self.queue_process.join()
        self.queue_process.join()
        self.queue_out = Queue()

    queue_out = None
    runing = None
    tempo = None
    deadline = None
    start = None
    queue_process = None
    peak_process = None
    midiout = None
    midi_for_file = None
    last_chord = None


if __name__ == '__main__':
    q = Player()
    t = time.time()
    q.run()
    chord = Chord([Note(60), Note(64)], 512, 80)
    q.put(chord)
    chord = Chord([Note(76)], 4, 80)
    q.put(chord)
    q.set_deadline(t + 1)
    sleep(delay)
    q.set_deadline(t + 3.5)
    sleep(10)
    q.stop()
