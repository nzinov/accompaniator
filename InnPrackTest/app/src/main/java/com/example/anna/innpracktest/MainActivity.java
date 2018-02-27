package com.example.anna.innpracktest;

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
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
    // Initialized by zero according to documentation.
    private long[] counterForLocal;
    private long counterForGlobal = Long.MAX_VALUE;
    private MidiDriver midiDriver;
    private byte[] startEvent;
    private byte[] finishEvent;
    private byte[] instrumentEvent;
    private byte[] endEvent;
    private int[] config;
    private Button buttonPlaySong;
    private CountDownTimer globalTimer = null;
    private byte[][][] Events;
    private long[] Times;
    private long[] Lengths;
    private int pointer = 0;
    private long DIFFERENCE = 10;
    ////////////
    private int MAXNOTESINTACT = 10;
    /////////////////////
    //delete
    private TextView mText;

    private CountDownTimer initLocalTimer(long counter, final Integer pointerToClock, final byte[][][] Events){
        CountDownTimer tmpTimer = new CountDownTimer(counter, 1) {

            @Override
            public void onTick(long millisUntilFinished) {
                counterForLocal[pointerToClock] = millisUntilFinished;
            }

            @Override
            public void onFinish() {
                midiDriver.write(Events[pointerToClock][1]);
            };
        };
        return tmpTimer;
    }

    private void initGlobalTimer(long counter, final byte[][][] Events, final long[] Times, final long[] Lenghts) {
        ///////////////////////////
        //What distance should I add?
        //to be synchronized with clock it's important
        // but to have a longer period is important too

        globalTimer = new CountDownTimer(counter, 1) {
            @Override
            public void onTick(long millisUntilFinished) {
                counterForGlobal = millisUntilFinished;
                searchForNotes(Events, Times, Lenghts, Long.MAX_VALUE - counterForGlobal);

                ////////////////////
                //delete
                mText.setText(Long.toString(Long.MAX_VALUE - counterForGlobal) + "_" + Integer.toString(pointer));
            }

            @Override
            public void onFinish() {};
        };
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        buttonPlaySong = (Button)findViewById(R.id.buttonPlaySong);
        buttonPlaySong.setOnClickListener(this);

        midiDriver = new MidiDriver();
        midiDriver.setOnMidiStartListener(this);

        Events = new byte[1][1][3];

        // The end of track
        endEvent = new byte[3];
        endEvent[0] = (byte) (0xFF);
        endEvent[1] = (byte) 0x2F;
        endEvent[2] = (byte) 0x00;

        Events[0][0] = endEvent;

        ////////////////////
        //Somethere I should do it
        counterForLocal = new long[MAXNOTESINTACT];

        if (savedInstanceState != null) {
            counterForGlobal = savedInstanceState.getLong(GLOBALCOUNTER);
            counterForLocal = savedInstanceState.getLongArray(LOCALCOUNTER);
        }
        initGlobalTimer(counterForGlobal, Events, Times, Lengths);
        globalTimer.start();

        for(int i = 0; i < MAXNOTESINTACT; ++i) {
            if (counterForLocal[i] != 0) {
                CountDownTimer tmpTimer = initLocalTimer(counterForLocal[i], i, Events);
                //tmpTimer.start();
            }
        }

        ///////////
        //delete
        mText = (TextView) findViewById(R.id.mText);
        mText.setText(Long.toString(counterForGlobal));
    }

    void searchForNotes(final byte[][][] Events, final long[] Times, long[] Lenghts, long clockTime) {
        while ((Events[pointer][0] != endEvent) && (Times[pointer] - DIFFERENCE <= clockTime) && (Times[pointer] + DIFFERENCE >= clockTime)) {
            /////////
            //What will happend if I stop programme here?
            final Integer tmpPointer = new Integer(pointer);
            CountDownTimer tmpTimer = initLocalTimer(Lenghts[tmpPointer], tmpPointer, Events);
            playNote(Events[tmpPointer][0], tmpTimer);

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
    protected void onPause() {
        super.onPause();
        ///////////////////////////////////////////////////////////
        //What should I do if somebody hide my app?
        //Because i cann't stop all the clocks
        globalTimer.cancel();
        midiDriver.stop();
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);

        outState.putLong(GLOBALCOUNTER, counterForGlobal);
        outState.putLongArray(LOCALCOUNTER, counterForLocal);
    }

    @Override
    public void onMidiStart() {
        Log.d(this.getClass().getName(), "onMidiStart()");
    }

    private void playNote(final byte[] startEvent, CountDownTimer timer) {
        instrumentEvent = new byte[2];
        instrumentEvent[0] = (byte) (0xC0 | 0x00);
        instrumentEvent[1] = (byte) 0x30;
        midiDriver.write(instrumentEvent);

        midiDriver.write(startEvent);

        timer.start();
    }

    /////////////
    //what should I do with notes, what are playing
    private void PlaySong(byte[][][] Events, long[] Times, long[] Lenghts){
        pointer = 0;
        globalTimer.cancel();
        initGlobalTimer(Long.MAX_VALUE, Events, Times, Lenghts);
        globalTimer.start();
    }

    @Override
    public void onClick(View v) {
        ///////////////////////////////////
        // What should I do if events have different size?
        Events = new byte[MAXNOTESINTACT + 1][2][3];
        Times = new long[MAXNOTESINTACT];
        Lengths = new long[MAXNOTESINTACT];

        startEvent = new byte[3];
        startEvent[0] = (byte) (0x90 | 0x00);
        startEvent[1] = (byte) 60;
        startEvent[2] = (byte) 0x3F;

        finishEvent = new byte[3];
        finishEvent[0] = (byte) (0x80 | 0x00);
        finishEvent[1] = (byte) 60;
        finishEvent[2] = (byte) 0x00;

        Events[0][0] = startEvent;
        Events[0][1] = finishEvent;
        Times[0] = 3000;
        Lengths[0] = 8000;


        startEvent = new byte[3];
        startEvent[0] = (byte) (0x90 | 0x00);
        startEvent[1] = (byte) 64;
        startEvent[2] = (byte) 0x4F;

        finishEvent = new byte[3];
        finishEvent[0] = (byte) (0x80 | 0x00);
        finishEvent[1] = (byte) 64;
        finishEvent[2] = (byte) 0x00;

        Events[1][0] = startEvent;
        Events[1][1] = finishEvent;
        Times[1] = 3000;
        Lengths[1] = 4000;


        startEvent = new byte[3];
        startEvent[0] = (byte) (0x90 | 0x00);
        startEvent[1] = (byte) 67;
        startEvent[2] = (byte) 0x5F;

        finishEvent = new byte[3];
        finishEvent[0] = (byte) (0x80 | 0x00);
        finishEvent[1] = (byte) 67;
        finishEvent[2] = (byte) 0x00;

        Events[2][0] = startEvent;
        Events[2][1] = finishEvent;
        Times[2] = 6000;
        Lengths[2] = 2000;

        startEvent = new byte[3];
        startEvent[0] = (byte) (0x90 | 0x00);
        startEvent[1] = (byte) 72;
        startEvent[2] = (byte) 0x5F;

        finishEvent = new byte[3];
        finishEvent[0] = (byte) (0x80 | 0x00);
        finishEvent[1] = (byte) 72;
        finishEvent[2] = (byte) 0x00;

        Events[3][0] = startEvent;
        Events[3][1] = finishEvent;
        Times[3] = 9000;
        Lengths[3] = 1000;

        // The end of track
        endEvent = new byte[3];
        endEvent[0] = (byte) (0xFF);
        endEvent[1] = (byte) 0x2F;
        endEvent[2] = (byte) 0x00;

        Events[4][0] = endEvent;
        Times[4] = 12000;
        Lengths[4] = 2000;

        Log.d(this.getClass().getName(), "Motion event: ");
        if (v.getId() == R.id.buttonPlaySong) {
            PlaySong(Events, Times, Lengths);
        }
    }
}

