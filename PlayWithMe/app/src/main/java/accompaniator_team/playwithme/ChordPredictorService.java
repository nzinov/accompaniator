package accompaniator_team.playwithme;

import android.app.Service;
import android.content.Intent;
import android.content.res.AssetManager;
import android.os.IBinder;
import android.support.annotation.Nullable;


import java.util.concurrent.LinkedBlockingQueue;

public class ChordPredictorService  extends Service {
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        ChordPredictorThread thread = new ChordPredictorThread(this, getAssets());
        thread.start();

        return super.onStartCommand(intent, flags, startId);
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
