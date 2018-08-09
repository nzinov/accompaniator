package accompaniator_team.playwithme;

import android.content.Context;
import android.content.res.TypedArray;
import android.os.Parcel;
import android.os.Parcelable;
import android.support.v7.preference.Preference;
import android.support.v7.preference.PreferenceViewHolder;
import android.util.AttributeSet;
import android.util.Log;
import android.view.KeyEvent;
import android.view.View;
import android.widget.SeekBar;
import android.widget.TextView;

// Copied SeekBarPreference from android.support.v7.preference and modified for floats.
public class FloatSeekBarPreference extends Preference {
    private static final String TAG = "FloatSeekBarPreference";

    private float mSeekBarValue;
    private float mMin;
    private float mMax;
    private float mSeekBarIncrement;
    private int mNumPositions;

    private boolean mTrackingTouch;
    private SeekBar mSeekBar;
    private TextView mSeekBarValueTextView;
    private boolean mAdjustable;
    private boolean mShowSeekBarValue;
    private SeekBar.OnSeekBarChangeListener mSeekBarChangeListener;
    private View.OnKeyListener mSeekBarKeyListener;

    public FloatSeekBarPreference(Context context, AttributeSet attrs, int defStyleAttr, int defStyleRes) {
        super(context, attrs, defStyleAttr, defStyleRes);
        this.mSeekBarChangeListener = new SeekBar.OnSeekBarChangeListener() {
            public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                if (fromUser && !FloatSeekBarPreference.this.mTrackingTouch) {
                    FloatSeekBarPreference.this.syncValueInternal(seekBar);
                }

            }

            public void onStartTrackingTouch(SeekBar seekBar) {
                FloatSeekBarPreference.this.mTrackingTouch = true;
            }

            public void onStopTrackingTouch(SeekBar seekBar) {
                FloatSeekBarPreference.this.mTrackingTouch = false;
                if (internalToFloat(seekBar.getProgress()) != FloatSeekBarPreference.this.mSeekBarValue) {
                    FloatSeekBarPreference.this.syncValueInternal(seekBar);
                }

            }
        };
        this.mSeekBarKeyListener = new View.OnKeyListener() {
            public boolean onKey(View v, int keyCode, KeyEvent event) {
                if (event.getAction() != 0) {
                    return false;
                } else if (!FloatSeekBarPreference.this.mAdjustable && (keyCode == 21 || keyCode == 22)) {
                    return false;
                } else if (keyCode != 23 && keyCode != 66) {
                    if (FloatSeekBarPreference.this.mSeekBar == null) {
                        Log.e("SeekBarPreference", "SeekBar view is null and hence cannot be adjusted.");
                        return false;
                    } else {
                        return FloatSeekBarPreference.this.mSeekBar.onKeyDown(keyCode, event);
                    }
                } else {
                    return false;
                }
            }
        };
        TypedArray a = context.obtainStyledAttributes(attrs, R.styleable.FloatSeekBarPreference, defStyleAttr, defStyleRes);
        this.mMin = a.getFloat(R.styleable.FloatSeekBarPreference_min, 0);
        this.setMax(a.getFloat(R.styleable.FloatSeekBarPreference_max, 100));
        this.setSeekBarIncrement(a.getFloat(R.styleable.FloatSeekBarPreference_increment, 1));
        this.mAdjustable = a.getBoolean(R.styleable.FloatSeekBarPreference_adjustable, true);
        this.mShowSeekBarValue = a.getBoolean(R.styleable.FloatSeekBarPreference_showSeekBarValue, true);
        a.recycle();
    }

    public FloatSeekBarPreference(Context context, AttributeSet attrs, int defStyleAttr) {
        this(context, attrs, defStyleAttr, 0);
    }

    public FloatSeekBarPreference(Context context, AttributeSet attrs) {
        this(context, attrs,0);
    }

    public FloatSeekBarPreference(Context context) {
        this(context, (AttributeSet)null);
    }

    private int floatToInternal(float val) {
        return Math.round((val-mMin)/(mMax-mMin)*mNumPositions);
    }

    private float internalToFloat(int val) {
        return mMin+val*mSeekBarIncrement;
    }

    public void onBindViewHolder(PreferenceViewHolder view) {
        super.onBindViewHolder(view);

        mNumPositions = Math.round((mMax-mMin)/(float)mSeekBarIncrement);

        view.itemView.setOnKeyListener(this.mSeekBarKeyListener);
        this.mSeekBar = (SeekBar)view.findViewById(R.id.seekbar);
        this.mSeekBarValueTextView = (TextView)view.findViewById(R.id.seekbar_value);
        if (this.mShowSeekBarValue) {
            this.mSeekBarValueTextView.setVisibility(View.VISIBLE);
        } else {
            this.mSeekBarValueTextView.setVisibility(View.GONE);
            this.mSeekBarValueTextView = null;
        }

        if (this.mSeekBar == null) {
            Log.e("SeekBarPreference", "SeekBar view is null in onBindViewHolder.");
        } else {
            this.mSeekBar.setOnSeekBarChangeListener(this.mSeekBarChangeListener);
            this.mSeekBar.setMax(mNumPositions); //this.mMax - this.mMin
            this.mSeekBar.setKeyProgressIncrement(1);

            this.mSeekBar.setProgress(floatToInternal(mSeekBarValue)); //this.mSeekBarValue - this.mMin
            if (this.mSeekBarValueTextView != null) {
                this.mSeekBarValueTextView.setText(String.valueOf(this.mSeekBarValue));
            }

            this.mSeekBar.setEnabled(this.isEnabled());
        }
    }

    protected void onSetInitialValue(boolean restoreValue, Object defaultValue) {
        this.setValue(floatToInternal(restoreValue ? this.getPersistedFloat(this.mSeekBarValue) : (Float)defaultValue));
    }

    protected Object onGetDefaultValue(TypedArray a, int index) {
        return a.getInt(index, 0);
    }

    public void setMin(float min) {
        if (min > this.mMax) {
            min = this.mMax;
        }

        if (min != this.mMin) {
            this.mMin = min;
            this.notifyChanged();
        }

    }

    public float getMin() {
        return this.mMin;
    }

    public final void setMax(float max) {
        if (max < this.mMin) {
            max = this.mMin;
        }

        if (max != this.mMax) {
            this.mMax = max;
            this.notifyChanged();
        }

    }

    public final float getSeekBarIncrement() {
        return this.mSeekBarIncrement;
    }

    public final void setSeekBarIncrement(float seekBarIncrement) {
        if (seekBarIncrement != this.mSeekBarIncrement) {
            this.mSeekBarIncrement = Math.min(this.mMax - this.mMin, Math.abs(seekBarIncrement));
            this.notifyChanged();
        }
    }

    public float getMax() {
        return this.mMax;
    }

    public void setAdjustable(boolean adjustable) {
        this.mAdjustable = adjustable;
    }

    public boolean isAdjustable() {
        return this.mAdjustable;
    }

    public void setValue(int seekBarValue) {
        this.setValueInternal(seekBarValue, true);
    }

    private void setValueInternal(float seekBarValue, boolean notifyChanged) {
        if (seekBarValue < this.mMin) {
            seekBarValue = this.mMin;
        }

        if (seekBarValue > this.mMax) {
            seekBarValue = this.mMax;
        }

        if (seekBarValue != this.mSeekBarValue) {
            this.mSeekBarValue = seekBarValue;
            if (this.mSeekBarValueTextView != null) {
                this.mSeekBarValueTextView.setText(String.valueOf(this.mSeekBarValue));
            }

            this.persistFloat(seekBarValue);
            if (notifyChanged) {
                this.notifyChanged();
            }
        }

    }

    public float getValue() {
        return this.mSeekBarValue;
    }

    private void syncValueInternal(SeekBar seekBar) {
        float seekBarValue = internalToFloat(seekBar.getProgress());
        if (seekBarValue != this.mSeekBarValue) {
            if (this.callChangeListener(seekBarValue)) {
                this.setValueInternal(seekBarValue, false);
            } else {
                seekBar.setProgress(floatToInternal(mSeekBarValue)); //this.mSeekBarValue - this.mMin
            }
        }

    }

    protected Parcelable onSaveInstanceState() {
        Parcelable superState = super.onSaveInstanceState();
        if (this.isPersistent()) {
            return superState;
        } else {
            FloatSeekBarPreference.SavedState myState = new FloatSeekBarPreference.SavedState(superState);
            myState.seekBarValue = this.mSeekBarValue;
            myState.min = this.mMin;
            myState.max = this.mMax;
            return myState;
        }
    }

    protected void onRestoreInstanceState(Parcelable state) {
        if (!state.getClass().equals(FloatSeekBarPreference.SavedState.class)) {
            super.onRestoreInstanceState(state);
        } else {
            FloatSeekBarPreference.SavedState myState = (FloatSeekBarPreference.SavedState)state;
            super.onRestoreInstanceState(myState.getSuperState());
            this.mSeekBarValue = myState.seekBarValue;
            this.mMin = myState.min;
            this.mMax = myState.max;
            this.notifyChanged();
        }
    }

    private static class SavedState extends BaseSavedState {
        float seekBarValue;
        float min;
        float max;
        public static final Creator<FloatSeekBarPreference.SavedState> CREATOR = new Creator<FloatSeekBarPreference.SavedState>() {
            public FloatSeekBarPreference.SavedState createFromParcel(Parcel in) {
                return new FloatSeekBarPreference.SavedState(in);
            }

            public FloatSeekBarPreference.SavedState[] newArray(int size) {
                return new FloatSeekBarPreference.SavedState[size];
            }
        };

        public SavedState(Parcel source) {
            super(source);
            this.seekBarValue = source.readInt();
            this.min = source.readInt();
            this.max = source.readInt();
        }

        public void writeToParcel(Parcel dest, int flags) {
            super.writeToParcel(dest, flags);
            dest.writeFloat(this.seekBarValue);
            dest.writeFloat(this.min);
            dest.writeFloat(this.max);
        }

        public SavedState(Parcelable superState) {
            super(superState);
        }
    }
}
