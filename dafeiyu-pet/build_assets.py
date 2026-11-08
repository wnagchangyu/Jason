# -*- coding: utf-8 -*-
"""把表情包素材处理成桌宠用的透明 PNG。

输入：表情包图库里的 jpg（白底）
输出：assets/sprites/<name>.png（透明底、裁边、统一高度）
"""
import json
import os
import shutil
import sys
from collections import deque

from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_ROOT = r"D:\dsh-home\profiles\desktop\node_modules\dsh-meme\memes\dafeiyu-001\memes"
RAW_DIR = os.path.join(HERE, "assets", "raw")
SPRITE_DIR = os.path.join(HERE, "assets", "sprites")

SPRITE_HEIGHT = 420  # 先做高清，运行时再按缩放比缩放


def flood_background(img):
    """从四边向内填充近似白/近纯色背景，返回 alpha 掩码图（255=前景）。"""
    from PIL import ImageDraw

    work = img.convert("RGB").copy()
    marker = (1, 2, 3)  # 罕见的哨兵色
    w, h = work.size
    seeds = []
    for x in range(0, w, 3):
        seeds.append((x, 0))
        seeds.append((x, h - 1))
    for y in range(0, h, 3):
        seeds.append((0, y))
        seeds.append((w - 1, y))

    for seed in seeds:
        px = work.getpixel(seed)
        if px == marker:
            continue
        ImageDraw.floodfill(work, seed, marker, thresh=42)

    mask = Image.new("L", (w, h), 255)
    mp = mask.load()
    wp = work.load()
    for y in range(h):
        for x in range(w):
            if wp[x, y] == marker:
                mp[x, y] = 0
    return mask


def largest_component(mask):
    """只保留最大连通前景（去掉散落的星星、特效符号）。"""
    w, h = mask.size
    px = mask.load()
    seen = bytearray(w * h)
    best = []
    for y in range(h):
        for x in range(w):
            i = y * w + x
            if seen[i] or px[x, y] == 0:
                continue
            q = deque([(x, y)])
            seen[i] = 1
            comp = []
            while q:
                cx, cy = q.popleft()
                comp.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h:
                        j = ny * w + nx
                        if not seen[j] and px[nx, ny] != 0:
                            seen[j] = 1
                            q.append((nx, ny))
            if len(comp) > len(best):
                best = comp

    out = Image.new("L", (w, h), 0)
    op = out.load()
    for x, y in best:
        op[x, y] = 255
    return out


def process(path, name):
    img = Image.open(path)
    rgba = img.convert("RGBA")
    mask = flood_background(img)
    # 保留最大主体
    big = largest_component(mask)
    # 只用最大的那份，但把内部的洞补回来（围裙、眼睛等白色区域）
    inner = Image.new("L", mask.size, 0)
    # 最大连通前景内部的白色细节：用「填洞」近似——先膨胀小的再相交
    big = big.filter(ImageFilter.MaxFilter(3))
    inner.paste(big)

    # 边缘抗锯齿：轻微模糊 alpha
    alpha = inner.filter(ImageFilter.GaussianBlur(0.7))

    rgba.putalpha(alpha)
    bbox = alpha.getbbox()
    if bbox:
        rgba = rgba.crop(bbox)

    # 统一高度
    w, h = rgba.size
    scale = SPRITE_HEIGHT / h
    rgba = rgba.resize((max(1, int(w * scale)), SPRITE_HEIGHT), Image.LANCZOS)

    out = os.path.join(SPRITE_DIR, name + ".png")
    rgba.save(out)
    return out, rgba.size


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(SPRITE_DIR, exist_ok=True)
    files = []
    for root, _dirs, names in os.walk(SRC_ROOT):
        for n in names:
            if n.lower().endswith(".jpg"):
                files.append(os.path.join(root, n))
    files.sort()

    manifest = {}
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        shutil.copyfile(path, os.path.join(RAW_DIR, os.path.basename(path)))
        out, size = process(path, name)
        manifest[name] = {"file": os.path.basename(out), "size": size, "category": os.path.basename(os.path.dirname(path))}
        print(f"ok {name:16s} {size[0]}x{size[1]}")

    with open(os.path.join(SPRITE_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"total {len(manifest)}")


if __name__ == "__main__":
    main()
