package com.example.anna.innpracktest;

import java.util.ArrayList;

/**
 * Created by sun on 06.03.18.
 */

public class NoteStan {
    public class Note{
        int times;
        String nameNote;
        public Note(String name) {
            times = 1;
            nameNote = name;
        }
        public String toString(){
            return Integer.toString(times) + "x " + nameNote + "|";
        }
        void addTimes(int time){
            times += time;
        }
    }

    public ArrayList<Note> stan = new ArrayList<Note>();



    public void addNote(String nameNowNote) {
        if (!stan.isEmpty() && stan.get(stan.size() - 1).nameNote == nameNowNote) {
            stan.get(stan.size() - 1).addTimes(1);
        } else {
            stan.add(new Note(nameNowNote));
        }
    }
    public String toString(){
        String result = "";
        ArrayList<Note> subStan = new ArrayList<Note>();
        for (Note note:stan) {
            if (!subStan.isEmpty() && subStan.get(subStan.size() - 1).nameNote == note.nameNote) {
                subStan.get(subStan.size() - 1).addTimes(note.times);
            } else {
                subStan.add(note);
            }
        }
        stan = subStan;
        for (Note note :stan){
            result = result + note.toString();
        }
        return result;
    }
}
