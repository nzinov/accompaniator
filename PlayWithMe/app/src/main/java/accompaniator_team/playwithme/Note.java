package accompaniator_team.playwithme;

import static java.lang.Math.log;
import static java.lang.Math.pow;
import static java.lang.Math.round;

public class Note {
    int number;

    public Note(int number) {
        this.number = number;
    }

    double toFrequency() {
        return NumToFreq(number);
    }

    static Note fromFrequency(float freq) {
        return new Note(FreqToNum(freq));
    }

    static int FreqToNum(float freq) {
        return (int)round(log(freq/440.0)/log(2)*12+69);
    }

    static float NumToFreq(int num) {
        return (float)pow(2, ((num - 69) / 12.))* 440;
    }
}
