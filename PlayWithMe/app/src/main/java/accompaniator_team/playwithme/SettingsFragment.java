package accompaniator_team.playwithme;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.support.v7.preference.ListPreference;
import android.support.v7.preference.Preference;
import android.support.v7.preference.PreferenceFragmentCompat;
import android.support.v7.preference.PreferenceManager;

public class SettingsFragment extends PreferenceFragmentCompat
        implements SharedPreferences.OnSharedPreferenceChangeListener {

    @Override
    public void onCreatePreferences(Bundle savedInstanceState, String rootKey) {
        addPreferencesFromResource(R.xml.preferences);

        ListPreference pref = (ListPreference) findPreference("pref_instrument");
        pref.setSummary(pref.getEntry());
    }

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
        if (key.equals("pref_instrument")) {
            ListPreference pref = (ListPreference) findPreference(key);
            pref.setSummary(pref.getEntry());
            /*SharedPreferences.Editor preferenceEditor = this.getPreferenceManager().getSharedPreferences().edit();
            preferenceEditor.putInt("pref_instrument_value", Integer.parseInt(pref.getValue()));
            preferenceEditor.apply();*/

            SingletonClass.getInstance().playerService.myStop();
            SingletonClass.getInstance().playerService.myStart();
        } else if (key.equals("pref_peakThreshold")
                || key.equals("pref_minimumInterOnsetInterval")
                || key.equals("pref_silenceThreshold")) {
            SingletonClass.getInstance().listenerService.myStop();
            SingletonClass.getInstance().listenerService.myStart();
        }

    }
}
