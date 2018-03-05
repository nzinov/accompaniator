package com.example.anna.innpracktest;

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.SparseArray;
import android.widget.Button;
import android.widget.TextView;
import android.os.CountDownTimer;
import android.util.Log;
import android.view.View;

import org.billthefarmer.mididriver.MidiDriver;

public class MainActivity extends AppCompatActivity implements MidiDriver.OnMidiStartListener,
        View.OnClickListener {

    private static final String GLOBALCOUNTER = "global counter";
    private static final String LOCALCOUNTER = "local counter";
    private static final String NOTES = "queue of notes";
    private static final String TIMES = "times for notes";
    private static final String LENGTHS = "lengths of notes";
    private static final String POINTER = "current note for playing";
    // Initialized by zero according to documentation.
    private long[] counterForLocal;
    private long counterForGlobal = Long.MAX_VALUE;
    private SparseArray<CountDownTimer> localTimers;
    private MidiDriver midiDriver;
    private byte[] startEvent;
    private byte[] finishEvent;
    private byte[] instrumentEvent = {(byte) (0xC0 | 0x00), (byte) 0x30};
    // The end of track
    public static byte[] endEvent = {(byte) (0xFF), (byte) 0x2F, (byte) 0x00};
    private int[] config;
    private Button buttonPlaySong;
    private CountDownTimer globalTimer = null;
    private byte [][][] Events = {{endEvent}};
    private long[] times;
    private long[] lengths;
    private int pointer = 0;
    //TODO
    private long DIFFERENCE = 10;
    ////////////
    public final static int MAXNOTESINTACT = 10;
    /////////////////////
    //delete
    private TextView mText;
    QueueOfNotes queue;

    private CountDownTimer initLocalTimer(long counter, final Integer pointerToClock, final QueueOfNotes gueue){
        Log.e("LOCAL_TIMER", "Starting local timer");
        CountDownTimer tmpTimer = new CountDownTimer(counter, 1) {

            @Override
            public void onTick(long millisUntilFinished) {
                counterForLocal[pointerToClock] = millisUntilFinished;
            }

            @Override
            public void onFinish() {
                Log.e("LOCAL_TIMER", "Finishing local timer");
                midiDriver.write(gueue.getFinish(pointerToClock));
                localTimers.delete(pointerToClock);
            };
        };
        return tmpTimer;
    }

    private void initGlobalTimer(long counter, final QueueOfNotes queue, final long[] Times, final long[] Lenghts) {
        ///////////////////////////
        //What distance should I add?
        //to be synchronized with clock it's important
        // but to have a longer period is important too

        Log.e("GLOBAL_TIMER", "starting global timer");
        globalTimer = new CountDownTimer(counter, 1) {
            @Override
            public void onTick(long millisUntilFinished) {
                counterForGlobal = millisUntilFinished;
                searchForNotes(queue, Times, Lenghts, Long.MAX_VALUE - counterForGlobal);

                ////////////////////
                //delete
                mText.setText(Long.toString(Long.MAX_VALUE - counterForGlobal) + "_" + Integer.toString(pointer));
            }

            @Override
            public void onFinish() {
                Log.e("GLOBAL_TIMER", "Finising global timer");
            };
        };
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Log.e("MAIN_ACTIVITY", "Creating activity");
        setContentView(R.layout.activity_main);

        buttonPlaySong = (Button)findViewById(R.id.buttonPlaySong);
        buttonPlaySong.setOnClickListener(this);

        midiDriver = new MidiDriver();
        midiDriver.setOnMidiStartListener(this);

        localTimers = new SparseArray<CountDownTimer>();

        if (savedInstanceState != null) {
            counterForGlobal = savedInstanceState.getLong(GLOBALCOUNTER);
            counterForLocal = savedInstanceState.getLongArray(LOCALCOUNTER);
            pointer = savedInstanceState.getInt(POINTER);
            queue = savedInstanceState.getParcelable(NOTES);
            times = savedInstanceState.getLongArray(TIMES);
            lengths = savedInstanceState.getLongArray(LENGTHS);
        } else {
            counterForLocal = new long[MAXNOTESINTACT];
            pointer = 0;
            queue = new QueueOfNotes();
            queue.put(endEvent, endEvent);
            times = new long[MAXNOTESINTACT];
            lengths = new long[MAXNOTESINTACT];
        }
        initGlobalTimer(counterForGlobal, queue, times, lengths);
        globalTimer.start();

        for(int i = 0; i < MAXNOTESINTACT; ++i) {
            if (counterForLocal[i] != 0) {
                localTimers.put(i, initLocalTimer(counterForLocal[i], i, queue));
                localTimers.get(i).start();
            }
        }

        ///////////
        //delete
        mText = (TextView) findViewById(R.id.mText);
        mText.setText(Long.toString(counterForGlobal));
    }

    void searchForNotes(final QueueOfNotes queue, final long[] Times, long[] Lenghts, long clockTime) {
        while ((pointer < 4) && (Times[pointer] - DIFFERENCE <= clockTime) && (Times[pointer] + DIFFERENCE >= clockTime)) {
            //queue.getStart(pointer) != endEvent
            /////////
            //What will happend if I stop programme here?
            final Integer tmpPointer = new Integer(pointer);
            localTimers.put(tmpPointer, initLocalTimer(Lenghts[tmpPointer], tmpPointer, queue));
            playNote(queue.getStart(tmpPointer), localTimers.get(tmpPointer));

            ++pointer;
        }
    }

    @Override
    protected void onResume() {
        super.onResume();

        midiDriver.start();
        config = midiDriver.config();

        // Print out the details.
        Log.d(this.getClass().getName(), "maxVoices: " + config[0]);
        Log.d(this.getClass().getName(), "numChannels: " + config[1]);
        Log.d(this.getClass().getName(), "sampleRate: " + config[2]);
        Log.d(this.getClass().getName(), "mixBufferSize: " + config[3]);
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        Log.e("MAIN_ACTIVITY", "Saving state");

        Log.e("YOYOYO", Integer.toString(queue.notes.size())+ "_" + Integer.toString(pointer));

        globalTimer.cancel();
        for (int i = 0; i < localTimers.size(); ++i) {
            Integer key = localTimers.keyAt(i);
            localTimers.get(key).cancel();
            localTimers.delete(key);
        }
        midiDriver.stop();

        outState.putLong(GLOBALCOUNTER, counterForGlobal);
        outState.putLongArray(LOCALCOUNTER, counterForLocal);
        outState.putInt(POINTER, pointer);
        outState.putParcelable(NOTES, queue);
        outState.putLongArray(TIMES, times);
        outState.putLongArray(LENGTHS, lengths);
    }

    @Override
    public void onMidiStart() {
        Log.d(this.getClass().getName(), "onMidiStart()");
    }

    private void playNote(final byte[] startEvent, CountDownTimer timer) {
        midiDriver.write(instrumentEvent);
        midiDriver.write(startEvent);
        timer.start();
    }

    /////////////
    //what should I do with notes, what are playing
    private void PlaySong(QueueOfNotes queue, long[] Times, long[] Lenghts){
        pointer = 0;
        globalTimer.cancel();
        initGlobalTimer(Long.MAX_VALUE, queue, Times, Lenghts);
        globalTimer.start();
    }

    @Override
    public void onClick(View v) {
        ///////////////////////////////////
        // What should I do if events have different size?
        QueueOfNotes queue = new QueueOfNotes();

        Events = new byte[MAXNOTESINTACT + 1][2][3];
        times = new long[MAXNOTESINTACT];
        lengths = new long[MAXNOTESINTACT];

        startEvent = new byte[3];
        startEvent[0] = (byte) (0x90 | 0x00);
        startEvent[1] = (byte) 60;
        startEvent[2] = (byte) 0x3F;

        finishEvent = new byte[3];
        finishEvent[0] = (byte) (0x80 | 0x00);
        finishEvent[1] = (byte) 60;
        finishEvent[2] = (byte) 0x00;

        queue.put(startEvent, finishEvent);
        times[0] = 3000;
        lengths[0] = 8000;


        startEvent = new byte[3];
        startEvent[0] = (byte) (0x90 | 0x00);
        startEvent[1] = (byte) 64;
        startEvent[2] = (byte) 0x4F;

        finishEvent = new byte[3];
        finishEvent[0] = (byte) (0x80 | 0x00);
        finishEvent[1] = (byte) 64;
        finishEvent[2] = (byte) 0x00;

        queue.put(startEvent, finishEvent);
        times[1] = 3000;
        lengths[1] = 4000;


        startEvent = new byte[3];
        startEvent[0] = (byte) (0x90 | 0x00);
        startEvent[1] = (byte) 67;
        startEvent[2] = (byte) 0x5F;

        finishEvent = new byte[3];
        finishEvent[0] = (byte) (0x80 | 0x00);
        finishEvent[1] = (byte) 67;
        finishEvent[2] = (byte) 0x00;

        queue.put(startEvent, finishEvent);
        times[2] = 6000;
        lengths[2] = 2000;

        startEvent = new byte[3];
        startEvent[0] = (byte) (0x90 | 0x00);
        startEvent[1] = (byte) 72;
        startEvent[2] = (byte) 0x5F;

        finishEvent = new byte[3];
        finishEvent[0] = (byte) (0x80 | 0x00);
        finishEvent[1] = (byte) 72;
        finishEvent[2] = (byte) 0x00;

        queue.put(startEvent, finishEvent);
        times[3] = 9000;
        lengths[3] = 1000;

        queue.put(endEvent, endEvent);
        times[4] = 12000;
        lengths[4] = 2000;

        Log.d(this.getClass().getName(), "Motion event: ");
        if (v.getId() == R.id.buttonPlaySong) {
            PlaySong(queue, times, lengths);
        }
    }
}

