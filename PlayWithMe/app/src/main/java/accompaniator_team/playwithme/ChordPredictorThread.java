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

        tensorflow = new TensorFlowInferenceInterface(assets, "NN_model.h5");
    }

    PlayerService.Chord tryPredict() {
        PlayerService.Note note;
        PlayerService.Chord predictedChord = null;

        while (true) {
            note = queueIn.peek();
            if (note == null) {
                break;
            }
            // TODO
            //tensorflow.feed();
            predictedChord = null; //tensorflow.fetch()
        }

        if (Instant.now().isAfter(predictionTime)) {
            return predictedChord;
        } else {
            return null;
        }
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
