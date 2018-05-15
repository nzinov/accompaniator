import sys
import time
import numpy as np
from time import sleep

from mido import Message, MidiFile, MidiTrack
from rtmidi import MidiOut
from production.structures import Note, Chord
from multiprocessing import Queue, Process, Value
import production.pyfluidsynth as fluidsynth

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
default_instrument = 40
28
default_ultrasound_instrument = 2
min_velocity = 0
default_port = 1
delay = 0.000000001
sec_in_hour = 3600
max_time = sys.float_info.max
empty_chord = Chord([], 0, 0)

default_soundfont_path = "../soundfonts/piano_and_ultrasound.sf2"
sent_chunk_size_in_secs = 1.5
small_frame_time_in_secs = 0.1
output_rate = 44100  # in Hz


def len_in_s(duration, bpm):
    """ Returns length of chord in s given beats per minute"""
    return duration * 60 / (bpm * 32)


def send_output_queue_to_client(player):
    """ Goes through the audio output queue and sends chunks from it to the client via tornado WebSocketHandler"""
    chunk = np.array([])
    count = 0
    while player.running.value:
        small_chunk = player.real_queue_out.get()
        if count == 0:
            chunk = small_chunk
        else:
            chunk = np.concatenate([chunk, small_chunk])
        count += 1
        if count >= int(sent_chunk_size_in_secs / small_frame_time_in_secs):
            print(len(chunk))
            player.websocket.send_audio(chunk)
            count = 0
        # sleep(sent_chunk_size_in_secs)


def run_peak(player):
    while player.running.value:
        sleep(distance_between_peaks)
        player.start_peak.value = time.monotonic()
        # player.play_peak()


def run_queue_out(player):
    while player.running.value:
        if not player.queue_out.empty() and time.monotonic() > player.deadline.value:
            """ track is array of pairs: first is note number in chord, second is note len (duration) in 1/128.
                Sum of durations MUST be equal to 128 """
            player.play_chord_arpeggio(np.array([[0, 19], [1, 18], [2, 18], [3, 18], [2, 18], [1, 18], [0, 19]]))
        time.sleep(0.01)
    if player.last_note_number is not None:
        player.note_off(default_channel, player.last_note_number, )
        player.fluid_synth.noteoff(default_ultrasound_channel, player.last_note_number, min_velocity)


