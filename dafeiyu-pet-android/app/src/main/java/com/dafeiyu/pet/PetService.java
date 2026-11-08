package com.dafeiyu.pet;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.provider.Settings;
import android.util.DisplayMetrics;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewConfiguration;
import android.view.WindowManager;
import android.widget.TextView;

import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;

/**
 * 悬浮窗本体：一个真正飘在所有应用上面的「大肥鱼」。
 */
public class PetService extends Service {

    public static final String ACTION_STOP = "com.dafeiyu.pet.action.STOP";
    public static final String ACTION_RESIZE = "com.dafeiyu.pet.action.RESIZE";
    public static volatile boolean isRunning = false;

    private static final float BASE_WIDTH_DP = 150f;

    private static final String CHANNEL_ID = "pet";
    private static final int NOTIF_ID = 1001;

    private static final String[] EXPRESSIONS = {
            "deyi", "bixin", "xia", "wenhao", "zhenjing", "haixiu", "ok", "piaole",
            "shuijiao", "tangping", "yun", "wuyu", "jiazai", "shengqi", "xianqi",
            "qiurao", "yaoqian", "ganfan", "zaoshanghao", "toukan", "maozhua",
            "buyao", "huachi", "jiaban"
    };

    private static final String[] LINES_IDLE = {
            "好无聊啊…要不要一起摸会儿鱼？",
            "点我干嘛，我又不会帮你写作业。",
            "这手机屏幕挺干净，适合躺平。",
            "要不要投喂一条小鱼干？",
            "困了…zzZ",
            "别看我，看路。",
            "今天也是努力（假装）的一天！",
            "我在这儿陪你呢。",
    };

    private static final String[] LINES_CLICK = {
            "诶！别戳我啦～",
            "痒痒的…你手好闲啊。",
            "再戳我就生气了哦。",
            "干嘛呀，人家在发呆。",
    };

    private static final String[] LINES_DRAG = {
            "哇——别甩我！",
            "放我下来！我晕了！",
            "喂喂喂，温柔一点嘛。",
    };

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Random random = new Random();
    private final Map<String, Bitmap> spriteCache = new HashMap<>();

    private WindowManager wm;
    private PetView petView;
    private TextView bubbleView;
    private WindowManager.LayoutParams lp;
    private WindowManager.LayoutParams bubbleLp;

    private int screenW;
    private int screenH;
    private int petWidth;

    private String expr = "deyi";
    private long exprUntil = 0;
    private long bubbleUntil = 0;

    private float downRawX;
    private float downRawY;
    private int downLpX;
    private int downLpY;
    private boolean moved;
    private boolean touching;
    private boolean longFired;
    private long lastTapTime = 0;
    private long downTime = 0;
    private int touchSlop;

    private float wanderVx = 0f;
    private long wanderUntil = 0;
    private long nextIdleAt = 0;
    private long bootTime = 0;

    private final Runnable ticker = new Runnable() {
        @Override
        public void run() {
            tick();
            handler.postDelayed(this, 33);
        }
    };

    private final Runnable longPress = new Runnable() {
        @Override
        public void run() {
            if (!moved) {
                longFired = true;
                randomExpression();
                say("换个表情给你看～", 2500);
            }
        }
    };

    private final Runnable singleTap = new Runnable() {
        @Override
        public void run() {
            onTap();
        }
    };

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        isRunning = true;
        bootTime = System.currentTimeMillis();
        nextIdleAt = bootTime + 6000;

        createChannel();
        startForeground(NOTIF_ID, buildNotification());

        if (!Settings.canDrawOverlays(this)) {
            stopSelf();
            return;
        }

        wm = (WindowManager) getSystemService(WINDOW_SERVICE);
        DisplayMetrics dm = new DisplayMetrics();
        wm.getDefaultDisplay().getMetrics(dm);
        screenW = dm.widthPixels;
        screenH = dm.heightPixels;
        touchSlop = ViewConfiguration.get(this).getScaledTouchSlop();
        petWidth = computePetWidth();

