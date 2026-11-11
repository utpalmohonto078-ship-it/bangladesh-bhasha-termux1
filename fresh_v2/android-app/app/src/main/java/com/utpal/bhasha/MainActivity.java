package com.utpal.bhasha;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.graphics.Typeface;
import android.view.ViewGroup;
import android.widget.*;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {

    private TextView status;
    private EditText editor;
    private TextView output;
    private Button runButton;

    private final ExecutorService executor =
            Executors.newSingleThreadExecutor();

    private final Handler mainHandler =
            new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(20, 24, 20, 20);

        TextView title = new TextView(this);
        title.setText("BANGLADESH BHASHA");
        title.setTextSize(24);
        title.setTypeface(null, Typeface.BOLD);
        root.addView(title);

        TextView version = new TextView(this);
        version.setText("ULTIMATE Android • 2.1.0");
        root.addView(version);

        status = new TextView(this);
        status.setText("Python runtime starting...");
        root.addView(status);

        editor = new EditText(this);
        editor.setGravity(48);
        editor.setTypeface(Typeface.MONOSPACE);
        editor.setTextSize(15);
        editor.setMinLines(7);
        editor.setHint("সংখ্যা x = 10\nদেখাও x");

        root.addView(editor, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1
        ));

        runButton = new Button(this);
        runButton.setText("RUN BHASHA");
        runButton.setEnabled(false);
        root.addView(runButton);

        output = new TextView(this);
        output.setText("Output will appear here.");
        output.setTextIsSelectable(true);
        output.setTextSize(18);
        output.setPadding(8, 18, 8, 8);
        root.addView(output);

        root.setOnApplyWindowInsetsListener((v, insets) -> {
            v.setPadding(
                20 + insets.getSystemWindowInsetLeft(),
                24 + insets.getSystemWindowInsetTop(),
                20 + insets.getSystemWindowInsetRight(),
                20 + insets.getSystemWindowInsetBottom());
            return insets;
        });

        setContentView(root);

        startRuntime();
        runButton.setOnClickListener(v -> executeBhasha());
    }

    private void startRuntime() {
        executor.execute(() -> {
            try {
                if (!Python.isStarted()) {
                    Python.start(
                        new AndroidPlatform(getApplicationContext())
                    );
                }

                String result = Python.getInstance()
                        .getModule("bhasha_android")
                        .callAttr("get_status").toString();

                mainHandler.post(() -> {
                    if (isFinishing() || isDestroyed()) return;

                    status.setText(result);

                    boolean ready =
                            result.contains("Original Compiler: CONNECTED")
                            && result.contains("Original Virtual Machine: CONNECTED");

                    runButton.setEnabled(ready);
                });

            } catch (Exception e) {
                mainHandler.post(() -> {
                    if (isFinishing() || isDestroyed()) return;
                    status.setText("Python startup error: " + e.getMessage());
                    runButton.setEnabled(false);
                });
            }
        });
    }

    private void executeBhasha() {
        String source = editor.getText().toString();

        runButton.setEnabled(false);
        output.setText("Executing BANGLADESH BHASHA...");

        executor.execute(() -> {
            String result;

            try {
                result = Python.getInstance()
                        .getModule("bhasha_android")
                        .callAttr("run_source", source).toString();

            } catch (Exception e) {
                result = "Runtime error: " + e.getMessage();
            }

            final String finalResult = result;

            mainHandler.post(() -> {
                if (isFinishing() || isDestroyed()) return;
                output.setText(finalResult);
                runButton.setEnabled(true);
            });
        });
    }

    @Override
    protected void onDestroy() {
        executor.shutdownNow();
        super.onDestroy();
    }
}
