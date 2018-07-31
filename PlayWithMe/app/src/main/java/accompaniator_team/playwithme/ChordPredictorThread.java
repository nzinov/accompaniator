package accompaniator_team.playwithme;

import android.content.Context;
import android.content.res.AssetManager;
import android.util.Log;

import org.dmg.pmml.PMML;
import org.jpmml.evaluator.Evaluator;
import org.jpmml.evaluator.InputField;
import org.jpmml.evaluator.ModelEvaluator;
import org.jpmml.evaluator.ModelEvaluatorFactory;
import org.nustaq.serialization.FSTObjectInput;

import java.io.IOException;
import java.io.InputStream;
import java.io.Serializable;
import java.time.Instant;
import java.util.concurrent.LinkedBlockingQueue;

public class ChordPredictorThread extends Thread {
    private static final String TAG = "ChordPredictorThread";

    private LinkedBlockingQueue<Chord> queueOut;
    private LinkedBlockingQueue<Chord> queueIn;
    //TensorFlowInferenceInterface tensorflow;
    Instant predictionTime;
    private Evaluator modelEvaluator = null;
    private GuiLogger guiLog;

    int cntIn = 0;
    int cntOut = 0;

    ChordPredictorThread(Context context, AssetManager assets) {
        guiLog = new GuiLogger(context);
        queueOut = SingletonClass.getInstance().queueOut;
        queueIn = SingletonClass.getInstance().queueIn;

        //tensorflow = new TensorFlowInferenceInterface(assets, "NN_model.h5");

        /*try {
            modelEvaluator = (Evaluator)loadSer("model_fst.ser");
            Log.e(TAG, modelEvaluator.getSummary());
            Log.e(TAG, "Evaluator loaded");
            for(InputField inf: modelEvaluator.getInputFields()){
                Log.e(TAG, inf.getName().toString());
            }
        } catch(Exception e) {

            Log.e(TAG, "Evaluator not loaded", e);
        }*/

    }

    private Evaluator loadSer(String serName) throws Exception {
        AssetManager assetManager = SingletonClass.getInstance().context.getAssets();

        /*try(InputStream is = assetManager.open(serName)){
            Evaluator evaluator = org.jpmml.android.EvaluatorUtil.createEvaluator(is);
            return evaluator;
        }*/
        InputStream is = assetManager.open(serName);
        PMML pmml = (PMML)myReadMethod(is);
        ModelEvaluatorFactory modelEvaluatorFactory = ModelEvaluatorFactory.newInstance();
        ModelEvaluator<?> evaluator = modelEvaluatorFactory.newModelEvaluator(pmml);
        evaluator.verify();
        is.close();
        return evaluator;
    }

    private Object myReadMethod(InputStream stream) throws IOException, ClassNotFoundException
    {
        FSTObjectInput in = new FSTObjectInput(stream);
        Object result = (Object)in.readObject();
        in.close(); // required !
        return result;
    }

    private Chord tryPredict() {
        Chord chord;
        Note note;
        Chord predictedChord = null;

        try {
            do {
                chord = queueIn.take();
                note = chord.notes[0];

                if (note == null) {
                    continue;
                }
                // TODO

                //tensorflow.feed();

                //modelEvaluator.evaluate()
                //note.number -= 12;
                Note[] notes = {note};
                predictedChord = new Chord(notes, 127, 128);
                //tensorflow.fetch()
            } while (note == null);

            return predictedChord;
        } catch (InterruptedException e) {
            Log.e(TAG, "Predictor interrupted", e);
        }
        /*if (Instant.now().isAfter(predictionTime)) {
            return predictedChord;
        } else {
            return null;
        }*/
        return null;
    }

    @Override
    public void run() {
        while (SingletonClass.getInstance().working.get()) {
            Chord chord = tryPredict();
            if (chord != null) {
                ++cntOut;
                MainActivity.GuiMessage l = (Serializable & MainActivity.GuiMessage) (MainActivity a) -> {
                    String message = String.format("%d Note %d in queue",cntOut, chord.notes[0].number);
                    a.predictorText.setText(message);
                };
                guiLog.sendResult(l);
                queueOut.offer(chord);
            }
        }
    }
}
