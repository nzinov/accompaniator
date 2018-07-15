package accompaniator_team.playwithme;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;

import java.util.concurrent.LinkedBlockingQueue;

import be.tarsos.dsp.AudioDispatcher;
import be.tarsos.dsp.AudioEvent;
import be.tarsos.dsp.AudioProcessor;
import be.tarsos.dsp.io.android.AudioDispatcherFactory;
import be.tarsos.dsp.onsets.ComplexOnsetDetector;
import be.tarsos.dsp.onsets.OnsetHandler;
import be.tarsos.dsp.onsets.PrintOnsetHandler;
import be.tarsos.dsp.pitch.PitchDetectionHandler;
import be.tarsos.dsp.pitch.PitchDetectionResult;
import be.tarsos.dsp.pitch.PitchProcessor;

import static android.os.SystemClock.sleep;

public class MainActivity extends AppCompatActivity {
    private static final int SAMPLE_RATE = 44100;

    LinkedBlockingQueue<PlayerService.Chord> queueOut;
    LinkedBlockingQueue<PlayerService.Note> queueIn;
    TextView noteText, pitchText;
    private static final int REQUEST_RECORD_AUDIO_PERMISSION = 200;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.RECORD_AUDIO}, REQUEST_RECORD_AUDIO_PERMISSION);
        }

        boolean hasLowLatencyFeature =
                getPackageManager().hasSystemFeature(PackageManager.FEATURE_AUDIO_LOW_LATENCY);

        boolean hasProFeature =
                getPackageManager().hasSystemFeature(PackageManager.FEATURE_AUDIO_PRO);

        noteText = findViewById(R.id.textViewNoteText);
        pitchText = findViewById(R.id.textViewPitchText);
        TextView hardwareSoundInfo = findViewById(R.id.textViewHardwareSoundInfo);
        hardwareSoundInfo.setText(String.format("hasLowLatencyFeature: %b\nhasProFeature: %b",
                hasLowLatencyFeature, hasProFeature));

        queueOut = SingletonClass.getInstance().queueOut;
        queueIn = SingletonClass.getInstance().queueIn;

        Intent playerIntent = new Intent(MainActivity.this, PlayerService.class);
        startService(playerIntent);

        /*Intent listenerIntent = new Intent(MainActivity.this, ListenerService.class);
        startService(listenerIntent);*/

        AudioDispatcher dispatcher = AudioDispatcherFactory.fromDefaultMicrophone(22050,1024,0);

        OnsetHandler odh = new OnsetHandler() {

            @Override
            public void handleOnset(double time, double salience){
                final double time_ = time;
                final double salience_ = salience;
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        //queueIn.offer(new PlayerService.Note((int)pitchInHz));
                        pitchText.setText("" + time_+" " + salience_);
                    }
                });
            }
        };

        ComplexOnsetDetector onsetProcessor = new ComplexOnsetDetector(1024, 0.4);
        onsetProcessor.setHandler(odh);
        dispatcher.addAudioProcessor(onsetProcessor);

        Thread audioThread = new Thread(dispatcher, "Audio Thread");
        audioThread.start();
    }

    @Override
    protected void onResume() {
        super.onResume();

        //player.onResume();
        /*while (true) {
            PlayerService.Note note = queueIn.peek();
            if (note != null) {
                pitchText.setText("Note " + note.number);
            }
            sleep(100);
        }*/

    }

    @Override
    protected void onPause() {
        super.onPause();

        //player.onPause();
    }

    public void playTestSound(View view) {
        TextView info = (TextView) findViewById(R.id.textViewSoundInfo);
        info.setText("Playing");
        //player.playTestSound();
        PlayerService.Note[] notes = {new PlayerService.Note(100)};
        queueOut.add(new PlayerService.Chord(notes, 127, 127));
        info.setText("Not playing");
    }

    public void settings(View view) {
        Intent intent = new Intent(this, SettingsActivity.class);
        startActivity(intent);
    }
}
