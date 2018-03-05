package com.example.anna.innpracktest;

import android.os.Parcel;
import android.os.Parcelable;

/**
 * Created by anna on 2018-03-04.
 */

public class Event implements Parcelable {

    final byte[] bytes;

    public Event(){
        this.bytes = MainActivity.endEvent;
    }

    public Event(byte[] bytes) {
        this.bytes = bytes;
    }

    protected Event(Parcel in) {
        int size = in.readInt();
        this.bytes = new byte[size];
        in.readByteArray(this.bytes);
    }

    public static final Creator<Event> CREATOR = new Creator<Event>() {
        @Override
        public Event createFromParcel(Parcel in) {
            return new Event(in);
        }

        @Override
        public Event[] newArray(int size) {
            return new Event[size];
        }
    };

    @Override
    public int describeContents() {
        return 0;
    }

    @Override
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeInt(bytes.length);
        dest.writeByteArray(bytes);
    }
}
