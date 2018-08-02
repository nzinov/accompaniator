package accompaniator_team.playwithme;

import android.app.Activity;
import android.content.Context;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

class SingletonClass {
    private static final SingletonClass ourInstance = new SingletonClass();

    static SingletonClass getInstance() {
        return ourInstance;
    }

    public LinkedBlockingQueue<Chord> queueOut = new LinkedBlockingQueue<>();
    public LinkedBlockingQueue<Chord> queueIn = new LinkedBlockingQueue<>();
    public AtomicBoolean working = new AtomicBoolean(false);
    public AtomicBoolean finished = new AtomicBoolean(false);
    public AtomicInteger deadline;
    public Activity mainActivity; // TODO: make atomic
    public Context context;
    public CountDownLatch latch = new CountDownLatch(1);

    private SingletonClass() {
        //working = new AtomicBoolean(true);
    }
}
