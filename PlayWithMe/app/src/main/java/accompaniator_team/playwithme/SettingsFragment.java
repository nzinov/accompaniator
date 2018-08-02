package accompaniator_team.playwithme;

import android.content.SharedPreferences;
//import android.support.v7.app.
import android.os.Bundle;
import android.support.v7.preference.SeekBarPreference;
import android.support.v7.preference.Preference;
import android.support.v7.preference.PreferenceFragmentCompat;

public class SettingsFragment extends PreferenceFragmentCompat
        implements SharedPreferences.OnSharedPreferenceChangeListener
{

    public static final String KEY_PREF_INSTRUMENT = "pref_Instrument";

    @Override
    public void onCreatePreferences(Bundle savedInstanceState, String rootKey) {
        //super.onCreate(savedInstanceState);
        addPreferencesFromResource(R.xml.preferences);
    }

    /*@Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {

        mListPreference = (ListPreference)  getPreferenceManager().findPreference("preference_key");
        mListPreference.setOnPreferenceChangeListener(new Preference.OnPreferenceChangeListener() {
            @Override
            public boolean onPreferenceChange(Preference preference, Object newValue) {
                // your code here
            }
        }

        return inflater.inflate(R.layout.fragment_settings, container, false);
    }*/

    @Override
    public void onResume() {
        super.onResume();
        getPreferenceScreen().getSharedPreferences()
                .registerOnSharedPreferenceChangeListener(this);
    }

    @Override
    public void onPause() {
        super.onPause();
        getPreferenceScreen().getSharedPreferences()
                .unregisterOnSharedPreferenceChangeListener(this);
    }

    public void onSharedPreferenceChanged(SharedPreferences sharedPreferences,
                                          String key) {
        if (key.equals(KEY_PREF_INSTRUMENT)) {
            Preference pref = findPreference(key);
            // TODO: name, not code!
            pref.setSummary("Code "+sharedPreferences.getString(key, ""));
        }
    }
}