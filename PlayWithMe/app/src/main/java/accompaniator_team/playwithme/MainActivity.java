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
import be.tarsos.dsp.pitch.PitchDetectionHandler;
import be.tarsos.dsp.pitch.PitchDetectionResult;
import be.tarsos.dsp.pitch.PitchProcessor;

public class MainActivity extends AppCompatActivity {

    //PlayerService player;
    LinkedBlockingQueue<PlayerService.Chord> queueOut;
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

        //player = new PlayerService();

        Intent playerIntent = new Intent(MainActivity.this, PlayerService.class);

        //queueOut = new LinkedBlockingQueue<>();
        queueOut = SingletonClass.getInstance().queueOut;
        playerIntent.putExtra(PlayerService.QUEUE_NAME, queueOut);
        startService(playerIntent);

        AudioDispatcher dispatcher = AudioDispatcherFactory.fromDefaultMicrophone(22050,1024,0);

        PitchDetectionHandler pdh = new PitchDetectionHandler() {

            @Override
            public void handlePitch(PitchDetectionResult res, AudioEvent e){
                final float pitchInHz = res.getPitch();
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        processPitch(pitchInHz);
                    }
                });
            }
        };

        AudioProcessor pitchProcessor = new PitchProcessor(PitchProcessor.PitchEstimationAlgorithm.FFT_YIN, 22050, 1024, pdh);
        dispatcher.addAudioProcessor(pitchProcessor);

        Thread audioThread = new Thread(dispatcher, "Audio Thread");
        audioThread.start();
    }

    public void processPitch(float pitchInHz) {

        pitchText.setText("" + pitchInHz);

        if(pitchInHz >= 110 && pitchInHz < 123.47) {
            //A
            noteText.setText("A");
        }
        else if(pitchInHz >= 123.47 && pitchInHz < 130.81) {
            //B
            noteText.setText("B");
        }
        else if(pitchInHz >= 130.81 && pitchInHz < 146.83) {
            //C
            noteText.setText("C");
        }
        else if(pitchInHz >= 146.83 && pitchInHz < 164.81) {
            //D
            noteText.setText("D");
        }
        else if(pitchInHz >= 164.81 && pitchInHz <= 174.61) {
            //E
            noteText.setText("E");
        }
        else if(pitchInHz >= 174.61 && pitchInHz < 185) {
            //F
            noteText.setText("F");
        }
        else if(pitchInHz >= 185 && pitchInHz < 196) {
            //G
            noteText.setText("G");
        }
    }

    @Override
    protected void onResume()
    {
        super.onResume();

        //player.onResume();

    }

    @Override
    protected void onPause()
    {
        super.onPause();

        //player.onPause();
    }

    public void playTestSound(View view) {
        TextView info = (TextView)findViewById(R.id.textViewSoundInfo);
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
