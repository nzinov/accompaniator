package accompaniator_team.playwithme;

import android.media.AudioRecord;
import android.os.Environment;

import com.android.webrtc.audio.MobileAEC;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

import be.tarsos.dsp.io.TarsosDSPAudioFormat;
import be.tarsos.dsp.io.android.AndroidAudioInputStream;
import speex.EchoCanceller;

import static com.google.common.primitives.Ints.min;

public class EchoCancellationAudioInputStream extends AndroidAudioInputStream {

    private EchoCanceller canceller;

    public EchoCancellationAudioInputStream(AudioRecord audioRecord, TarsosDSPAudioFormat tarsosDSPAudioFormat) {
        super(audioRecord, tarsosDSPAudioFormat);
        canceller = new EchoCanceller();
        canceller.open(8000, 1024, 256);
    }

    public int read(byte[] b, int off, int len) throws IOException {
        byte[] readed = b.clone();
        int result = super.read(readed, off, len);
        byte[] filtered = canceller.captureBytes(readed);
        System.arraycopy(b,0,filtered, 0, filtered.length);
        return result;
    }

    @Override
    public void close() throws IOException {
        super.close();
    }
}
