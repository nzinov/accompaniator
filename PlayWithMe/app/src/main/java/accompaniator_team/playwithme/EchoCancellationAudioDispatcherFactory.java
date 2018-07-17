package accompaniator_team.playwithme;

import android.content.Context;
import android.media.AudioManager;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.media.audiofx.AcousticEchoCanceler;

import be.tarsos.dsp.AudioDispatcher;
import be.tarsos.dsp.io.TarsosDSPAudioFormat;
import be.tarsos.dsp.io.TarsosDSPAudioInputStream;
import be.tarsos.dsp.io.android.AndroidAudioInputStream;
import be.tarsos.dsp.io.android.AudioDispatcherFactory;

import static android.support.v4.content.ContextCompat.getSystemService;

public class EchoCancellationAudioDispatcherFactory extends AudioDispatcherFactory {

    public static AudioDispatcher fromDefaultMicrophoneEchoCancellation(final int sampleRate,
                                                                        final int audioBufferSize, final int bufferOverlap) {
        int minAudioBufferSize = AudioRecord.getMinBufferSize(sampleRate,
                android.media.AudioFormat.CHANNEL_IN_MONO,
                android.media.AudioFormat.ENCODING_PCM_16BIT);
        int minAudioBufferSizeInSamples = minAudioBufferSize / 2;
        if (minAudioBufferSizeInSamples <= audioBufferSize) {

            AudioRecord audioInputStream = new AudioRecord(
                    MediaRecorder.AudioSource.VOICE_COMMUNICATION, sampleRate,
                    android.media.AudioFormat.CHANNEL_IN_MONO,
                    android.media.AudioFormat.ENCODING_PCM_16BIT,
                    audioBufferSize * 2);

            AcousticEchoCanceler echoCanceler;
            if (AcousticEchoCanceler.isAvailable()) {
                echoCanceler = AcousticEchoCanceler.create(audioInputStream.getAudioSessionId());
                echoCanceler.setEnabled(true);
            }

            TarsosDSPAudioFormat format = new TarsosDSPAudioFormat(sampleRate, 16, 1, true, false);

            TarsosDSPAudioInputStream audioStream = new AndroidAudioInputStream(audioInputStream, format);
            //start recording ! Opens the stream.
            audioInputStream.startRecording();

            return new AudioDispatcher(audioStream, audioBufferSize, bufferOverlap);
        } else {
            throw new IllegalArgumentException("Buffer size too small should be at least " + (minAudioBufferSize * 2));
        }
    }
}
