# -*- coding: utf-8 -*-
"""大肥鱼桌宠 · Dafeiyu Desktop Pet

纯 Python + Win32 分层窗口实现：真·逐像素透明的置顶桌面宠物。
- 拖动 / 单击互动 / 右键菜单
- 透明区域点击穿透
- 待机呼吸浮动、随机说话、随机走动、按时间问候
"""
import ctypes
import ctypes.wintypes as wt
import json
import math
import os
import random
import sys
import threading
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SPRITE_DIR = os.path.join(HERE, "assets", "sprites")
FULL_DIR = os.path.join(HERE, "assets", "full")
CONFIG_DIR = os.path.join(os.environ.get("APPDATA", HERE), "dafeiyu-pet")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM)

WS_POPUP = 0x80000000
WS_EX_LAYERED = 0x00080000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

WM_DESTROY = 0x0002
WM_NCHITTEST = 0x0084
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP = 0x0205
WM_MOUSEMOVE = 0x0200
WM_NULL = 0x0000

HTTRANSPARENT = -1
HTCLIENT = 1

ULW_ALPHA = 0x00000002
AC_SRC_OVER = 0x00
AC_SRC_ALPHA = 0x01

TPM_LEFTALIGN = 0x0000
TPM_RIGHTBUTTON = 0x0002
TPM_RETURNCMD = 0x0100
TPM_BOTTOMALIGN = 0x0020
TPM_NONOTIFY = 0x0080

DIB_RGB_COLORS = 0
BI_RGB = 0
CS_DBLCLKS = 0x0008
IDC_ARROW = 32512


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_ubyte),
        ("BlendFlags", ctypes.c_ubyte),
        ("SourceConstantAlpha", ctypes.c_ubyte),
        ("AlphaFormat", ctypes.c_ubyte),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wt.DWORD),
        ("biWidth", wt.LONG),
        ("biHeight", wt.LONG),
        ("biPlanes", wt.WORD),
        ("biBitCount", wt.WORD),
        ("biCompression", wt.DWORD),
        ("biSizeImage", wt.DWORD),
        ("biXPelsPerMeter", wt.LONG),
        ("biYPelsPerMeter", wt.LONG),
        ("biClrUsed", wt.DWORD),
        ("biClrImportant", wt.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wt.DWORD * 3)]


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", ctypes.c_uint),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wt.HINSTANCE),
        ("hIcon", wt.HICON),
        ("hCursor", wt.HANDLE),
        ("hbrBackground", wt.HBRUSH),
        ("lpszMenuName", wt.LPCWSTR),
        ("lpszClassName", wt.LPCWSTR),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wt.HWND),
        ("message", ctypes.c_uint),
        ("wParam", wt.WPARAM),
        ("lParam", wt.LPARAM),
        ("time", wt.DWORD),
        ("pt", wt.POINT),
    ]


