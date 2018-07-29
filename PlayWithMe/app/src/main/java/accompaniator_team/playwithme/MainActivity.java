package accompaniator_team.playwithme;

import android.Manifest;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.media.audiofx.AcousticEchoCanceler;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import android.support.v4.content.LocalBroadcastManager;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.widget.TextView;

import java.util.concurrent.LinkedBlockingQueue;

public class MainActivity extends AppCompatActivity {
    private static final int SAMPLE_RATE = 44100;

    public static final String MESSAGE_GUI = "message.gui";

    private BroadcastReceiver broadcastReceiver;
    LinkedBlockingQueue<Chord> queueOut;
    LinkedBlockingQueue<Chord> queueIn;
    TextView onsetText, pitchText, soundText, predictorText;
    private static final int REQUEST_RECORD_AUDIO_PERMISSION = 200;

    interface GuiMessage {
        void action(MainActivity s);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.RECORD_AUDIO}, REQUEST_RECORD_AUDIO_PERMISSION);
        }

        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        SingletonClass.getInstance().mainActivity = this;
        SingletonClass.getInstance().context = getApplicationContext();

        boolean hasLowLatencyFeature =
                getPackageManager().hasSystemFeature(PackageManager.FEATURE_AUDIO_LOW_LATENCY);

        boolean hasProFeature =
                getPackageManager().hasSystemFeature(PackageManager.FEATURE_AUDIO_PRO);
        boolean hasAcousticEchoCancellation = AcousticEchoCanceler.isAvailable();

        onsetText = findViewById(R.id.textViewOnsetText);
        pitchText = findViewById(R.id.textViewPitchText);
        soundText = findViewById(R.id.textViewSoundInfo);
        predictorText = findViewById(R.id.textViewPredictorText);

        TextView hardwareSoundInfo = findViewById(R.id.textViewHardwareSoundInfo);
        hardwareSoundInfo.setText(String.format("hasLowLatencyFeature: %b\nhasProFeature: %b\nhasAcousticEchoCancellation: %b",
                hasLowLatencyFeature, hasProFeature, hasAcousticEchoCancellation));

        queueOut = SingletonClass.getInstance().queueOut;
        queueIn = SingletonClass.getInstance().queueIn;

        Intent playerIntent = new Intent(MainActivity.this, PlayerService.class);
        startService(playerIntent);

        Intent predictorIntent = new Intent(MainActivity.this, ChordPredictorService.class);
        startService(predictorIntent);

        Intent listenerIntent = new Intent(MainActivity.this, ListenerService.class);
        startService(listenerIntent);

        broadcastReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                GuiMessage s = (GuiMessage)intent.getSerializableExtra(MESSAGE_GUI);
                //soundText.setText(s);
                s.action(MainActivity.this);
            }
        };
    }

    @Override
    protected void onStart() {
        super.onStart();
        LocalBroadcastManager.getInstance(this).registerReceiver((broadcastReceiver),
                new IntentFilter(MESSAGE_GUI));
    }

    @Override
    protected void onResume() {
        super.onResume();
        //player.onResume();
    }

    @Override
    protected void onPause() {
        super.onPause();
        //player.onPause();
    }

    @Override
    protected void onStop() {
        LocalBroadcastManager.getInstance(this).unregisterReceiver(broadcastReceiver);
        super.onStop();
    }

    @Override
    protected void onDestroy() {
        SingletonClass.getInstance().mainActivity = null;
        super.onDestroy();
    }

    public void playTestSound(View view) {
        TextView info = (TextView) findViewById(R.id.textViewSoundInfo);
        info.setText("Playing");
        //player.playTestSound();
        Note[] notes = {new Note(100)};
        queueOut.add(new Chord(notes, 127, 127));
        info.setText("Not playing");
    }

    public void settings(View view) {
        Intent intent = new Intent(this, SettingsActivity.class);
        startActivity(intent);
    }
}