        showPet();
        say(greeting(), 4000);
        handler.postDelayed(ticker, 33);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) {
            stopSelf();
            return START_NOT_STICKY;
        }
        if (intent != null && ACTION_RESIZE.equals(intent.getAction())) {
            resizePet();
            return START_STICKY;
        }
        return START_STICKY;
    }

    /** 按设置里的比例算宽度，并限制不超过屏幕一半、不小于 60dp。 */
    private int computePetWidth() {
        float scale = getSharedPreferences("pet", MODE_PRIVATE).getFloat("size_scale", 1f);
        float density = getResources().getDisplayMetrics().density;
        int w = Math.round(BASE_WIDTH_DP * density * scale);
        int max = Math.round(screenW * 0.5f);
        int min = Math.round(60f * density);
        return Math.max(min, Math.min(w, max));
    }

    /** 运行中改大小：保持中心位置重新贴图。 */
    private void resizePet() {
        if (petView == null || lp == null) {
            return;
        }
        int old = petWidth;
        int now = computePetWidth();
        if (now == old) {
            return;
        }
        petWidth = now;
        lp.x = clampX(lp.x + (old - petWidth) / 2);
        lp.y = clampY(lp.y + (old - petWidth) / 4);
        petView.setSprite(loadSprite(expr), petWidth);
        lp.width = petWidth;
        lp.height = petView.totalHeight();
        try {
            wm.updateViewLayout(petView, lp);
        } catch (Exception ignored) {
        }
        updateBubblePosition();
        say("这样够小了吧？", 2000);
    }

    @Override
    public void onDestroy() {
        isRunning = false;
        handler.removeCallbacksAndMessages(null);
        if (wm != null) {
            if (petView != null) {
                try {
                    wm.removeView(petView);
                } catch (Exception ignored) {
                }
            }
            if (bubbleView != null) {
                try {
                    wm.removeView(bubbleView);
                } catch (Exception ignored) {
                }
            }
        }
        spriteCache.clear();
        super.onDestroy();
    }

    // ---------------------------------------------------------------- 窗口

    private int overlayType() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            return WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY;
        }
        return WindowManager.LayoutParams.TYPE_PHONE;
    }

    private void showPet() {
        petView = new PetView(this);
        Bitmap first = loadSprite(expr);
        if (first == null) {
            first = loadSprite("deyi");
        }
        petView.setSprite(first, petWidth);

        SharedPreferences sp = getSharedPreferences("pet", MODE_PRIVATE);
        int x = sp.getInt("x", Math.max(0, screenW - petWidth - Math.round(24 * getResources().getDisplayMetrics().density)));
        int y = sp.getInt("y", Math.round(screenH * 0.45f));

        lp = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                overlayType(),
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                        | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
                        | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT);
        lp.gravity = Gravity.TOP | Gravity.START;
        lp.x = x;
        lp.y = y;
        lp.width = petWidth;
        lp.height = petView.totalHeight();

        wm.addView(petView, lp);
        petView.setOnTouchListener(new View.OnTouchListener() {
            @Override
            public boolean onTouch(View v, MotionEvent event) {
                return handleTouch(event);
            }
        });
    }

    private boolean handleTouch(MotionEvent event) {
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                downRawX = event.getRawX();
                downRawY = event.getRawY();
                downLpX = lp.x;
                downLpY = lp.y;
                downTime = System.currentTimeMillis();
                moved = false;
                longFired = false;
                touching = true;
                handler.removeCallbacks(singleTap);
                handler.postDelayed(longPress, 650);
                return true;

            case MotionEvent.ACTION_MOVE: {
                float dx = event.getRawX() - downRawX;
                float dy = event.getRawY() - downRawY;
                if (!moved && (Math.abs(dx) > touchSlop || Math.abs(dy) > touchSlop)) {
                    moved = true;
                    handler.removeCallbacks(longPress);
                    setExpression("xia", 1200);
                }
                if (moved) {
                    lp.x = clampX(downLpX + (int) dx);
                    lp.y = clampY(downLpY + (int) dy);
                    try {
                        wm.updateViewLayout(petView, lp);
                    } catch (Exception ignored) {
                    }
                    updateBubblePosition();
                }
                return true;
            }

            case MotionEvent.ACTION_UP: {
                handler.removeCallbacks(longPress);
                touching = false;
                long now = System.currentTimeMillis();
                if (!moved && !longFired) {
                    if (now - lastTapTime < 320) {
                        handler.removeCallbacks(singleTap);
                        lastTapTime = 0;
                        setExpression("bixin", 2500);
                        say("最喜欢你了！", 2500);
                    } else {
                        lastTapTime = now;
                        handler.postDelayed(singleTap, 300);
                    }
                } else if (moved) {
                    say(pick(LINES_DRAG), 2200);
                    savePosition();
                    wanderVx = 0f;
                }
                return true;
            }

            case MotionEvent.ACTION_CANCEL:
                handler.removeCallbacks(longPress);
                touching = false;
                return true;
            default:
                return true;
        }
    }

    private int clampX(int x) {
        return Math.max(0, Math.min(x, screenW - petWidth));
    }

    private int clampY(int y) {
        return Math.max(0, Math.min(y, screenH - petView.totalHeight()));
    }

    private void savePosition() {
        getSharedPreferences("pet", MODE_PRIVATE).edit()
                .putInt("x", lp.x)
                .putInt("y", lp.y)
                .apply();
    }

    // ---------------------------------------------------------------- 气泡

    private void say(String text, long durationMs) {
        if (text == null || text.isEmpty()) {
            return;
        }
        if (bubbleView == null) {
            bubbleView = new TextView(this);
            bubbleView.setTextColor(0xFF1E293B);
            bubbleView.setTextSize(14f);
            bubbleView.setPadding(dp(14), dp(10), dp(14), dp(10));
            GradientDrawable bg = new GradientDrawable();
            bg.setColor(0xF7FFFFFF);
            bg.setCornerRadius(dp(14));
            bg.setStroke(dp(2), 0xFF2B3A67);
            bubbleView.setBackground(bg);
            bubbleView.setMaxWidth(dp(230));

            bubbleLp = new WindowManager.LayoutParams(
                    WindowManager.LayoutParams.WRAP_CONTENT,
                    WindowManager.LayoutParams.WRAP_CONTENT,
                    overlayType(),
                    WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                            | WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
                            | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                    PixelFormat.TRANSLUCENT);
            bubbleLp.gravity = Gravity.TOP | Gravity.START;
            try {
                wm.addView(bubbleView, bubbleLp);
            } catch (Exception e) {
                bubbleView = null;
                return;
            }
        }
        bubbleView.setText(text);
        bubbleView.setVisibility(View.VISIBLE);
        bubbleUntil = System.currentTimeMillis() + durationMs;
        updateBubblePosition();
    }

    private void updateBubblePosition() {
        if (bubbleView == null || bubbleLp == null || lp == null) {
            return;
        }
        bubbleView.post(new Runnable() {
            @Override
            public void run() {
                if (bubbleView == null || bubbleLp == null) {
                    return;
                }
                int bw = bubbleView.getWidth();
                int bh = bubbleView.getHeight();
                int x = lp.x + (petWidth - bw) / 2;
                int y = lp.y - bh - dp(6);
                bubbleLp.x = Math.max(dp(4), Math.min(x, screenW - bw - dp(4)));
                bubbleLp.y = Math.max(0, y);
                try {
                    wm.updateViewLayout(bubbleView, bubbleLp);
                } catch (Exception ignored) {
                }
            }
        });
    }

    // ---------------------------------------------------------------- 动画

    private void tick() {
        long now = System.currentTimeMillis();

        petView.setBob((int) (Math.sin((now - bootTime) / 480.0) * 5));

        if (exprUntil > 0 && now > exprUntil) {
            exprUntil = 0;
            setExpression("deyi", 0);
        }

        if (bubbleView != null && now > bubbleUntil) {
            bubbleView.setVisibility(View.GONE);
        }

        if (now > nextIdleAt) {
            nextIdleAt = now + 9000 + random.nextInt(14000);
            int roll = random.nextInt(100);
            if (roll < 45) {
                say(pick(LINES_IDLE), 4000);
            } else if (roll < 75) {
                randomExpression();
            } else if (roll < 90) {
                setExpression(random.nextBoolean() ? "shuijiao" : "tangping", 5000);
                say("摸鱼中，勿扰…", 4000);
            }
        }

        updateWander(now);
    }

    private void updateWander(long now) {
        if (touching) {
            return;
        }
        if (now > wanderUntil) {
            if (random.nextInt(100) < 18) {
                wanderVx = (random.nextBoolean() ? 1 : -1) * (0.8f + random.nextFloat());
                wanderUntil = now + 1200 + random.nextInt(1600);
            } else {
                wanderVx = 0f;
                wanderUntil = now + 4000 + random.nextInt(6000);
            }
        }
        if (wanderVx != 0f) {
            int nx = (int) (lp.x + wanderVx);
            if (nx < 0 || nx > screenW - petWidth) {
                wanderVx = -wanderVx;
            } else {
                lp.x = nx;
                try {
                    wm.updateViewLayout(petView, lp);
                } catch (Exception ignored) {
                }
                updateBubblePosition();
            }
        }
    }

    private void onTap() {
        randomExpression();
        say(pick(LINES_CLICK), 2600);
    }

    private void randomExpression() {
        setExpression(EXPRESSIONS[random.nextInt(EXPRESSIONS.length)], 2600);
    }

    private void setExpression(String name, long holdMs) {
        Bitmap bm = loadSprite(name);
        if (bm == null) {
            return;
        }
        expr = name;
        exprUntil = holdMs > 0 ? System.currentTimeMillis() + holdMs : 0;
        petView.setSprite(bm, petWidth);
        lp.height = petView.totalHeight();
        try {
            wm.updateViewLayout(petView, lp);
        } catch (Exception ignored) {
        }
    }

    private Bitmap loadSprite(String name) {
        Bitmap cached = spriteCache.get(name);
        if (cached != null) {
            return cached;
        }
        try {
            InputStream is = getAssets().open("sprites/" + name + ".png");
            Bitmap bm = BitmapFactory.decodeStream(is);
            is.close();
            if (bm != null) {
                spriteCache.put(name, bm);
            }
            return bm;
        } catch (Exception e) {
            return null;
        }
    }

    // ---------------------------------------------------------------- 杂项

    private String greeting() {
        int h = java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY);
        if (h >= 5 && h < 11) {
            return "早上好！今天也要元气满满～";
        } else if (h >= 11 && h < 14) {
            return "中午了，吃饭了没？";
        } else if (h >= 14 && h < 23) {
            return "我出来啦，陪你一会儿～";
        }
        return "这么晚还不睡？小心秃头。";
    }

    private String pick(String[] arr) {
        return arr[random.nextInt(arr.length)];
    }

    private int dp(float v) {
        return Math.round(getResources().getDisplayMetrics().density * v);
    }

    private void createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationManager nm = getSystemService(NotificationManager.class);
            if (nm != null && nm.getNotificationChannel(CHANNEL_ID) == null) {
                NotificationChannel ch = new NotificationChannel(
                        CHANNEL_ID, "桌宠运行中", NotificationManager.IMPORTANCE_LOW);
                ch.setDescription("大肥鱼正在你的屏幕上飘着");
                ch.setShowBadge(false);
                nm.createNotificationChannel(ch);
            }
        }
    }

    private Notification buildNotification() {
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pi = PendingIntent.getActivity(
                this, 0, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        Intent stop = new Intent(this, PetService.class).setAction(ACTION_STOP);
        PendingIntent ps = PendingIntent.getService(
                this, 1, stop, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        Notification.Builder b;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            b = new Notification.Builder(this, CHANNEL_ID);
        } else {
            b = new Notification.Builder(this);
        }
        b.setContentTitle("大肥鱼桌宠")
                .setContentText("她正在你的屏幕上陪着你")
                .setSmallIcon(android.R.drawable.ic_menu_gallery)
                .setContentIntent(pi)
                .addAction(0, "让她回去", ps)
                .setOngoing(true);
        return b.build();
    }
}
