package accompaniator_team.playwithme;

import android.content.res.AssetManager;

import org.tensorflow.contrib.android.TensorFlowInferenceInterface;

import java.time.Instant;
import java.util.concurrent.LinkedBlockingQueue;

public class ChordPredictorThread extends Thread {

    LinkedBlockingQueue<PlayerService.Chord> queueOut;
    LinkedBlockingQueue<PlayerService.Note> queueIn;
    TensorFlowInferenceInterface tensorflow;
    Instant predictionTime;

    ChordPredictorThread(AssetManager assets) {
        queueOut = SingletonClass.getInstance().queueOut;
        queueIn = SingletonClass.getInstance().queueIn;

        //tensorflow = new TensorFlowInferenceInterface(assets, "NN_model.h5");
    }

    private PlayerService.Chord tryPredict() {
        PlayerService.Note note;
        PlayerService.Chord predictedChord = null;

        do {
            note = queueIn.peek();
            if (note == null) {
                continue;
            }
            // TODO
            //tensorflow.feed();
            //note.number -= 12;
            PlayerService.Note[] notes = {note};
            predictedChord = new PlayerService.Chord(notes, 127, 128); //tensorflow.fetch()
        } while (note == null);

        return predictedChord;
        /*if (Instant.now().isAfter(predictionTime)) {
            return predictedChord;
        } else {
            return null;
        }*/
    }

    @Override
    public void run() {
        while (SingletonClass.getInstance().working.get()) {
            PlayerService.Chord chord = tryPredict();
            if (chord != null) {
                queueOut.offer(chord);
            }
        }
    }
}
