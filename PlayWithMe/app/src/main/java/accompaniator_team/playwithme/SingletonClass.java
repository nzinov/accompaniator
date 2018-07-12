package accompaniator_team.playwithme;

import java.util.concurrent.LinkedBlockingQueue;

class SingletonClass {
    private static final SingletonClass ourInstance = new SingletonClass();

    static SingletonClass getInstance() {
        return ourInstance;
    }

    public LinkedBlockingQueue<PlayerService.Chord> queueOut = new LinkedBlockingQueue<>();
    public LinkedBlockingQueue<PlayerService.Note> queueIn = new LinkedBlockingQueue<>();

    private SingletonClass() {
    }
}
