package speex;

public class EchoCanceller {

    static {
        System.loadLibrary("speex");
    }

    public native void open(int sampleRate, int bufSize, int totalSize);

    public native short[] process(short[] input_frame, short[] echo_frame);

    public native short[] capture(short[] input_frame);
    public native byte[] captureBytes(byte[] input_frame);

    public native void playback(short[] echo_frame);

    public native void close();
}
