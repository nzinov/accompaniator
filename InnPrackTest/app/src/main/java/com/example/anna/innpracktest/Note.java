package com.example.anna.innpracktest;

import android.os.Parcel;
import android.os.Parcelable;

/**
 * Created by anna on 2018-03-04.
 */

public class Note implements Parcelable {

    final Event start;
    final Event finish;

    Note(){
        this.start = new Event();
        this.finish = new Event();
    }

    Note(Event start, Event finish) {
        this.start = start;
        this.finish = finish;
    }

    protected Note(Parcel in) {
        this.start = in.readParcelable(Event.class.getClassLoader());
        this.finish = in.readParcelable(Event.class.getClassLoader());
    }

    public static final Creator<Note> CREATOR = new Creator<Note>() {
        @Override
        public Note createFromParcel(Parcel in) {
            return new Note(in);
        }

        @Override
        public Note[] newArray(int size) {
            return new Note[size];
        }
    };

    @Override
    public int describeContents() {
        return 0;
    }

    @Override
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeParcelable(start, 0);
        dest.writeParcelable(finish, 0);
    }
}
