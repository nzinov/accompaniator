package accompaniator_team.playwithme;

import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.media.AudioManager;
import android.os.IBinder;
import android.support.annotation.Nullable;

import java.io.Serializable;
import java.util.concurrent.LinkedBlockingQueue;

import be.tarsos.dsp.AudioDispatcher;
import be.tarsos.dsp.AudioEvent;
import be.tarsos.dsp.onsets.ComplexOnsetDetector;
import be.tarsos.dsp.onsets.OnsetHandler;
import be.tarsos.dsp.pitch.PitchDetectionHandler;
import be.tarsos.dsp.pitch.PitchDetectionResult;
import be.tarsos.dsp.pitch.PitchProcessor;

import static java.lang.Math.min;

public class ListenerService extends Service {
    private static final String TAG = "ListenerService";

    LinkedBlockingQueue<Chord> queueIn;

    class PitchOnsetHandler implements OnsetHandler, PitchDetectionHandler {

        double mLastTimeStamp;
        float mPitch;
        int onsetCnt = 0;
        int pitchCnt = 0;

        GuiLogger mGuiLog;

        PitchOnsetHandler(Context context) {
            mGuiLog = new GuiLogger(context);
        }

        @Override
        public void handleOnset(final double time, double salience) {
            if (mLastTimeStamp >= time) {
                return;
            }
            Note note = Note.fromFrequency(mPitch);
            double exactFreq = note.toFrequency();
            Note[] notes = {note};
            Chord chord = new Chord(notes, min((int) salience, 500), 0);
            queueIn.offer(chord);

            String message =
                    String.format("%d Onset detected at %.2fs\n" +
                                    "salience %.2f\n" +
                                    "pitch %.2fHz\n" +
                                    "exact pitch %.2fHz\n" +
                                    "divergence %.2fHz (%.2f%%)\n"+
                                    "note number %d\n" +
                                    "lastTimeStamp %.2fs",
                            onsetCnt, time, salience, mPitch, exactFreq,
                            Math.abs(mPitch-exactFreq),
                            100*(Note.NumToFreq(note.number)-mPitch)/
                                    Math.abs((Note.NumToFreq(note.number)-Note.NumToFreq(note.number+1))),
                            note.number, mLastTimeStamp);

            MainActivity.GuiMessage l = (Serializable & MainActivity.GuiMessage) (MainActivity a) -> {
                a.onsetText.setText(message);
            };
            mGuiLog.sendResult(l);

            ++onsetCnt;
        }

        @Override
        public void handlePitch(PitchDetectionResult pitchDetectionResult, AudioEvent audioEvent) {
            if (pitchDetectionResult.getPitch() != -1) {
                double timeStamp = audioEvent.getTimeStamp();
                float pitch = pitchDetectionResult.getPitch();
                float probability = pitchDetectionResult.getProbability();
                double rms = audioEvent.getRMS() * 100;
                mPitch = pitch;
                mLastTimeStamp = timeStamp;

                final String message = String.format("%d Pitch detected at %.2fs\nfreq %.2fHz\nprobability %.2f\nRMS %.5f",
                        pitchCnt, timeStamp, pitch, probability, rms);

                MainActivity.GuiMessage l = (Serializable & MainActivity.GuiMessage) (MainActivity a) -> {
                    a.pitchText.setText(message);
                };
                mGuiLog.sendResult(l);

                ++pitchCnt;
            }
        }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        queueIn = SingletonClass.getInstance().queueIn;

        AudioManager audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);
        audioManager.setMode(AudioManager.MODE_IN_COMMUNICATION);
        AudioDispatcher dispatcher = EchoCancellationAudioDispatcherFactory.fromDefaultMicrophoneEchoCancellation(22050, 1024, 0);

        PitchOnsetHandler pitchOnsetHandler = new PitchOnsetHandler(this);

        ComplexOnsetDetector onsetProcessor = new ComplexOnsetDetector(1024, 0.4);
        onsetProcessor.setHandler(pitchOnsetHandler);
        dispatcher.addAudioProcessor(onsetProcessor);

        PitchProcessor pitchProcessor = new PitchProcessor(PitchProcessor.PitchEstimationAlgorithm.FFT_YIN,
                22050, 1024, pitchOnsetHandler);
        dispatcher.addAudioProcessor(pitchProcessor);

        Thread audioThread = new Thread(dispatcher, "Audio Thread");
        audioThread.start();

        return super.onStartCommand(intent, flags, startId);
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
