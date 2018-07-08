package accompaniator_team.playwithme;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.os.SystemClock;
import android.support.annotation.Nullable;
import android.util.Log;

import org.billthefarmer.mididriver.MidiDriver;

import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.LinkedBlockingDeque;
import java.util.concurrent.LinkedBlockingQueue;

public class Player extends Service {
    private static final int DEFAULT_CHANNEL = 0;
    private static final String TAG = "Player";

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        Log.d(TAG, "onBind");
        queueOut = (LinkedBlockingQueue) intent.getSerializableExtra(QUEUE_NAME);
        return null;
    }

    public static class Note {
        int number;

        public Note(int number) {
            this.number = number;
        }
    }

    public static class Chord {
        Note[] notes;
        int velocity;
        int duration;

        public Chord(Note[] notes, int velocity, int duration) {
            this.notes = notes;
            this.velocity = velocity;
            this.duration = duration;
        }
    }

    public static final String QUEUE_NAME = "playQueue";
    LinkedBlockingQueue<Chord> queueOut;
    private Chord currentChord;
    private MidiDriver midiDriver;
    private int tempo;

    @Override
    public void onCreate() {
        Log.d(TAG, "onCreate");
        super.onCreate();
        midiDriver = new MidiDriver();

        while (true) {
            playChord();
        }
    }

    protected void onResume() {
        if (midiDriver != null)
            midiDriver.start();
    }

    protected void onPause() {
        if (midiDriver != null)
            midiDriver.stop();
    }

    @Override
    public void onDestroy() {
        if (midiDriver != null)
            midiDriver.stop();
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

    private float lenInSeconds(int duration, int tempo) {
        return duration * 60 / (tempo * 32);
    }

    public void playChord() {
        try {
            Chord chord = (Chord) queueOut.take();


            Assert.that(chord.duration > 0);
            Assert.that(chord.velocity < 128);
            for (Note note : chord.notes) {
                Assert.that(note.number < 128);
            }

            // Off notes of previous chord when next chord is playing
            if (currentChord != null) {
                for (Note note : currentChord.notes) {
                    sendMidi(0x80, note.number, chord.velocity);
                }
            }
            for (Note note : chord.notes) {
                sendMidi(0x90, note.number, chord.velocity);
            }

            currentChord = chord;

            float durationInSeconds = lenInSeconds(chord.duration, tempo);

            SystemClock.sleep(1000 * (int) durationInSeconds);

            // Off notes of chord after timeout.
            if (currentChord == chord) {
                for (Note note : currentChord.notes) {
                    sendMidi(0x80, note.number, chord.velocity);
                }
            }
        } catch (InterruptedException e) {
            Log.d(TAG, "", e);
        }
    }


    void playTestSound() {
        sendMidi(0xC0, 79);
        sendMidi(0x90, 48, 63);
        sendMidi(0x90, 52, 63);
        sendMidi(0x90, 55, 63);
        SystemClock.sleep(3000);
        sendMidi(0x80, 48, 0);
        sendMidi(0x80, 52, 0);
        sendMidi(0x80, 55, 0);
    }
}