user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
user32.CreateWindowExW.restype = wt.HWND
user32.CreateWindowExW.argtypes = [
    wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, wt.HWND, wt.HMENU, wt.HINSTANCE, ctypes.c_void_p,
]
user32.DefWindowProcW.restype = LRESULT
user32.DefWindowProcW.argtypes = [wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM]
user32.UpdateLayeredWindow.restype = wt.BOOL
user32.UpdateLayeredWindow.argtypes = [
    wt.HWND, wt.HDC, ctypes.POINTER(wt.POINT), ctypes.POINTER(wt.SIZE), wt.HDC,
    ctypes.POINTER(wt.POINT), wt.COLORREF, ctypes.POINTER(BLENDFUNCTION), wt.DWORD,
]
user32.GetDC.restype = wt.HDC
user32.GetDC.argtypes = [wt.HWND]
user32.ReleaseDC.argtypes = [wt.HWND, wt.HDC]
gdi32.CreateCompatibleDC.restype = wt.HDC
gdi32.CreateCompatibleDC.argtypes = [wt.HDC]
gdi32.DeleteDC.argtypes = [wt.HDC]
gdi32.CreateDIBSection.restype = wt.HBITMAP
gdi32.CreateDIBSection.argtypes = [
    wt.HDC, ctypes.POINTER(BITMAPINFO), wt.UINT, ctypes.POINTER(ctypes.c_void_p),
    wt.HANDLE, wt.DWORD,
]
gdi32.SelectObject.restype = wt.HGDIOBJ
gdi32.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
gdi32.DeleteObject.argtypes = [wt.HGDIOBJ]
user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), wt.HWND, ctypes.c_uint, ctypes.c_uint]
user32.DispatchMessageW.restype = LRESULT
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.SetWindowPos.argtypes = [
    wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint,
]
user32.GetCursorPos.argtypes = [ctypes.POINTER(wt.POINT)]
user32.SetCapture.restype = wt.HWND
user32.SetCapture.argtypes = [wt.HWND]
user32.ReleaseCapture.restype = wt.BOOL
user32.CreatePopupMenu.restype = wt.HMENU
user32.AppendMenuW.argtypes = [wt.HMENU, ctypes.c_uint, ctypes.c_size_t, wt.LPCWSTR]
user32.TrackPopupMenu.restype = ctypes.c_int
user32.TrackPopupMenu.argtypes = [
    wt.HMENU, ctypes.c_uint, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.HWND, ctypes.c_void_p,
]
user32.DestroyMenu.argtypes = [wt.HMENU]
user32.SetForegroundWindow.argtypes = [wt.HWND]
user32.LoadCursorW.restype = wt.HANDLE
user32.LoadCursorW.argtypes = [wt.HINSTANCE, ctypes.c_void_p]
user32.GetSystemMetrics.restype = ctypes.c_int
user32.SystemParametersInfoW.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]
user32.PostMessageW.argtypes = [wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM]

try:
    # per-monitor v2，保证在 125%/150% 缩放下依然按物理像素绘制，不会糊
    user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass


def single_instance():
    """同名互斥量，防止开出多只大肥鱼。"""
    kernel32.CreateMutexW.restype = wt.HANDLE
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wt.BOOL, wt.LPCWSTR]
    handle = kernel32.CreateMutexW(None, True, "Local\\DafeiyuDesktopPet")
    if not handle:
        return True  # 创建失败（极少见）就照常启动
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        return None
    return handle


def log_exception(where):
    """pythonw 没有控制台，异常写进 %APPDATA%\\dafeiyu-pet\\error.log。"""
    import traceback

    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(os.path.join(CONFIG_DIR, "error.log"), "a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] {where}\n")
            traceback.print_exc(file=f)
    except Exception:
        pass


# --------------------------------------------------------------------------
# 台词
# --------------------------------------------------------------------------
LINES_IDLE = [
    "好无聊啊…要不要一起摸会儿鱼？",
    "点我干嘛，我又不会替你写代码。",
    "这桌面挺干净的，适合躺平。",
    "要不要投喂一条小鱼干？",
    "困了…zzZ",
    "别看我，看你的屏幕。",
    "今天也是努力（假装）的一天！",
    "我在这儿陪你呢，别怕。",
    "摸鱼一时爽，一直摸鱼一直爽。",
    "你鼠标挪那么快，我眼都花了。",
]
LINES_CLICK = [
    "诶！别戳我啦～",
    "痒痒的…你手好闲啊。",
    "再戳我就生气了哦。",
    "干嘛呀，人家在发呆。",
    "哼哼，点击已收到，奖励是…没有奖励。",
]
LINES_DRAG = [
    "哇——别甩我！",
    "放我下来！我晕了！",
    "喂喂喂，温柔一点嘛。",
    "我要掉下去了啦！",
]
LINES_GREET = {
    "morning": ["早上好！今天也要元气满满～", "早上好，先喝口水再干活。"],
    "noon": ["中午了，吃饭了没？", "午休时间到，趴一会儿吧。"],
    "evening": ["下班了没？该摸鱼了。", "晚上好呀～"],
    "night": ["这么晚还不睡？小心秃头。", "夜深了，我陪你一起熬夜。"],
}
LINES_MOOD = {
    "happy": ["嘿嘿，今天心情不错！", "赚到了赚到了～"],
    "sad": ["呜…有点委屈。", "算了算了，不跟你计较。"],
    "angry": ["哼！不理你了。", "你再说一遍试试？"],
    "confused": ["嗯？你在干什么？", "我有点没看懂…"],
}


