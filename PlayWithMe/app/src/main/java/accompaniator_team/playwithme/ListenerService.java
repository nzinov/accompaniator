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
        Log.d(TAG, "onStartCommand");

        queueIn = SingletonClass.getInstance().queueIn;

        AudioDispatcher dispatcher = AudioDispatcherFactory.fromDefaultMicrophone(22050, 1024, 0);

        PitchDetectionHandler pdh = new PitchDetectionHandler() {

            LinkedBlockingQueue<PlayerService.Note> queueIn;

            @Override
            public void handlePitch(PitchDetectionResult res, AudioEvent e) {
                final float pitchInHz = res.getPitch();
                (new Runnable() {
                    @Override
                    public void run() {
                        try {
                            queueIn = SingletonClass.getInstance().queueIn;
                            Log.w(TAG, "PITCH!!!!!!!!!!");
                            queueIn.put(new PlayerService.Note(hzToMidiNumber(pitchInHz)));
                        } catch (InterruptedException e) {
                            Log.d(TAG, "", e);
                        }
                    }
                }).run();
            }
        };

        AudioProcessor pitchProcessor = new PitchProcessor(PitchProcessor.PitchEstimationAlgorithm.FFT_YIN, 22050, 1024, pdh);
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
