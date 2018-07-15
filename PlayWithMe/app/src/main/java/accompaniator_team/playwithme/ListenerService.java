package accompaniator_team.playwithme;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.support.annotation.Nullable;
import android.util.Log;

import org.billthefarmer.mididriver.MidiDriver;

import java.util.concurrent.LinkedBlockingQueue;

import be.tarsos.dsp.AudioDispatcher;
import be.tarsos.dsp.AudioEvent;
import be.tarsos.dsp.AudioProcessor;
import be.tarsos.dsp.io.android.AudioDispatcherFactory;
import be.tarsos.dsp.onsets.ComplexOnsetDetector;
import be.tarsos.dsp.onsets.OnsetHandler;
import be.tarsos.dsp.pitch.PitchDetectionHandler;
import be.tarsos.dsp.pitch.PitchDetectionResult;
import be.tarsos.dsp.pitch.PitchProcessor;

public class ListenerService extends Service {
    private static final String TAG = "ListenerService";

    LinkedBlockingQueue<PlayerService.Note> queueIn;

    int hzToMidiNumber(float hz) {
        return (int) (12 * Math.log(hz / 440) / Math.log(2));
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        queueIn = SingletonClass.getInstance().queueIn;

        AudioDispatcher dispatcher = AudioDispatcherFactory.fromDefaultMicrophone(22050,1024,0);

        OnsetHandler odh = new OnsetHandler() {

            @Override
            public void handleOnset(double time, double salience){
                final double time_ = time;
                final double salience_ = salience;
                new Runnable() {
                    @Override
                    public void run() {
                        //queueIn.offer(new PlayerService.Note(...));
                    }
                }.run();
            }
        };

        ComplexOnsetDetector onsetProcessor = new ComplexOnsetDetector(1024, 0.4);
        onsetProcessor.setHandler(odh);
        dispatcher.addAudioProcessor(onsetProcessor);

        PitchDetectionHandler pitchHandler = new PitchDetectionHandler() {
            @Override
            public void handlePitch(PitchDetectionResult pitchDetectionResult, AudioEvent audioEvent) {
                if(pitchDetectionResult.getPitch() != -1){
                    double timeStamp = audioEvent.getTimeStamp();
                    float pitch = pitchDetectionResult.getPitch();
                    float probability = pitchDetectionResult.getProbability();
                    double rms = audioEvent.getRMS() * 100;
                    String message = String.format("Pitch detected at %.2fs: %.2fHz ( %.2f probability, RMS: %.5f )\n", timeStamp,pitch,probability,rms);
                }
            }
        };

        PitchProcessor pitchProcessor = new PitchProcessor(PitchProcessor.PitchEstimationAlgorithm.FFT_YIN,
                22050, 1024, pitchHandler);
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
