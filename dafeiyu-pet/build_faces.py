# -*- coding: utf-8 -*-
"""把 24 张半身表情的「五官」换到全身立绘上，生成一整套全身表情。

做法：
  1. 半身图按身高比例裁出脸部框（眼睛+嘴）
  2. 等比缩放到全身图的脸部框，羽化边缘再贴上去
  3. 只保留效果干净的几张（姿态太偏的会错位，直接跳过）

输出：assets/full/expressions/<name>.png
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
BODY = os.path.join(HERE, "assets", "full", "body.png")
HEAD_DIR = os.path.join(HERE, "assets", "sprites")
OUT = os.path.join(HERE, "assets", "full", "expressions")

# 全身图的脸部框（按网格量出来的）
FACE_BODY = (200, 240, 440, 380)

# 逐张手工量的脸部框（左, 上, 右, 下），比自动识别准
FACE_SRC = {
    "deyi": (120, 150, 310, 275),      # 开心笑
    "shengqi": (120, 160, 305, 285),   # 生气
    "haixiu": (170, 170, 340, 300),    # 害羞
    "shuijiao": (125, 160, 295, 290),  # 睡着
    "wenhao": (125, 145, 315, 275),    # 疑惑
    "bixin": (125, 140, 335, 275),     # 比心
}
GOOD = list(FACE_SRC.keys())


def face_box(img):
    """半身图的脸部框：高度比例固定，水平居中于内容。"""
    a = np.array(img)[:, :, 3]
    ys, xs = np.where(a > 30)
    cx = int((xs.min() + xs.max()) / 2)
    h = img.height
    w = int(h * 0.34)
    th = int(h * 0.26)
    top = int(h * 0.355)
    return cx - w // 2, top, cx + w // 2, top + th


def compose(head, body, box=None):
    x0, y0, x1, y1 = FACE_BODY
    bw, bh = x1 - x0, y1 - y0
    fx0, fy0, fx1, fy1 = box if box else face_box(head)
    face = head.crop((fx0, fy0, fx1, fy1))

    s = bw / face.width
    face = face.resize((bw, max(1, int(face.height * s))), Image.LANCZOS)
    if face.height < bh:
        s2 = bh / (fy1 - fy0)
        face = head.crop((fx0, fy0, fx1, fy1)).resize(
            (max(1, int((fx1 - fx0) * s2)), bh), Image.LANCZOS)

    mask = Image.new("L", face.size, 0)
    ImageDraw.Draw(mask).ellipse([4, 4, face.width - 4, face.height - 4], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(5))

    out = body.copy()
    out.paste(face, (x0 + (bw - face.width) // 2, y0 + (bh - face.height) // 2), mask)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    body = Image.open(BODY).convert("RGBA")
    made = 0
    for name in GOOD:
        p = os.path.join(HEAD_DIR, name + ".png")
        if not os.path.exists(p):
            continue
        head = Image.open(p).convert("RGBA")
        compose(head, body, FACE_SRC.get(name)).save(os.path.join(OUT, name + ".png"))
        made += 1
    print("expressions:", made)


if __name__ == "__main__":
    main()
