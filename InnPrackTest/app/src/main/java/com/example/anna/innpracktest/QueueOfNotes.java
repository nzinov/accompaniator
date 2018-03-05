package com.example.anna.innpracktest;

import android.os.Parcel;
import android.os.Parcelable;
import android.util.Log;

import java.util.ArrayList;
import java.util.Arrays;

/**
 * Created by anna on 2018-03-04.
 */

public class QueueOfNotes implements Parcelable{
    private int capacity;
    private int size;
    //TODO private
    ArrayList<Note> notes;

    public QueueOfNotes() {
        capacity = MainActivity.MAXNOTESINTACT + 1;
        size = 0;
        notes = new ArrayList<>();
    }
    protected QueueOfNotes(Parcel in) {

        capacity = in.readInt();
        size = in.readInt();
        in.readTypedList(notes, Note.CREATOR);
    }

    public static final Creator<QueueOfNotes> CREATOR = new Creator<QueueOfNotes>() {
        @Override
        public QueueOfNotes createFromParcel(Parcel in) {
            return new QueueOfNotes(in);
        }

        @Override
        public QueueOfNotes[] newArray(int size) {
            return new QueueOfNotes[size];
        }
    };

    public void put(byte[] startEvent, byte[] finishEvent) {
        Event start = new Event(startEvent);
        Event finish = new Event(finishEvent);
        Log.e("QUEUE", "Adding events toi queue.");
        notes.add(new Note(start, finish));
    }

    public byte[] getStart(int pointer){
        return notes.get(pointer).start.bytes;
    }

    public byte[] getFinish(int pointer){
        Log.e("LOLOLO", Integer.toString(pointer));
        Log.e("HOHOHO", Integer.toString(notes.size()));
        return notes.get(pointer).finish.bytes;
    }

    @Override
    public int describeContents() {
        return 0;
    }

    @Override
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeInt(capacity);
        dest.writeInt(size);
        dest.writeTypedList(notes);
    }
}
