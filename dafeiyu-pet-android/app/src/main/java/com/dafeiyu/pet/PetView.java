package com.dafeiyu.pet;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.View;

/**
 * 只负责画：把当前表情的立绘画在 View 上，并带一点点上下浮动。
 */
public class PetView extends View {

    public static final int BOB_MARGIN = 10;

    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
    private Bitmap bitmap;
    private int bob = 0;

    public PetView(Context context) {
        super(context);
    }

    public void setSprite(Bitmap src, int targetWidth) {
        if (src == null) {
            return;
        }
        int w = Math.max(1, targetWidth);
        int h = Math.max(1, Math.round(src.getHeight() * (w / (float) src.getWidth())));
        bitmap = Bitmap.createScaledBitmap(src, w, h, true);
        invalidate();
    }

    public int contentWidth() {
        return bitmap == null ? 0 : bitmap.getWidth();
    }

    public int contentHeight() {
        return bitmap == null ? 0 : bitmap.getHeight();
    }

    public int totalHeight() {
        return contentHeight() + BOB_MARGIN * 2;
    }

    public void setBob(int value) {
        if (bob != value) {
            bob = value;
            invalidate();
        }
    }

    @Override
    protected void onDraw(Canvas canvas) {
        if (bitmap != null) {
            canvas.drawBitmap(bitmap, 0f, (float) (BOB_MARGIN + bob), paint);
        }
    }

    /** 这个点是不是落在有像素的地方（用来判断戳到了她）。 */
    public boolean isOpaqueAt(float x, float y) {
        if (bitmap == null) {
            return false;
        }
        int px = (int) x;
        int py = (int) (y - BOB_MARGIN - bob);
        if (px < 0 || py < 0 || px >= bitmap.getWidth() || py >= bitmap.getHeight()) {
            return false;
        }
        return Color.alpha(bitmap.getPixel(px, py)) > 24;
    }
}
