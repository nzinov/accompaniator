package accompaniator_team.playwithme;

public class Chord {
    Note[] notes;
    int velocity;
    int duration;

    public Chord(Note[] notes, int velocity, int duration) {
        this.notes = notes;
        this.velocity = velocity;
        this.duration = duration;
    }
}
