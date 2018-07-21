package accompaniator_team.playwithme;

import android.content.Context;
import android.content.Intent;
import android.support.v4.content.LocalBroadcastManager;

import java.io.Serializable;

public class GuiLogger {
    private LocalBroadcastManager localBroadcastManager;

    GuiLogger(Context context) {
        localBroadcastManager = LocalBroadcastManager.getInstance(context);
    }

    void sendResult(MainActivity.GuiMessage message) {
        Intent intent = new Intent(MainActivity.MESSAGE_GUI);
        if (message != null)
            intent.putExtra(MainActivity.MESSAGE_GUI, (Serializable)message);
        localBroadcastManager.sendBroadcast(intent);
    }
}
