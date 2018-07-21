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

    LinkedBlockingQueue<PlayerService.Chord> queueIn;

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
            String pitchStr;
            if (mLastTimeStamp < time) {
                pitchStr = String.format("%.2fHz", mPitch);
                PlayerService.Note note = PlayerService.Note.fromFrequency(mPitch);
                PlayerService.Note[] notes = { note };
                PlayerService.Chord chord = new PlayerService.Chord(notes, min((int)salience, 500), 0);
                queueIn.offer(chord);
            } else {
                return;
            }
            String message =
                    String.format("%d Onset detected at %.2fs\nsalience %.2f\npitch %s\nnote number %d\nlastTimeStamp %.2fs",
                            onsetCnt, time, salience, pitchStr, PlayerService.Note.fromFrequency(mPitch).number, mLastTimeStamp);

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
