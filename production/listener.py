import sys
import time
import aubio
import numpy as np
import pyaudio
from time import sleep
from multiprocessing import Queue, Process, Value
from aubio import notes, onset, tempo
from production.structures import Note, Chord

"""
1 beat in bpm is 1/4 of musical beat
deadline is the time in seconds since the beginning of the era, float
"""

default_tempo = 124
max_time = sys.float_info.max

sample_rate = 44100
win_s = 1024
hop_s = win_s // 4
buffer_size = hop_s

alpha = 0.1


def from_ms_to_our_time(time, bpm):
    return int(time * (32 * bpm) / (60 * 1000))


def find_closest_onset_velocity(beat, onsets_velocity):
    minimum_difference = 100000
    closest_velocity = -1
    for local_onset, velocity in onsets_velocity:
        if beat - local_onset < minimum_difference:
            closest_velocity = velocity
            minimum_difference = beat - local_onset

    return closest_velocity


def run_queue_in(listener):
    stream = None
    if not listener.input_from_queue:
        p = pyaudio.PyAudio()
        # open stream
        pyaudio_format = pyaudio.paFloat32
        n_channels = 1
        stream = p.open(format=pyaudio_format,
                        channels=n_channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=buffer_size)
    '''
    s = aubio.source('/home/nikolay/pahanini.mp3', sample_rate, buffer_size)
    '''

    notes_o = notes("default", win_s, hop_s, sample_rate)
    onset_o = onset("default", win_s, hop_s, sample_rate)
    temp_o = tempo("specdiff", win_s, hop_s, sample_rate)
    last_onset = 0
    beats = []
    last_beat = 0
    count_beat = 0
    # last_downbeat = 0
    bar_start = False
    # the stream is read until you call stop
    prev_time = 0
    start_time = time.monotonic()

    # downbeat's structures' initialization
    latest_onsets_velocities = []
    i_onset = 0
    n_onset = 16
    for i in range(0, n_onset):
        latest_onsets_velocities.append((0.0, 0))

    beat_groups = np.zeros(4)
    group_means = np.zeros(4)

    downbeat_group = -1

    while listener.running.value:
        # read data from audio input
        if not listener.input_from_queue:
            audiobuffer = stream.read(buffer_size, exception_on_overflow=False)
            samples = np.fromstring(audiobuffer, dtype=np.float32)
        else:
            samples = listener.queue_in.get()
            if samples is None:
                break

        if onset_o(samples):
            last_onset = onset_o.get_last_ms()
        if temp_o(samples):
            tmp = temp_o.get_last_ms()
            beats.append(tmp - last_beat)
            count_beat = (count_beat + 1) % 4
            last_beat = tmp

            beat_groups[count_beat] = last_beat  # update last beat of the group
            beat_velocity = find_closest_onset_velocity(last_beat, latest_onsets_velocities)
            group_means[count_beat] = alpha * group_means[count_beat] + (1 - alpha) * beat_velocity  # update_mean

            downbeat_group = group_means.argmax()  # change the current downbeat_group
            # print(downbeat_group)
            if count_beat == downbeat_group:
                bar_start = True

            '''
            if (count_beat == 0):
                last_downbeat = last_beat
                bar_start = True
            '''

        new_note = notes_o(samples)
        if new_note[0] != 0:
            if len(beats) != 0:
                listener.set_tempo(60 * 1000.0 / np.median(beats))

            latest_onsets_velocities[i_onset] = (last_onset, int(new_note[1]))
            i_onset += 1
            if i_onset == n_onset:
                i_onset = 0

            chord = Chord([Note(int(new_note[0]))], from_ms_to_our_time(last_onset - prev_time, listener.tempo.value),
                          int(new_note[1]), bar_start)
            print(bar_start, listener.tempo.value, listener.deadline.value, time.monotonic())
            bar_start = False
            listener.queue_from_listener_to_predictor.put(chord)
            KOLYA_time = start_time - listener.web_delay + (beat_groups[downbeat_group] + (4 - count_beat) * 60 * 1000.0
                                                            / listener.tempo.value) / 1000.0
            # print(bar_start, listener.tempo.value, listener.deadline.value, time.monotonic(), KOLYA_time)
            # print(count_beat, time.monotonic(), KOLYA_time, listener.deadline.value)
            if count_beat != downbeat_group:
                listener.set_deadline(KOLYA_time)
            prev_time = last_onset


class Listener:
    def __init__(self, input_queue=None, queue_from_listener_to_predictor=None, running=Value('i', False),
                 tempo=Value('i', default_tempo),
                 deadline=Value('f', 0)):
        self.queue_in = input_queue
        self.queue_from_listener_to_predictor = queue_from_listener_to_predictor

        if input_queue is not None:
            self.input_from_queue = True
        else:
            self.input_from_queue = False

        self.web_delay = 0

        self.running = running
        self.tempo = tempo
        self.deadline = deadline

    def run(self):
        self.running.value = True
        self.process_queue_in = Process(target=run_queue_in, args=(self, ))
        self.process_queue_in.start()

    def stop(self):
        self.running.value = False
        self.queue_in.put_nowait(None)
        self.process_queue_in.join()
        self.queue_in = Queue()
        print("listener stopped")

    def get(self):
        if self.queue_in.empty() is False:
            return self.queue_in.get()

    def set_tempo(self, tempo=default_tempo):
        self.tempo.value = tempo

    def set_deadline(self, deadline=0):
        self.deadline.value = deadline

    def set_queue_in(self, queue):
        self.queue_in = queue
        self.input_from_queue = True

    def set_web_delay(self, delay):
        self.web_delay = delay

    queue_in = None
    running = None
    tempo = None
    deadline = None
    process_queue_in = None


if __name__ == '__main__':
    q = Listener()
    q.run()
    sleep(1)
    a = q.get()
    print(a)
    q.stop()
    print("Stopped")