def load_sprites():
    manifest_path = os.path.join(SPRITE_DIR, "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    sprites = {}
    for name, meta in manifest.items():
        p = os.path.join(SPRITE_DIR, meta["file"])
        sprites[name] = Image.open(p).convert("RGBA")
    return sprites


# ---- 全身站姿（来自角色设定图）与它的姿势变体 ----
BODY_POSES = {
    "body_idle": (0.0, 1.0, 0.0),
    "body_happy": (-3.0, 1.02, -6.0),
    "body_shy": (3.0, 0.99, 4.0),
    "body_hop": (0.0, 1.0, -14.0),
    "body_lean": (-6.0, 1.0, 0.0),
}

BODY_ALIAS = {
    "deyi": "body_happy", "ok": "body_happy", "piaole": "body_happy",
    "bixin": "body_happy", "maozhua": "body_happy", "zaoshanghao": "body_happy",
    "ganfan": "body_happy", "huachi": "body_happy",
    "haixiu": "body_shy", "toukan": "body_shy", "shuijiao": "body_shy",
    "tangping": "body_shy", "yun": "body_shy", "qiurao": "body_shy",
    "yaoqian": "body_shy",
    "xia": "body_hop", "zhenjing": "body_hop", "shengqi": "body_hop",
    "jiazai": "body_lean", "wenhao": "body_lean", "wuyu": "body_lean",
    "buyao": "body_lean", "xianqi": "body_lean", "jiaban": "body_lean",
}


def _body_variant(base, angle=0.0, scale=1.0, dy=0.0):
    w, h = base.size
    img = base
    if scale != 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    if angle != 0.0:
        img = img.rotate(angle, resample=Image.BICUBIC, expand=False)
    canvas = Image.new("RGBA", (w, h + 60), (0, 0, 0, 0))
    canvas.alpha_composite(
        img, (max(0, (w - img.width) // 2), 30 + int(dy) + (h - img.height)))
    return canvas


def load_body_sprites():
    path = os.path.join(FULL_DIR, "body.png")
    if not os.path.exists(path):
        return {}
    base = Image.open(path).convert("RGBA")
    return {name: _body_variant(base, a, s, d) for name, (a, s, d) in BODY_POSES.items()}


class Pet:
    def __init__(self):
        self.cfg = self._load_cfg()
        self.heads_raw = load_sprites()            # 24 张半身表情（留作备用素材）
        self.sprites_raw = load_body_sprites()     # 设定图切出来的全身站姿
        if not self.sprites_raw:
            self.sprites_raw = self.heads_raw
        self.screen_w = user32.GetSystemMetrics(0)
        self.screen_h = user32.GetSystemMetrics(1)
        # 任务栏之上的可用区域，让桌宠站在任务栏上面而不是被它盖住
        wa = wt.RECT()
        self.work_bottom = wa.bottom if user32.SystemParametersInfoW(
            0x0030, 0, ctypes.byref(wa), 0) else self.screen_h

        self.scale = self.cfg.get("scale") or self._default_scale()
        self.default_scale = self._default_scale()
        self.scale = min(self.scale, self.default_scale)
        self.sprites = {k: self._fit(v) for k, v in self.sprites_raw.items()}

        max_w = max(s.width for s in self.sprites.values())
        max_h = max(s.height for s in self.sprites.values())
        self.CANVAS_W = int(max_w + 56)
        self.CANVAS_H = int(max_h + 320)

        self.expr = "body_idle" if "body_idle" in self.sprites else "deyi"
        self.bubble_text = ""
        self.bubble_until = 0.0
        self.dragging = False
        self.drag_dx = 0
        self.drag_dy = 0
        self.wander = self.cfg.get("wander", True)
        self.quiet = self.cfg.get("quiet", False)
        self.wander_vx = 0.0
        self.wander_until = 0.0
        self.next_idle_action = time.time() + random.uniform(6, 14)
        self.expr_until = 0.0
        self.frame_rgba = None
        self.alpha_np = None
        self.lock = threading.Lock()

        self.x, self.y = self._initial_pos()
        self._wndproc_ref = WNDPROC(self._wndproc)
        self._create_window()
        self.say(self._greeting(), 6)
        self._start_anim()

    # ---------------- 基础工具 ----------------
    def _default_scale(self):
        target = max(220, min(400, int(self.screen_h * 0.38)))
        raw_h = max(img.height for img in self.sprites_raw.values())
        return round(target / raw_h, 3)

    def _fit(self, img):
        w = max(1, int(img.width * self.scale))
        h = max(1, int(img.height * self.scale))
        return img.resize((w, h), Image.LANCZOS)

    def _load_cfg(self):
        # 优先读程序目录（便携），没有再用系统配置目录
        for path in (os.path.join(HERE, "config.json"), CONFIG_PATH):
            try:
                with open(path, "r", encoding="utf-8-sig") as f:
                    return json.load(f)
            except Exception:
                continue
        return {}

    def _save_cfg(self):
        data = {
            "x": self.x, "y": self.y, "scale": self.scale,
            "wander": self.wander, "quiet": self.quiet,
        }
        for d in (CONFIG_DIR, HERE):
            try:
                os.makedirs(d, exist_ok=True)
                with open(os.path.join(d, "config.json"), "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return
            except Exception:
                continue

    def _initial_pos(self):
        x = self.cfg.get("x")
        y = self.cfg.get("y")
        if isinstance(x, int) and isinstance(y, int) and -self.CANVAS_W < x < self.screen_w:
            return x, y
        return self.screen_w - self.CANVAS_W - 36, self.work_bottom - self.CANVAS_H - 4

    def _greeting(self):
        h = time.localtime().tm_hour
        if 5 <= h < 11:
            key = "morning"
        elif 11 <= h < 14:
            key = "noon"
        elif 14 <= h < 23:
            key = "evening"
        else:
            key = "night"
        return random.choice(LINES_GREET[key])

    def say(self, text, seconds=5):
        self.bubble_text = text
        self.bubble_until = time.time() + seconds

    # ---------------- Win32 窗口 ----------------
    def _create_window(self):
        hinst = kernel32.GetModuleHandleW(None)
        wc = WNDCLASSW()
        wc.style = CS_DBLCLKS
        wc.lpfnWndProc = self._wndproc_ref
        wc.hInstance = hinst
        wc.hCursor = user32.LoadCursorW(None, ctypes.c_void_p(IDC_ARROW))
        wc.lpszClassName = "DafeiyuPetWindow"
        user32.RegisterClassW(ctypes.byref(wc))

        ex = WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
        self.hwnd = user32.CreateWindowExW(
            ex, "DafeiyuPetWindow", "大肥鱼桌宠", WS_POPUP,
            self.x, self.y, self.CANVAS_W, self.CANVAS_H,
            None, None, hinst, None,
        )
        if not self.hwnd:
            raise OSError(f"CreateWindowExW failed: {ctypes.get_last_error()}")

        self.hdc_screen = user32.GetDC(None)
        self.hdc_mem = gdi32.CreateCompatibleDC(self.hdc_screen)
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = self.CANVAS_W
        bmi.bmiHeader.biHeight = -self.CANVAS_H
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = BI_RGB
        self.bits = ctypes.c_void_p()
        self.hbmp = gdi32.CreateDIBSection(
            self.hdc_screen, ctypes.byref(bmi), DIB_RGB_COLORS,
            ctypes.byref(self.bits), None, 0,
        )
        gdi32.SelectObject(self.hdc_mem, self.hbmp)
        user32.SetWindowPos(self.hwnd, -1, self.x, self.y, 0, 0,
                            SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW)

    def _wndproc(self, hwnd, msg, wparam, lparam):
        try:
            if msg == WM_NCHITTEST:
                sx = ctypes.c_short(lparam & 0xFFFF).value
                sy = ctypes.c_short((lparam >> 16) & 0xFFFF).value
                if self._hit(sx, sy):
                    return HTCLIENT
                return HTTRANSPARENT
            if msg == WM_LBUTTONDOWN:
                pt = wt.POINT()
                user32.GetCursorPos(ctypes.byref(pt))
                self.dragging = True
                self.drag_dx = pt.x - self.x
                self.drag_dy = pt.y - self.y
                self.start_x, self.start_y = self.x, self.y
                user32.SetCapture(hwnd)
                self._set_expr("xia", 1.5)
                return 0
            if msg == WM_MOUSEMOVE:
                if self.dragging:
                    pt = wt.POINT()
                    user32.GetCursorPos(ctypes.byref(pt))
                    self.x = pt.x - self.drag_dx
                    self.y = pt.y - self.drag_dy
                    user32.SetWindowPos(hwnd, -1, self.x, self.y, 0, 0,
                                        SWP_NOSIZE | SWP_NOACTIVATE)
                return 0
            if msg == WM_LBUTTONUP:
                was_drag = self.dragging and (
                    abs(self.x - getattr(self, "start_x", self.x)) > 6
                    or abs(self.y - getattr(self, "start_y", self.y)) > 6
                )
                self.dragging = False
                user32.ReleaseCapture()
                if was_drag:
                    self._snap_into_screen()
                    self._save_cfg()
                    if not self.quiet:
                        self.say(random.choice(LINES_DRAG), 3)
                else:
                    self._on_click()
                return 0
            if msg == WM_LBUTTONDBLCLK:
                self._set_expr("bixin", 3)
                self.say("最喜欢你了！", 3)
                return 0
            if msg == WM_RBUTTONUP:
                self._show_menu()
                return 0
            if msg == WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
        except Exception:  # 绝不让异常打断消息循环
            log_exception("wndproc")
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _hit(self, screen_x, screen_y):
        arr = self.alpha_np
        if arr is None:
            return True
        cx = int(screen_x - self.x)
        cy = int(screen_y - self.y)
        if 0 <= cx < arr.shape[1] and 0 <= cy < arr.shape[0]:
            return arr[cy, cx] > 24
        return False

    def _on_click(self):
        self._set_expr(random.choice(["wenhao", "zhenjing", "haixiu", "deyi", "bixin"]), 2)
        if not self.quiet:
            self.say(random.choice(LINES_CLICK), 4)

    def _snap_into_screen(self):
        self.x = int(max(-self.CANVAS_W // 2, min(self.x, self.screen_w - self.CANVAS_W // 2)))
        self.y = int(max(-60, min(self.y, self.work_bottom - 120)))

    def _set_expr(self, name, seconds):
        if name not in self.sprites:
            name = BODY_ALIAS.get(name, "body_idle")
        if name in self.sprites:
            self.expr = name
            self.expr_until = time.time() + seconds

    # ---------------- 右键菜单 ----------------
    def _show_menu(self):
        menu = user32.CreatePopupMenu()
        items = [
            (1, "说句话"),
            (2, "换个表情"),
            (3, None),
            (4, f"{'√ ' if self.wander else '　'}随机走动"),
            (5, f"{'√ ' if self.quiet else '　'}安静模式"),
            (6, "大小 → 小 / 中 / 大"),
            (7, None),
            (8, "藏起来 10 分钟"),
            (9, "退出"),
        ]
        for cid, text in items:
            if text is None:
                user32.AppendMenuW(menu, 0x00000800, 0, None)  # MF_SEPARATOR
            else:
                user32.AppendMenuW(menu, 0, cid, text)

        pt = wt.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        user32.SetForegroundWindow(self.hwnd)
        cmd = user32.TrackPopupMenu(
            menu, TPM_LEFTALIGN | TPM_RIGHTBUTTON | TPM_RETURNCMD | TPM_NONOTIFY,
            pt.x, pt.y, 0, self.hwnd, None,
        )
        user32.PostMessageW(self.hwnd, WM_NULL, 0, 0)
        user32.DestroyMenu(menu)
        self._menu_command(cmd)

    def _menu_command(self, cmd):
        if cmd == 1:
            self.say(random.choice(LINES_IDLE), 5)
        elif cmd == 2:
            self._set_expr(random.choice(list(self.sprites.keys())), 4)
        elif cmd == 4:
            self.wander = not self.wander
            self._save_cfg()
        elif cmd == 5:
            self.quiet = not self.quiet
            self._save_cfg()
        elif cmd == 6:
            order = [0.65, 0.8, 1.0]
            base = self.default_scale
            cur = min(order, key=lambda s: abs(s * base - self.scale))
            nxt = order[(order.index(cur) + 1) % len(order)] * base
            self.scale = round(nxt, 3)
            self.sprites = {k: self._fit(v) for k, v in self.sprites_raw.items()}
            self._save_cfg()
            self.say(f"变成 {int(order[(order.index(cur) + 1) % len(order)] * 100)}% 啦", 3)
        elif cmd == 8:
            self._hide_temporarily(600)
        elif cmd == 9:
            self._save_cfg()
            user32.PostMessageW(self.hwnd, WM_DESTROY, 0, 0)

    def _hide_temporarily(self, seconds):
        user32.ShowWindow(self.hwnd, 0)

        def restore():
            time.sleep(seconds)
            user32.ShowWindow(self.hwnd, 5)
            self.say("我回来啦！", 4)

        threading.Thread(target=restore, daemon=True).start()

    # ---------------- 渲染 ----------------
    def _compose(self):
        canvas = Image.new("RGBA", (self.CANVAS_W, self.CANVAS_H), (0, 0, 0, 0))
        now = time.time()

        sprite = self.sprites[self.expr]
        bob = 0 if self.dragging else int(round(3.0 * self.scale * math.sin(now * 1.9)))

        sw, sh = sprite.size
        sx = (self.CANVAS_W - sw) // 2
        sy = self.CANVAS_H - sh - 24 + bob
        canvas.alpha_composite(sprite, (sx, sy))

        if self.bubble_text and now < self.bubble_until:
            self._draw_bubble(canvas, self.bubble_text, sx, sy, sw)
        elif self.bubble_text and now >= self.bubble_until:
            self.bubble_text = ""

        return canvas

    def _draw_bubble(self, canvas, text, sx, sy, sw):
        font = ImageFont.truetype(FONT_PATH, 20)
        max_w = 330
        lines, buf = [], ""
        for ch in text:
            if ch == "\n":
                lines.append(buf)
                buf = ""
                continue
            if font.getlength(buf + ch) > max_w:
                lines.append(buf)
                buf = ch
            else:
                buf += ch
        if buf:
            lines.append(buf)

        pad_x, pad_y, lh = 16, 12, 28
        tw = max(int(font.getlength(l)) for l in lines)
        bw = min(max_w, tw) + pad_x * 2
        bh = lh * len(lines) + pad_y * 2

        bx = sx + sw // 2 - bw // 2
        bx = max(6, min(bx, self.CANVAS_W - bw - 6))
        by = sy - bh - 16

        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        radius = 16
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=radius,
                            fill=(255, 255, 255, 245), outline=(43, 58, 103, 255), width=2)
        # 小尾巴
        cx = sx + sw // 2
        d.polygon([(cx - 9, by + bh - 1), (cx + 9, by + bh - 1), (cx, by + bh + 13)],
                  fill=(255, 255, 255, 245), outline=(43, 58, 103, 255))
        d.line([(cx - 9, by + bh), (cx + 9, by + bh)], fill=(255, 255, 255, 245), width=2)

        for i, line in enumerate(lines):
            d.text((bx + pad_x, by + pad_y + i * lh), line, font=font, fill=(30, 41, 59, 255))

        canvas.alpha_composite(layer)

    def _push(self, canvas):
        arr = np.array(canvas, dtype=np.uint8)
        a = arr[:, :, 3]
        rgb = arr[:, :, :3].astype(np.uint32)
        alpha = a.astype(np.uint32)[:, :, None]
        premul = ((rgb * alpha + 127) // 255).astype(np.uint8)
        bgra = np.empty_like(arr)
        bgra[:, :, 0] = premul[:, :, 2]
        bgra[:, :, 1] = premul[:, :, 1]
        bgra[:, :, 2] = premul[:, :, 0]
        bgra[:, :, 3] = a
        ctypes.memmove(self.bits, bgra.ctypes.data, bgra.size)

        with self.lock:
            self.alpha_np = a

        dst = wt.POINT(int(self.x), int(self.y))
        size = wt.SIZE(self.CANVAS_W, self.CANVAS_H)
        src = wt.POINT(0, 0)
        blend = BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)
        user32.UpdateLayeredWindow(
            self.hwnd, self.hdc_screen, ctypes.byref(dst), ctypes.byref(size),
            self.hdc_mem, ctypes.byref(src), 0, ctypes.byref(blend), ULW_ALPHA,
        )

    # ---------------- 动画循环 ----------------
    def _start_anim(self):
        def loop():
            while True:
                try:
                    now = time.time()
                    self._tick(now)
                    self._push(self._compose())
                except Exception:
                    log_exception("anim")
                time.sleep(1 / 30)

        threading.Thread(target=loop, daemon=True).start()

    def _tick(self, now):
        if self.expr_until and now > self.expr_until:
            self.expr = "body_idle" if "body_idle" in self.sprites else "deyi"
            self.expr_until = 0

        # 走动
        if self.wander and not self.dragging:
            if now > self.wander_until:
                if random.random() < 0.25:
                    self.wander_vx = random.choice([-1, 1]) * random.uniform(0.6, 1.6)
                    self.wander_until = now + random.uniform(1.2, 3.0)
                else:
                    self.wander_vx = 0
                    self.wander_until = now + random.uniform(3, 8)
            if self.wander_vx:
                self.x = int(self.x + self.wander_vx)
                if self.x < -self.CANVAS_W // 3:
                    self.x = -self.CANVAS_W // 3
                    self.wander_vx = abs(self.wander_vx)
                if self.x > self.screen_w - self.CANVAS_W * 2 // 3:
                    self.x = self.screen_w - self.CANVAS_W * 2 // 3
                    self.wander_vx = -abs(self.wander_vx)
                user32.SetWindowPos(self.hwnd, -1, int(self.x), int(self.y), 0, 0,
                                    SWP_NOSIZE | SWP_NOACTIVATE)

        # 随机小动作
        if now > self.next_idle_action:
            self.next_idle_action = now + random.uniform(10, 26)
            roll = random.random()
            if self.quiet:
                if roll < 0.5:
                    self._set_expr(random.choice(["shuijiao", "tangping", "yun"]), 4)
            else:
                if roll < 0.45:
                    self.say(random.choice(LINES_IDLE), 5)
                elif roll < 0.75:
                    self._set_expr(random.choice(list(self.sprites.keys())), 3)
                elif roll < 0.9:
                    self._set_expr(random.choice(["shuijiao", "tangping"]), 6)
                    self.say("摸鱼中，勿扰…", 5)

    def run(self):
        msg = MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))


def main():
    try:
        if single_instance() is None:
            return
        pet = Pet()
        pet.run()
    except Exception:
        log_exception("main")
        raise


if __name__ == "__main__":
    main()
