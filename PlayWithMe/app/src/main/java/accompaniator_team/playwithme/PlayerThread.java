package accompaniator_team.playwithme;

import android.content.Context;
import android.os.SystemClock;
import android.util.Log;

import org.billthefarmer.mididriver.MidiDriver;

import java.io.Serializable;
import java.util.concurrent.LinkedBlockingQueue;

public class PlayerThread extends Thread {
    private static final String TAG = "PlayerThread";

    private int tempo;
    private PlayerService.Chord currentChord;
    private MidiDriver midiDriver;
    private LinkedBlockingQueue<PlayerService.Chord> queueOut;
    private GuiLogger guiLog;

    PlayerThread(Context context, LinkedBlockingQueue<PlayerService.Chord> queueOut_, MidiDriver midiDriver_) {
        guiLog = new GuiLogger(context);
        tempo = 60;
        queueOut = queueOut_;
        midiDriver = midiDriver_;
        midiDriver.start();
        sendMidi(0xC0, 79);
    }

    private float lenInSeconds(int duration, int tempo) {
        return duration * 60 / (tempo * 32);
    }

    private void sendMidi(int m, int p) {
        byte msg[] = new byte[2];

        msg[0] = (byte) m;
        msg[1] = (byte) p;

        midiDriver.write(msg);
    }

    private void sendMidi(int m, int n, int v) {
        byte msg[] = new byte[3];

        msg[0] = (byte) m;
        msg[1] = (byte) n;
        msg[2] = (byte) v;

        midiDriver.write(msg);
    }

    private static int cnt = 0;

    private void playChord() {
        try {
            PlayerService.Chord chord = queueOut.take();

            Assert.that(chord.duration > 0);
            Assert.that(chord.velocity < 128);
            for (PlayerService.Note note : chord.notes) {
                Assert.that(note.number < 128);
            }

            // Off notes of previous chord when next chord is playing
            if (currentChord != null) {
                for (PlayerService.Note note : currentChord.notes) {
                    sendMidi(0x80, note.number, chord.velocity);
                }
            }
            for (PlayerService.Note note : chord.notes) {
                sendMidi(0x90, note.number, chord.velocity);
            }

            currentChord = chord;

            float durationInSeconds = lenInSeconds(chord.duration, tempo);

            SystemClock.sleep(500 * (int) durationInSeconds);

            // Off notes of chord after timeout.
            if (currentChord == chord) {
                for (PlayerService.Note note : currentChord.notes) {
                    sendMidi(0x80, note.number, chord.velocity);
                }
            }

            ++cnt;
            MainActivity.GuiMessage l = (Serializable & MainActivity.GuiMessage) (MainActivity a) -> {
                String message = String.format("%d Note %d played", cnt, chord.notes[0].number);
                a.soundText.setText(message);
            };
            guiLog.sendResult(l);
        } catch (InterruptedException e) {
            Log.e(TAG, "", e);
        }
    }

    private void playTestSound() {
        sendMidi(0xC0, 79);
        sendMidi(0x90, 48, 63);
        sendMidi(0x90, 52, 63);
        sendMidi(0x90, 55, 63);
        SystemClock.sleep(500);
        sendMidi(0x80, 48, 0);
        sendMidi(0x80, 52, 0);
        sendMidi(0x80, 55, 0);
        SystemClock.sleep(500);
    }

    public void run() {
        while (true) {
            playChord();
            //playTestSound();
        }
    }
}
