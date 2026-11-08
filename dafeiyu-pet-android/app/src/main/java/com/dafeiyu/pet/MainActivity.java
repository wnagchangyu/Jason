package com.dafeiyu.pet;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {

    private TextView statusView;
    private Button startBtn;

    private static final float[] SIZES = {0.55f, 0.75f, 1.0f, 1.3f};
    private static final String[] SIZE_LABELS = {"迷你", "小", "标准", "大"};
    private final Button[] builtSizeButtons = new Button[4];

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(wrapScroll(buildLayout()));
        askNotificationPermission();
    }

    @SuppressWarnings("NewApi")
    private void askNotificationPermission() {
        if (Build.VERSION.SDK_INT >= 33) {
            if (checkSelfPermission("android.permission.POST_NOTIFICATIONS")
                    != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"}, 1);
            }
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        refreshStatus();
        refreshSizeButtons();
    }

    private int dp(float v) {
        return Math.round(getResources().getDisplayMetrics().density * v);
    }

    private View buildLayout() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setBackgroundColor(0xFF121830);
        root.setPadding(dp(28), dp(48), dp(28), dp(28));

        TextView title = new TextView(this);
        title.setText(R.string.title);
        title.setTextColor(Color.WHITE);
        title.setTextSize(28f);
        title.setGravity(Gravity.CENTER);
        root.addView(title);

        TextView sub = new TextView(this);
        sub.setText(R.string.subtitle);
        sub.setTextColor(0xFF9FB3D9);
        sub.setTextSize(14f);
        sub.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams subLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        subLp.topMargin = dp(10);
        root.addView(sub, subLp);

        statusView = new TextView(this);
        statusView.setTextColor(0xFFB9C7E6);
        statusView.setTextSize(13f);
        statusView.setGravity(Gravity.CENTER);
        statusView.setLineSpacing(dp(4), 1f);
        LinearLayout.LayoutParams stLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        stLp.topMargin = dp(36);
        root.addView(statusView, stLp);

        TextView sizeLabel = new TextView(this);
        sizeLabel.setText("大小");
        sizeLabel.setTextColor(0xFF9FB3D9);
        sizeLabel.setTextSize(13f);
        LinearLayout.LayoutParams slLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        slLp.topMargin = dp(22);
        root.addView(sizeLabel, slLp);

        LinearLayout sizeRow = new LinearLayout(this);
        sizeRow.setOrientation(LinearLayout.HORIZONTAL);
        LinearLayout.LayoutParams rowLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        rowLp.topMargin = dp(8);
        for (int i = 0; i < SIZE_LABELS.length; i++) {
            final int idx = i;
            Button b = new Button(this);
            b.setText(SIZE_LABELS[i]);
            b.setTextSize(14f);
            b.setTextColor(Color.WHITE);
            b.setAllCaps(false);
            b.setStateListAnimator(null);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, dp(46), 1f);
            if (i > 0) {
                lp.leftMargin = dp(8);
            }
            b.setOnClickListener(v -> setSize(idx));
            sizeRow.addView(b, lp);
            builtSizeButtons[i] = b;
        }
        root.addView(sizeRow, rowLp);
        refreshSizeButtons();

        Button permBtn = makeButton(getString(R.string.btn_permission), 0xFF2B3A67);
        LinearLayout.LayoutParams p1 = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(52));
        p1.topMargin = dp(28);
        root.addView(permBtn, p1);
        permBtn.setOnClickListener(v -> openOverlaySettings());

        startBtn = makeButton(getString(R.string.btn_start), 0xFF5B8DE6);
        LinearLayout.LayoutParams p2 = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(52));
        p2.topMargin = dp(14);
        root.addView(startBtn, p2);
        startBtn.setOnClickListener(v -> startPet());

        Button stopBtn = makeButton(getString(R.string.btn_stop), 0xFF3A4460);
        LinearLayout.LayoutParams p3 = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(52));
        p3.topMargin = dp(14);
        root.addView(stopBtn, p3);
        stopBtn.setOnClickListener(v -> {
            stopService(new Intent(this, PetService.class));
            Toast.makeText(this, "大肥鱼回去睡觉了", Toast.LENGTH_SHORT).show();
            refreshStatus();
        });

        TextView tip = new TextView(this);
        tip.setText("提示：拖动可以换位置，单击会理你，双击比心，长按换表情。\n"
                + "她需要「显示在其他应用上层」权限才能飘在桌面上。");
        tip.setTextColor(0xFF7488AC);
        tip.setTextSize(12f);
        tip.setLineSpacing(dp(3), 1f);
        LinearLayout.LayoutParams tipLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        tipLp.topMargin = dp(30);
        root.addView(tip, tipLp);

        return root;
    }

    private View wrapScroll(View content) {
        ScrollView sv = new ScrollView(this);
        sv.setBackgroundColor(0xFF121830);
        sv.setFillViewport(true);
        sv.addView(content);
        return sv;
    }

    private Button makeButton(String text, int color) {        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setTextSize(16f);
        b.setAllCaps(false);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(color);
        bg.setCornerRadius(dp(14));
        b.setBackground(bg);
        b.setStateListAnimator(null);
        return b;
    }

    private void setSize(int idx) {
        getSharedPreferences("pet", MODE_PRIVATE).edit()
                .putFloat("size_scale", SIZES[idx]).apply();
        refreshSizeButtons();
        if (PetService.isRunning) {
            Intent i = new Intent(this, PetService.class).setAction(PetService.ACTION_RESIZE);
            startService(i);
        }
    }

    private void refreshSizeButtons() {
        float cur = getSharedPreferences("pet", MODE_PRIVATE).getFloat("size_scale", 1f);
        int best = 0;
        for (int i = 1; i < SIZES.length; i++) {
            if (Math.abs(SIZES[i] - cur) < Math.abs(SIZES[best] - cur)) {
                best = i;
            }
        }
        int density = Math.round(getResources().getDisplayMetrics().density);
        for (int i = 0; i < builtSizeButtons.length; i++) {
            Button b = builtSizeButtons[i];
            if (b == null) {
                continue;
            }
            GradientDrawable bg = new GradientDrawable();
            bg.setColor(i == best ? 0xFF5B8DE6 : 0xFF2B3A67);
            bg.setCornerRadius(12 * density);
            b.setBackground(bg);
        }
    }

    private void openOverlaySettings() {
        Intent i = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:" + getPackageName()));
        try {
            startActivity(i);
        } catch (Exception e) {
            startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION));
        }
    }

    private void startPet() {
        if (!Settings.canDrawOverlays(this)) {
            Toast.makeText(this, "先开启悬浮窗权限哦", Toast.LENGTH_LONG).show();
            openOverlaySettings();
            return;
        }
        Intent svc = new Intent(this, PetService.class);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(svc);
        } else {
            startService(svc);
        }
        Toast.makeText(this, "大肥鱼出来啦～", Toast.LENGTH_SHORT).show();
        statusView.postDelayed(this::refreshStatus, 600);
    }

    private void refreshStatus() {
        boolean overlay = Settings.canDrawOverlays(this);
        boolean running = PetService.isRunning;
        StringBuilder sb = new StringBuilder();
        sb.append(overlay ? "悬浮窗权限：已开启 ✅" : "悬浮窗权限：未开启 ❌");
        sb.append("\n");
        sb.append(running ? "桌宠状态：正在陪伴你 🐋" : "桌宠状态：还在睡觉");
        statusView.setText(sb.toString());
        startBtn.setAlpha(running ? 0.55f : 1f);
    }
}
