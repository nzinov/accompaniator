package accompaniator_team;

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

import static com.google.common.primitives.Ints.min;

public class EchoCancellationAudioInputStream extends AndroidAudioInputStream {
    MobileAEC aecm;
    private final int cacheSize;
    private byte[] pcmInputCache;

    public EchoCancellationAudioInputStream(AudioRecord audioRecord, TarsosDSPAudioFormat tarsosDSPAudioFormat) {
        super(audioRecord, tarsosDSPAudioFormat);
        aecm = new MobileAEC(null);
        aecm.setAecmMode(MobileAEC.AggressiveMode.MOST_AGGRESSIVE)
                .prepare();

        cacheSize = 320;
        pcmInputCache = new byte[cacheSize];
    }

    public int read(byte[] b, int off, int len) throws IOException {
        //int result = super.read(b, off, len);

        //OutputStream fout = new ByteArrayOutputStream(b.length);
        ByteBuffer outBuf = ByteBuffer.wrap(b);

        int bytesLeft = len;
        for (/* empty */;
                        ;
                        /* empty */) {
            int numToRead = min(bytesLeft, pcmInputCache.length);
            bytesLeft -= pcmInputCache.length;

            if(super.read(pcmInputCache, 0, numToRead) == -1) {
                break;
            }

            short[] aecTmpIn = new short[cacheSize / 2];
            short[] aecTmpOut = new short[cacheSize / 2];
            ByteBuffer.wrap(pcmInputCache).order(ByteOrder.LITTLE_ENDIAN)
                    .asShortBuffer().get(aecTmpIn);

            // aecm procession, for now the echo tail is hard-coded 10ms,
            // but you
            // should estimate it correctly each time you call
            // echoCancellation, otherwise aecm
            // cannot work.
            try {
                aecm.farendBuffer(aecTmpIn, cacheSize / 2);

                aecm.echoCancellation(aecTmpIn, null, aecTmpOut,
                        (short) (cacheSize / 2), (short) 10);
            } catch(Exception e) {
                throw new IOException(e);
            }

            // output
            byte[] aecBuf = new byte[cacheSize];
            ByteBuffer.wrap(aecBuf).order(ByteOrder.LITTLE_ENDIAN)
                    .asShortBuffer().put(aecTmpOut);

            outBuf.put(aecBuf);
        }

        return len-bytesLeft;
    }

    @Override
    public void close() throws IOException {
        aecm.close();
        super.close();
    }
}
