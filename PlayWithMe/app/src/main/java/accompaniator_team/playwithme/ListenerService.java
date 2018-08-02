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

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        queueIn = SingletonClass.getInstance().queueIn;

        ListenerThread thread = new ListenerThread(this);
        thread.start();

        return super.onStartCommand(intent, flags, startId);
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onTaskRemoved(Intent rootIntent) {
        SingletonClass.getInstance().working.set(false);
        super.onTaskRemoved(rootIntent);
    }
}
