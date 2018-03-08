package com.example.anna.innpracktest;

//import android.app.Fragment;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import android.support.v7.app.AppCompatActivity;
import android.view.View;
import android.widget.TextView;

import be.tarsos.dsp.AudioDispatcher;
import be.tarsos.dsp.AudioEvent;
import be.tarsos.dsp.AudioProcessor;
import be.tarsos.dsp.io.android.AudioDispatcherFactory;
import be.tarsos.dsp.pitch.PitchDetectionHandler;
import be.tarsos.dsp.pitch.PitchDetectionResult;
import be.tarsos.dsp.pitch.PitchProcessor;

import static com.example.anna.innpracktest.NoteMap.displayNoteOf;

public class tarsosActivity extends AppCompatActivity {

    private static final int MY_PERMISSIONS_REQUEST_RECORD_AUDIO = 0;
    StringBuffer total = new StringBuffer("");
    String last = "Z";
    NoteStan stan = new NoteStan();
    @Override
  protected void onCreate(Bundle savedInstanceState) {
      super.onCreate(savedInstanceState);
      setContentView(R.layout.activity_tarsos);

      if (ContextCompat.checkSelfPermission(tarsosActivity.this,
              Manifest.permission.RECORD_AUDIO)
              != PackageManager.PERMISSION_GRANTED) {

          // Permission is not granted
          // Should we show an explanation?
          if (ActivityCompat.shouldShowRequestPermissionRationale(tarsosActivity.this,
                  Manifest.permission.RECORD_AUDIO)) {

              // Show an explanation to the user *asynchronously* -- don't block
              // this thread waiting for the user's response! After the user
              // sees the explanation, try again to request the permission.

          } else {

              // No explanation needed; request the permission
              ActivityCompat.requestPermissions(tarsosActivity.this,
                      new String[]{Manifest.permission.RECORD_AUDIO},
                      MY_PERMISSIONS_REQUEST_RECORD_AUDIO);

              // MY_PERMISSIONS_REQUEST_READ_CONTACTS is an
              // app-defined int constant. The callback method gets the
              // result of the request.
          }
      }
  }


  public void buttonClick(View view) {

      //int hz = 44100;
      //MicrophoneAudioDispatcher audioDispatcher = new MicrophoneAudioDispatcher(44100, 2048, 1024);

      //AudioDispatcherFactory af = new AudioDispatcherFactory();

     /* if (af == null) {
          Log.e("debug an error: ", " null audio2");
      }*/
   /*   if (ContextCompat.checkSelfPermission(thisActivity, Manifest.permission.WRITE_CALENDAR)
              != PackageManager.PERMISSION_GRANTED) {
          // Permission is not granted
      }
     */
   AudioDispatcher dispatcher =
              AudioDispatcherFactory.fromDefaultMicrophone(22050,1024,0);
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

  public void clearButtonClick(View view){
        stan = new NoteStan();
  }

  public void processPitch(float pitchInHz) {

        TextView pitchText = (TextView) findViewById(R.id.textView);
        TextView totalText = (TextView) findViewById(R.id.textView3);

        pitchText.setText("" + pitchInHz);
        String note = displayNoteOf(pitchInHz);
        if (note != "")
            stan.addNote(note);
        totalText.setText(stan.toString());

    }
}
