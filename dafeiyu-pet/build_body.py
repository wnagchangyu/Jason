# -*- coding: utf-8 -*-
"""从角色设定图里切出正面全身，做成桌宠本体。

来源：assets/source/character_sheet.jpg（三视图 + 细节）
输出：assets/full/body.png（透明、760 高）
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SHEET = os.path.join(HERE, "assets", "source", "character_sheet.jpg")
OUT = os.path.join(HERE, "assets", "full")
# 正面视图在左上角，稍微收一点避开右边的侧视图
CROP = (6, 4, 542, 636)
HEIGHT = 760


def cutout(img):
    work = img.convert("RGB").copy()
    marker = (1, 2, 3)
    w, h = work.size
    seeds = [(x, 0) for x in range(0, w, 2)] + [(x, h - 1) for x in range(0, w, 2)]
    seeds += [(0, y) for y in range(0, h, 2)] + [(w - 1, y) for y in range(0, h, 2)]
    for s in seeds:
        if work.getpixel(s) == marker:
            continue
        ImageDraw.floodfill(work, s, marker, thresh=40)

    a = np.array(work)
    mask = ~np.all(a == np.array(marker), axis=2)

    # 只保留最大连通块，顺手丢掉右边的侧视图碎片和脚下阴影
    from collections import deque
    seen = np.zeros((h, w), bool)
    best = []
    for y in range(h):
        for x in range(w):
            if seen[y, x] or not mask[y, x]:
                continue
            q = deque([(x, y)])
            seen[y, x] = True
            comp = []
            while q:
                cx, cy = q.popleft()
                comp.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny, nx] and mask[ny, nx]:
                        seen[ny, nx] = True
                        q.append((nx, ny))
            if len(comp) > len(best):
                best = comp

    m = Image.new("L", (w, h), 0)
    px = m.load()
    for x, y in best:
        px[x, y] = 255
    return m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))


def main():
    os.makedirs(OUT, exist_ok=True)
    sheet = Image.open(SHEET).convert("RGB")
    front = sheet.crop(CROP)
    full = front.convert("RGBA")
    full.putalpha(cutout(front))
    full = full.crop(full.getchannel("A").getbbox())
    w, h = full.size
    full = full.resize((int(w * HEIGHT / h), HEIGHT), Image.LANCZOS)
    full.save(os.path.join(OUT, "body.png"))
    print("body.png", full.size)


if __name__ == "__main__":
    main()
