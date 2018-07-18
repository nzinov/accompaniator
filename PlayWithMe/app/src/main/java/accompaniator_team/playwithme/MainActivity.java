package accompaniator_team.playwithme;

import android.Manifest;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioManager;
import android.media.audiofx.AcousticEchoCanceler;
import android.provider.ContactsContract;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.widget.TextView;

import java.util.concurrent.LinkedBlockingQueue;

import be.tarsos.dsp.AudioDispatcher;
import be.tarsos.dsp.AudioEvent;
import be.tarsos.dsp.io.android.AudioDispatcherFactory;
import be.tarsos.dsp.onsets.ComplexOnsetDetector;
import be.tarsos.dsp.onsets.OnsetHandler;
import be.tarsos.dsp.pitch.PitchDetectionHandler;
import be.tarsos.dsp.pitch.PitchDetectionResult;
import be.tarsos.dsp.pitch.PitchProcessor;

import static android.support.v4.content.ContextCompat.getSystemService;

public class MainActivity extends AppCompatActivity {
    private static final int SAMPLE_RATE = 44100;

    LinkedBlockingQueue<PlayerService.Chord> queueOut;
    LinkedBlockingQueue<PlayerService.Note> queueIn;
    TextView onsetText, pitchText;
    private static final int REQUEST_RECORD_AUDIO_PERMISSION = 200;

    class PitchOnsetHandler implements OnsetHandler, PitchDetectionHandler {

        double mLastTimeStamp;
        float mPitch;

        @Override
        public void handleOnset(final double time, double salience){
            final double time_ = time;
            final double salience_ = salience;
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    String pitchStr = "none";
                    if(mLastTimeStamp < time_) {
                        pitchStr = String.format("%.2fHz", mPitch);
                        PlayerService.Note note = PlayerService.Note.fromFrequency(mPitch);
                        queueIn.offer(note);
                    }
                    String message =
                            String.format("Onset detected at %.2fs\nsalience %.2f\npitch %s\nnote number %d\nlastTimeStamp %.2fs",
                            time_, salience_, pitchStr, PlayerService.Note.fromFrequency(mPitch).number, mLastTimeStamp);
                    onsetText.setText(message);
                }
            });
        }
        @Override
        public void handlePitch(PitchDetectionResult pitchDetectionResult, AudioEvent audioEvent) {
            if(pitchDetectionResult.getPitch() != -1){
                double timeStamp = audioEvent.getTimeStamp();
                float pitch = pitchDetectionResult.getPitch();
                float probability = pitchDetectionResult.getProbability();
                double rms = audioEvent.getRMS() * 100;
                mPitch = pitch;
                mLastTimeStamp = timeStamp;

                final String message = String.format("Pitch detected at %.2fs: %.2fHz ( %.2f probability, RMS: %.5f )\n", timeStamp,pitch,probability,rms);
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        pitchText.setText(message);
                    }
                });
            }
        }
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
        TextView hardwareSoundInfo = findViewById(R.id.textViewHardwareSoundInfo);
        hardwareSoundInfo.setText(String.format("hasLowLatencyFeature: %b\nhasProFeature: %b\nhasAcousticEchoCancellation: %b",
                hasLowLatencyFeature, hasProFeature, hasAcousticEchoCancellation));

        queueOut = SingletonClass.getInstance().queueOut;
        queueIn = SingletonClass.getInstance().queueIn;

        Intent playerIntent = new Intent(MainActivity.this, PlayerService.class);
        startService(playerIntent);

        Intent predictorIntent = new Intent(MainActivity.this, ChordPredictorService.class);
        startService(predictorIntent);

        /*Intent listenerIntent = new Intent(MainActivity.this, ListenerService.class);
        startService(listenerIntent);*/
        AudioManager audioManager = (AudioManager)getSystemService(Context.AUDIO_SERVICE);
        audioManager.setMode(AudioManager.MODE_IN_COMMUNICATION);
        AudioDispatcher dispatcher = EchoCancellationAudioDispatcherFactory.fromDefaultMicrophoneEchoCancellation(22050,1024,0);

        PitchOnsetHandler pitchOnsetHandler = new MainActivity.PitchOnsetHandler();

        ComplexOnsetDetector onsetProcessor = new ComplexOnsetDetector(1024, 0.4);
        onsetProcessor.setHandler(pitchOnsetHandler);
        dispatcher.addAudioProcessor(onsetProcessor);

        PitchProcessor pitchProcessor = new PitchProcessor(PitchProcessor.PitchEstimationAlgorithm.FFT_YIN,
                22050, 1024, pitchOnsetHandler);
        dispatcher.addAudioProcessor(pitchProcessor);

        Thread audioThread = new Thread(dispatcher, "Audio Thread");
        audioThread.start();
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
    protected void onDestroy() {
        SingletonClass.getInstance().mainActivity = null;
        super.onDestroy();
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
