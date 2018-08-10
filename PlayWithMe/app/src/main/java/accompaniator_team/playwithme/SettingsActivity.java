package accompaniator_team.playwithme;

import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.view.WindowManager;

public class SettingsActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        setContentView(R.layout.activity_settings);

        getSupportFragmentManager().beginTransaction()
                // .replace(android.R.id.content, SettingsFragment())
                .replace(R.id.content, new SettingsFragment())
                .commit();
    }
}