class Player:
    def __init__(self, queue=Queue(), running=Value('i', False),
                 tempo=Value('i', default_tempo),
                 deadline=Value('f', 0)):
        self.midiout = MidiOut()
        self.midi_for_file = MidiFile()
        self.last_chord = empty_chord

        self.websocket = None
        self.output_to_websocket = None

        self.fluid_synth = None
        self.real_queue_out = None
        self.fluid_synth = fluidsynth.Synth()
        sfid = self.fluid_synth.sfload(default_soundfont_path)
        self.fluid_synth.program_select(0, sfid, 0, 0)
        self.real_queue_out = Queue()

        """
        special ultrasound synth
        self.ultrasound_fluid_synth = fluidsynth.Synth()
        sfid = self.ultrasound_fluid_synth.sfload(default_soundfont_path)
        #TODO: check whether it works
        self.ultrasound_fluid_synth.program_select(0, sfid, 0, 1) #should be fine??
        """

        self.queue_out = queue
        self.running = running
        self.tempo = tempo
        self.deadline = deadline
        self.start_peak = Value('f', 0)
        self.start_chord = 0

    def play_peak(self, number=default_peak_number,
                  velocity=default_peak_velocity):
        self.note_on(default_ultrasound_channel, number, velocity)
        sleep(default_peak_time)
        self.note_off(default_ultrasound_channel, number, min_velocity)

    def play_chord_same_time(self):
        chord = self.queue_out.get()
        # print("player get", chord, "vel", chord.velocity, "queue", self.queue_out.qsize(), "time", time.monotonic())
        if chord.velocity > 127:
            chord.velocity = 127
        if chord.duration == 0:
            return
        for note in chord.notes:
            if note.number > 127:
                print("an incorrect note in player")
                return

        if self.last_chord != empty_chord:
            for note in self.last_chord.notes:
                self.note_off(default_channel, note.number, min_velocity)

        for note in chord.notes:
            self.note_on(default_channel, note.number, chord.velocity)

        self.last_chord = chord

        duration_in_secs = len_in_s(chord.duration, self.tempo.value)

        if self.output_to_websocket is True:
            for i in range((duration_in_secs / sent_chunk_size_in_secs) // 1):
                # put chunk of full size in the queue
                self.real_queue_out.put(self.fluid_synth.get_samples(int(output_rate * sent_chunk_size_in_secs)))
                duration_in_secs -= duration_in_secs

            if duration_in_secs > 0:
                # put chunk of leftovers in the queue
                self.real_queue_out.put(self.fluid_synth.get_samples(int(output_rate * duration_in_secs)))

        sleep(duration_in_secs)  # not sure if that's needed?

        if self.last_chord == chord:
            for note in chord.notes:
                self.note_off(default_channel, note.number, min_velocity)

    def play_chord_arpeggio(self, track=np.array([])):
        chord = self.queue_out.get()
        # print("player get", chord, "vel", chord.velocity, "queue", self.queue_out.qsize(), "time", time.monotonic())
        if chord.velocity > 127:
            chord.velocity = 127
        if chord.duration == 0:
            return
        for note in chord.notes:
            if note.number > 127:
                print("an incorrect note in player")
                return
        chord.notes = sorted(chord.notes)
        if len(chord.notes) == 3:
            chord.notes.append(Note(chord.notes[0].number + 12))
        if track == np.array([]):
            notes_numbers = np.arange(len(chord.notes))
            notes_durations = np.array([int(128 / len(chord.notes)) for i in range(len(chord.notes))])
            track = np.column_stack((notes_numbers, notes_durations))

        notes_sum_durations = np.cumsum(track.transpose(), axis=1)[1]

        if self.last_note_number is not None:
            self.note_off(default_channel, self.last_note_number, min_velocity)

        self.start_chord = time.monotonic()
        pair = 0
        note_number = track[pair][0]
        self.note_on(default_channel, chord.notes[note_number].number, chord.velocity)

        while pair < len(track) - 1:
            # TODO
            if time.monotonic() > self.start_chord + max((self.deadline.value - self.start_chord) *
                                                         notes_sum_durations[pair] /
                                                         notes_sum_durations[-1],
                                                         len_in_s(notes_sum_durations[pair],
                                                         self.tempo.value)):
                self.note_off(default_channel, chord.notes[note_number].number, min_velocity)
                pair += 1
                note_number = track[pair][0]
                self.note_on(default_channel, chord.notes[note_number].number, chord.velocity)

                self.last_note_number = chord.notes[note_number].number

            if self.output_to_websocket is True:
                self.real_queue_out.put(self.fluid_synth.get_samples(int(output_rate * small_frame_time_in_secs)))
            time.sleep(small_frame_time_in_secs)

    def note_on(self, channel, note, velocity):
        if self.output_to_websocket is True:
            self.fluid_synth.noteon(channel, note, velocity)

        else:
            note_on = Message('note_on', note=note, velocity=velocity, channel=channel).bytes()
            self.midiout.send_message(note_on)

    def note_off(self, channel, note, velocity):
        if self.output_to_websocket is True:
            self.fluid_synth.noteoff(channel, note)

        else:
            note_off = Message('note_off', note=note, velocity=velocity, channel=channel).bytes()
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

    def set_deadline(self, deadline=0):
        self.deadline.value = deadline

    def set_start_peak(self, start=max_time):
        self.start_peak.value = start

    def get_sleeping_time(self):
        return self.deadline.value - time.monotonic()

    def get_track(self):
        return self.midi_for_file.tracks[0]

    def save_file(self, filename='my track.mid'):
        self.midi_for_file.save(filename)
        return filename

    def set_websocket(self, websocket):
        self.websocket = websocket
        self.output_to_websocket = True
        self.real_queue_out = Queue()

    def run(self):
        self.running.value = True
        if not self.output_to_websocket:
            self.set_up_ports()
            self.set_up_midi_for_file()
            self.set_up_instrument()
        # self.set_up_ultrasound_instrument()

        self.queue_process = Process(target=run_queue_out, args=(self,))
        self.queue_process.start()

        self.queue_process = Process(target=run_peak, args=(self,))
        self.queue_process.start()

        self.queue_process = Process(target=send_output_queue_to_client, args=(self,))
        self.queue_process.start()

    def stop(self):
        """ All chords that already sound will continue to sound """
        self.running.value = False
        self.queue_process.join()
        self.queue_process.join()
        self.queue_out = Queue()

    queue_out = None
    running = None
    tempo = None
    deadline = None
    start_peak = None
    start_chord = None
    queue_process = None
    peak_process = None
    midiout = None
    midi_for_file = None
    last_chord = None
    last_note_number = None


if __name__ == '__main__':
    q = Player()
    t = time.monotonic()
    q.run()
    chord = Chord([Note(60), Note(64), Note(67)], 512, 120)
    q.put(chord)
    # chord = Chord([Note(76)], 4, 80)
    # q.put(chord)
    q.set_deadline(t)
    sleep(10)
    q.stop()
