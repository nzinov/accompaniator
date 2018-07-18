package accompaniator_team.playwithme;

import android.content.res.AssetManager;
import android.util.Log;

import org.jpmml.android.EvaluatorUtil;
import org.jpmml.evaluator.Evaluator;
import org.jpmml.evaluator.InputField;
import org.jpmml.evaluator.ModelEvaluator;
import org.tensorflow.contrib.android.TensorFlowInferenceInterface;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.ObjectInputStream;
import java.time.Instant;
import java.util.concurrent.LinkedBlockingQueue;

public class ChordPredictorThread extends Thread {
    private static final String TAG = "ChordPredictorThread";

    LinkedBlockingQueue<PlayerService.Chord> queueOut;
    LinkedBlockingQueue<PlayerService.Note> queueIn;
    TensorFlowInferenceInterface tensorflow;
    Instant predictionTime;
    Evaluator modelEvaluator = null;

    ChordPredictorThread(AssetManager assets) {
        queueOut = SingletonClass.getInstance().queueOut;
        queueIn = SingletonClass.getInstance().queueIn;

        //tensorflow = new TensorFlowInferenceInterface(assets, "NN_model.h5");

        try {
            modelEvaluator = loadSer("model.ser");
            Log.e(TAG, modelEvaluator.getSummary());
            Log.e(TAG, "Evaluator loaded");
            for(InputField inf: modelEvaluator.getInputFields()){
                Log.e(TAG, inf.getName().toString());
            }
        } catch(Exception e) {
            Log.e(TAG, "Evaluator not loaded", e);
        }

    }

    public Evaluator loadSer(String serName) throws Exception {
        AssetManager assetManager = SingletonClass.getInstance().context.getAssets();

        /*try(InputStream is = assetManager.open(serName)){
            Evaluator evaluator = org.jpmml.android.EvaluatorUtil.createEvaluator(is);
            return evaluator;
        }*/
        InputStream is = assetManager.open(serName);
        Evaluator evaluator = org.jpmml.android.EvaluatorUtil.createEvaluator(is);
        is.close();
        return evaluator;
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

            //modelEvaluator.evaluate()
            //note.number -= 12;
            PlayerService.Note[] notes = {note};
            predictedChord = new PlayerService.Chord(notes, 127, 128);
            //tensorflow.fetch()
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
