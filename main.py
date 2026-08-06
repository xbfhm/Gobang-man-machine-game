# -*- coding: utf-8 -*-
"""
五子棋豪华版 v2.1 —— 安卓 16 兼容版（真机 UI 修复）
====================================================
v2.1 修复（真机反馈）：
  * 全部字号改用 sp()、尺寸改用 dp() —— 高密度屏不再字小
  * 顶部安全区：读取状态栏高度（含刘海/摄像头挖孔），标题不再被挡住
  * 主控制面板 GridLayout 子控件固定高度，避免面板塌陷导致按键失效
  * 回放控制条仅在回放模式下显示，平时不再出现“没反应”的按钮
  * 去除所有 emoji（NotoSansCJK 无字形→豆腐块），改用安全符号
  * 弹窗改用自定义中文标题，避免默认字体缺中文字形
"""

import gc as _gc_module  # 统一用 gc 指代 game_core
import os
import sys
import json
import time
import math
import struct
import wave
import random

from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.metrics import dp, sp
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, Line, Ellipse, Rectangle, Triangle
from kivy.clock import Clock
from kivy.logger import Logger

import game_core as gc

# =========================
# 字体注册
# =========================
FONT_PATH = "NotoSansCJK-Regular.otf"
try:
    if os.path.exists(FONT_PATH):
        LabelBase.register(name="Chinese", fn_regular=FONT_PATH)
    else:
        LabelBase.register(name="Chinese", fn_regular=None)
except Exception:
    pass


def CJK(text, size=15, color=(1, 1, 1, 1), **kw):
    """统一创建中文字体 Label（默认字号 sp 15）"""
    return Label(text=text, font_name="Chinese", font_size=sp(size),
                 color=color, **kw)


def CJKBtn(text, font=15, **kw):
    """统一创建中文字体 Button（宽度自适应，固定高度，防面板塌陷）"""
    kw.setdefault("size", (dp(100), dp(46)))
    b = Button(text=text, font_name="Chinese", font_size=sp(font),
               size_hint=(1, None), **kw)
    return b


# =========================
# 多语言（不含 emoji，全部为 NotoSansCJK 可显示字符）
# =========================
TXT = {
    "zh": {
        "title": "五子棋豪华版",
        "your_turn": "轮到你了（黑棋）",
        "ai_thinking": "AI 思考中...",
        "you_win": "你赢了！",
        "ai_win": "对方赢了！",
        "draw": "平局",
        "forbidden": "禁手！",
        "timeout": "超时！",
        "new_game": "新游戏开始",
        "undo_done": "已悔棋（剩余 {n} 次）",
        "no_undo": "本局悔棋次数已用完",
        "hint": "提示",
        "hint_show": "提示：第 {r} 行 第 {c} 列（已标绿圈）",
        "threats_on": "威胁点：开",
        "threats_off": "威胁点：关",
        "saved": "棋谱已保存",
        "loaded": "棋谱已载入，进入回放",
        "stats": "统计",
        "settings": "设置",
        "replay": "回放",
        "online": "联机",
        "challenge_sel": "残局选关",
        "fullscreen": "全屏",
        "lang": "EN",
        "restart": "重开",
        "undo": "悔棋",
        "mode_ai": "人机",
        "mode_double": "双人",
        "mode_challenge": "残局",
        "mode_online": "联机",
        "create_room": "创建房间",
        "join_room": "加入房间",
        "my_ip": "我的 IP",
        "enter_ip": "输入对方 IP",
        "connect": "连接",
        "cancel": "取消",
        "chat_placeholder": "输入聊天内容...",
        "send": "发送",
        "resume": "发现未完成的对局，是否继续？",
        "resume_yes": "继续",
        "resume_no": "放弃",
        "challenge_pass": "残局通过！",
        "challenge_fail": "残局失败，再接再厉",
        "challenge_hint": "提示：",
        "black": "黑棋",
        "white": "白棋",
        "move": "第 {n} 手",
        "time_left": "剩余 {t} 秒",
        "achievement": "解锁成就：{name}",
        "undo_limit": "悔棋剩余",
        "ai_first": "AI 先手",
        "you_first": "你先手",
        "save_sgf": "保存棋谱",
        "ai_move": "AI 代走",
        "prev": "上一步",
        "play": "播放",
        "pause": "暂停",
        "next": "下一步",
        "speed": "速度",
        "locked": "未解锁",
        "unlocked": "已解锁",
        "ok": "保存",
        "apply": "应用",
    },
    "en": {
        "title": "Gomoku Deluxe",
        "your_turn": "Your turn (Black)",
        "ai_thinking": "AI thinking...",
        "you_win": "You win!",
        "ai_win": "AI wins!",
        "draw": "Draw",
        "forbidden": "Forbidden move!",
        "timeout": "Time out!",
        "new_game": "New game",
        "undo_done": "Undone ({n} left)",
        "no_undo": "No undo left",
        "hint": "Hint",
        "hint_show": "Hint: row {r} col {c}",
        "threats_on": "Threats: ON",
        "threats_off": "Threats: OFF",
        "saved": "SGF saved",
        "loaded": "Loaded, replay mode",
        "stats": "Stats",
        "settings": "Settings",
        "replay": "Replay",
        "online": "Online",
        "challenge_sel": "Challenges",
        "fullscreen": "Fullscreen",
        "lang": "中",
        "restart": "New",
        "undo": "Undo",
        "mode_ai": "AI",
        "mode_double": "2P",
        "mode_challenge": "Puzzle",
        "mode_online": "Online",
        "create_room": "Host",
        "join_room": "Join",
        "my_ip": "My IP",
        "enter_ip": "Peer IP",
        "connect": "Connect",
        "cancel": "Cancel",
        "chat_placeholder": "Chat...",
        "send": "Send",
        "resume": "Unfinished game found. Resume?",
        "resume_yes": "Resume",
        "resume_no": "Discard",
        "challenge_pass": "Puzzle solved!",
        "challenge_fail": "Puzzle failed",
        "challenge_hint": "Hint: ",
        "black": "Black",
        "white": "White",
        "move": "Move {n}",
        "time_left": "{t}s left",
        "achievement": "Achievement: {name}",
        "undo_limit": "Undo left",
        "ai_first": "AI first",
        "you_first": "You first",
        "save_sgf": "Save SGF",
        "ai_move": "AI move",
        "prev": "Prev",
        "play": "Play",
        "pause": "Pause",
        "next": "Next",
        "speed": "Speed",
        "locked": "Locked",
        "unlocked": "Unlocked",
        "ok": "Save",
        "apply": "Apply",
    },
}


# =========================
# 程序生成音效（无需外部 wav）
# =========================
def _write_wav(path, freq, dur, vol=0.5, wave_type="sin", seq=None):
    try:
        rate = 22050
        frames = bytearray()
        if seq is None:
            seq = [(freq, dur)]
        for f, d in seq:
            n = int(rate * d)
            for i in range(n):
                t = i / float(rate)
                if wave_type == "square":
                    v = vol if math.sin(2 * math.pi * f * t) >= 0 else -vol
                else:
                    v = vol * math.sin(2 * math.pi * f * t)
                if i > n * 0.8:
                    v *= (n - i) / (n * 0.2)
                frames += struct.pack("<h", int(v * 32000))
        with wave.open(path, "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(bytes(frames))
        return True
    except Exception as e:
        Logger.warning("wav gen failed: %s", e)
        return False


def ensure_sounds():
    files = {
        "place.wav": dict(seq=[(660, 0.06)], wave_type="square", vol=0.4),
        "undo.wav": dict(seq=[(440, 0.08), (330, 0.08)], vol=0.4),
        "win.wav": dict(seq=[(523, 0.12), (659, 0.12), (784, 0.12), (1047, 0.25)], vol=0.5),
        "lose.wav": dict(seq=[(392, 0.15), (330, 0.15), (262, 0.3)], vol=0.45),
        "ui.wav": dict(seq=[(880, 0.05)], wave_type="square", vol=0.3),
    }
    for name, kw in files.items():
        if not os.path.exists(name):
            _write_wav(name, 0, 0, **kw)


# =========================
# 安全区（状态栏/刘海/摄像头挖孔）
# =========================
def get_insets():
    """
    返回 (top, right, bottom, left) 安全区（单位：像素）。
    安卓：尝试读取 status_bar_height / navigation_bar_height 资源。
    其他平台：返回 0。
    """
    top = right = bottom = left = 0
    platform = None
    try:
        from kivy.utils import platform
    except Exception:
        platform = None
    if platform == "android":
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            res = activity.getResources()
            ident = res.getIdentifier("status_bar_height", "dimen", "android")
            if ident > 0:
                top = int(res.getDimensionPixelSize(ident))
            ident2 = res.getIdentifier("navigation_bar_height", "dimen", "android")
            if ident2 > 0:
                bottom = int(res.getDimensionPixelSize(ident2))
            try:  # 刘海/挖孔区域
                from jnius import cast
                from jnius import autoclass as _ac
                DisplayCutout = _ac("android.view.DisplayCutout")
                view = activity.getWindow().getDecorView()
                cutout = view.getRootWindowInsets().getDisplayCutout()
                if cutout is not None:
                    safe = cutout.getSafeInsetTop()
                    if safe > top:
                        top = safe
            except Exception:
                pass
        except Exception as e:
            Logger.warning("insets error: %s", e)
    return (top, right, bottom, left)


# =========================
# 全局配置
# =========================
class Config:
    def __init__(self):
        self.mode = "AI"
        self.board_size = 19
        self.difficulty = "中"
        self.ai_style = "平衡"
        self.theme = "木质"
        self.piece_style = "圆形"
        self.grid_color = (0.2, 0.15, 0.1, 1)
        self.show_coords = True
        self.sound_enabled = True
        self.vibrate = True
        self.timer_enabled = False
        self.timer_seconds = 30
        self.forbidden_enabled = False
        self.six_in_row = False
        self.undo_limit = 3
        self.ai_first = False
        self.opening = "天元"
        self.fullscreen = False
        self.lang = "zh"
        self.show_threats = True
        self.auto_save = True
        self.save_file = "config.json"

    def load(self):
        try:
            with open(self.save_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in data.items():
                if hasattr(self, k):
                    setattr(self, k, v)
        except Exception:
            pass

    def save(self):
        try:
            with open(self.save_file, "w", encoding="utf-8") as f:
                json.dump(self.__dict__, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


config = Config()
config.load()
ensure_sounds()

THEMES = {
    "木质": {"bg": (0.86, 0.72, 0.48, 1), "line": (0.25, 0.17, 0.10, 1)},
    "深色": {"bg": (0.09, 0.09, 0.12, 1), "line": (0.55, 0.55, 0.58, 1)},
    "简约": {"bg": (0.96, 0.96, 0.96, 1), "line": (0.3, 0.3, 0.3, 1)},
    "星空": {"bg": (0.05, 0.07, 0.20, 1), "line": (0.45, 0.62, 0.90, 1)},
    "海洋": {"bg": (0.75, 0.88, 0.90, 1), "line": (0.05, 0.35, 0.45, 1)},
}


# =========================
# 棋盘 Widget
# =========================
class BoardWidget(Widget):
    def __init__(self, status_label, **kwargs):
        super().__init__(**kwargs)
        self.status_label = status_label
        self.board_size = config.board_size
        self.board = gc.make_board(self.board_size)
        self.history = []
        self.last_move = None
        self.winning_cells = None
        self.game_over = False
        self.awaiting_ai = False
        self.current_player = gc.BLACK
        self.step_count = 0
        self.undo_used = 0

        self.challenge_idx = 1
        self.ai_steps = 0
        self.challenge_active = False

        self.network = None
        self.online = False
        self.my_turn = False
        self.chat_lines = []

        self.timer_running = False
        self.time_left = config.timer_seconds
        self.timer_event = None

        self.replay_mode = False
        self.replay_steps = []
        self.replay_index = 0
        self.replay_playing = False
        self.replay_speed = 1.0
        self.replay_event = None

        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._touches = {}
        self._pinch_start_dist = None
        self._pinch_start_zoom = None
        self._drag_start = None

        self.piece_anim = {}
        self.pulse_t = 0.0
        self.confetti = []
        self.anim_event = None

        self.sound = {}
        if config.sound_enabled:
            try:
                from kivy.core.audio import SoundLoader
                for name in ("place", "win", "lose", "undo", "ui"):
                    if os.path.exists(name + ".wav"):
                        self.sound[name] = SoundLoader.load(name + ".wav")
            except Exception:
                pass

        self._vibrator = None
        if config.vibrate:
            try:
                from plyer import vibrator
                self._vibrator = vibrator
            except Exception:
                self._vibrator = None

        self.bind(size=self.redraw, pos=self.redraw)
        Window.bind(on_key_down=self.on_key_down)
        self.redraw()

    # ---------- 工具 ----------
    def tr(self, key, **kw):
        s = TXT.get(config.lang, TXT["zh"]).get(key, TXT["zh"].get(key, key))
        try:
            return s.format(**kw)
        except Exception:
            return s

    def play_sound(self, name):
        try:
            if config.sound_enabled and name in self.sound and self.sound[name]:
                self.sound[name].stop()
                self.sound[name].play()
        except Exception:
            pass

    def vibrate(self, sec=0.03):
        try:
            if self._vibrator:
                self._vibrator.vibrate(sec)
        except Exception:
            pass

    def set_status(self, text, color=(1, 1, 1, 1)):
        self.status_label.text = text
        self.status_label.color = color

    def on_key_down(self, window, key, scancode, codepoint, modifiers):
        if key == 114:
            self.reset()
        elif key == 117:
            self.undo()
        elif key == 115:
            self.save_sgf()
        elif key == 102:
            self.toggle_fullscreen()

    def toggle_fullscreen(self):
        config.fullscreen = not config.fullscreen
        Window.fullscreen = config.fullscreen
        config.save()

    # ---------- 几何 ----------
    def cell_size(self):
        base = min(self.width, self.height) / (self.board_size + 1)
        return base * self.zoom

    def origin(self):
        cs = self.cell_size()
        w = cs * (self.board_size - 1)
        ox = self.x + (self.width - w) / 2 + self.pan_x
        oy = self.y + (self.height - w) / 2 + self.pan_y
        return ox, oy

    # ---------- 绘制 ----------
    def redraw(self, *args):
        self.canvas.clear()
        cs = self.cell_size()
        if cs <= 0:
            return
        ox, oy = self.origin()
        th = THEMES.get(config.theme, THEMES["木质"])
        line_col = config.grid_color if config.grid_color else th["line"]
        bg = th["bg"]

        with self.canvas:
            Color(*bg)
            Rectangle(pos=self.pos, size=self.size)
            Color(*line_col)
            for i in range(self.board_size):
                Line(points=[ox + i * cs, oy, ox + i * cs, oy + cs * (self.board_size - 1)], width=1)
                Line(points=[ox, oy + i * cs, ox + cs * (self.board_size - 1), oy + i * cs], width=1)
            if self.board_size >= 13:
                stars = [3, self.board_size // 2, self.board_size - 4]
                for sr in stars:
                    for sc in stars:
                        Line(circle=(ox + sc * cs, oy + sr * cs, cs * 0.08), width=2)
            elif self.board_size >= 9:
                m = self.board_size // 2
                for sr, sc in [(m, m), (2, 2), (2, self.board_size - 3),
                               (self.board_size - 3, 2), (self.board_size - 3, self.board_size - 3)]:
                    Line(circle=(ox + sc * cs, oy + sr * cs, cs * 0.08), width=2)
            if config.show_coords:
                fs = max(cs * 0.5, sp(8))
                for i in range(self.board_size):
                    self._draw_text(ox - cs * 0.7, oy + i * cs - cs * 0.35, str(i + 1), fs, line_col)
                    self._draw_text(ox + i * cs - cs * 0.3, oy - cs * 0.85, chr(ord('A') + i), fs, line_col)

            now = time.time()
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if self.board[r][c] == gc.EMPTY:
                        continue
                    x, y = ox + c * cs, oy + r * cs
                    if config.piece_style == "方块":
                        Color(0.02, 0.02, 0.02, 1) if self.board[r][c] == gc.BLACK else Color(0.95, 0.95, 0.95, 1)
                        half = cs * 0.38
                        Rectangle(pos=(x - half, y - half), size=(half * 2, half * 2))
                    else:
                        scale = 1.0
                        if (r, c) in self.piece_anim:
                            dt = now - self.piece_anim[(r, c)]
                            scale = min(1.0, dt / 0.18)
                            scale = 0.3 + 0.7 * scale
                        Color(0.02, 0.02, 0.02, 1) if self.board[r][c] == gc.BLACK else Color(0.97, 0.97, 0.97, 1)
                        radius = cs * 0.42 * scale
                        Ellipse(pos=(x - radius, y - radius), size=(radius * 2, radius * 2))
                        if self.board[r][c] == gc.BLACK:
                            Color(0.35, 0.35, 0.35, 0.5)
                            Line(circle=(x, y, radius * 0.6), width=1)
                        else:
                            Color(0.75, 0.75, 0.75, 0.5)
                            Line(circle=(x, y, radius * 0.6), width=1)
                    if config.piece_style == "序号":
                        step = self._get_step(r, c)
                        if step:
                            col = (0.9, 0.6, 0.1, 1) if self.board[r][c] == gc.BLACK else (0.1, 0.1, 0.1, 1)
                            self._draw_text(x - cs * 0.25, y - cs * 0.35, str(step), max(cs * 0.5, sp(8)), col)

            if self.last_move and not self.game_over:
                r, c = self.last_move
                rr = cs * (0.12 + 0.06 * math.sin(self.pulse_t * 6))
                Color(1, 0.25, 0.1, 1)
                Line(circle=(ox + c * cs, oy + r * cs, rr), width=2)

            if self.winning_cells:
                Color(1, 0.85, 0.1, 0.75 + 0.25 * math.sin(self.pulse_t * 5))
                for r, c in self.winning_cells:
                    Line(circle=(ox + c * cs, oy + r * cs, cs * 0.46), width=3)

            if config.show_threats and not self.game_over and self.history:
                Color(1, 0.15, 0.15, 0.35)
                enemy = gc.other(self.current_player) if not self.awaiting_ai else gc.BLACK
                for (r, c) in gc.threat_points(self.board, self.board_size, enemy):
                    Line(circle=(ox + c * cs, oy + r * cs, cs * 0.3), width=1.5)

            if getattr(self, "hint_move", None) and not self.game_over:
                r, c = self.hint_move
                Color(0.2, 1.0, 0.3, 0.9)
                Line(circle=(ox + c * cs, oy + r * cs, cs * 0.34), width=3)
                Line(circle=(ox + c * cs, oy + r * cs, cs * 0.12), width=3)

            for p in self.confetti:
                Color(p["color"][0], p["color"][1], p["color"][2], p["alpha"])
                Triangle(points=[p["x"], p["y"], p["x"] + p["w"], p["y"],
                                 p["x"] + p["w"] / 2, p["y"] + p["h"]])

        if (self.piece_anim or self.winning_cells or self.confetti) and not self.anim_event:
            self.anim_event = Clock.schedule_interval(self._anim_tick, 1 / 30.0)

    def _anim_tick(self, dt):
        now = time.time()
        self.pulse_t += dt
        for key in list(self.piece_anim.keys()):
            if now - self.piece_anim[key] > 0.2:
                del self.piece_anim[key]
        alive = []
        for p in self.confetti:
            p["vy"] -= 300 * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["alpha"] -= 0.9 * dt
            if p["alpha"] > 0 and p["y"] > -10:
                alive.append(p)
        self.confetti = alive
        self.redraw()
        if not self.piece_anim and not self.winning_cells and not self.confetti:
            if self.anim_event:
                self.anim_event.cancel()
                self.anim_event = None
            self.redraw()

    def _draw_text(self, x, y, text, font_size, color):
        try:
            from kivy.core.text import Label as CoreLabel
            lbl = CoreLabel(text=str(text), font_size=font_size, color=color)
            lbl.refresh()
            tex = lbl.texture
            with self.canvas:
                Color(*color)
                Rectangle(texture=tex, pos=(x, y), size=tex.size)
        except Exception:
            pass

    def _get_step(self, row, col):
        for i, (r, c, who) in enumerate(self.history, 1):
            if r == row and c == col:
                return i
        return None

    def start_confetti(self):
        w, h = self.width, self.height
        colors = [(1, 0.3, 0.3), (0.3, 1, 0.4), (0.3, 0.6, 1), (1, 0.9, 0.2), (0.9, 0.4, 1)]
        self.confetti = []
        rnd = random.Random()
        for _ in range(60):
            self.confetti.append({
                "x": rnd.uniform(0, w), "y": rnd.uniform(h * 0.6, h),
                "vx": rnd.uniform(-60, 60), "vy": rnd.uniform(-40, 40),
                "w": rnd.uniform(4, 9), "h": rnd.uniform(8, 16),
                "alpha": 1.0, "color": rnd.choice(colors),
            })
        self.redraw()

    # ---------- 触摸 ----------
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        if len(self._touches) == 0:
            self._drag_start = (touch.x, touch.y)
        self._touches[touch.id] = touch
        if len(self._touches) == 2:
            ids = list(self._touches.keys())
            t1, t2 = self._touches[ids[0]], self._touches[ids[1]]
            self._pinch_start_dist = self._dist(t1, t2)
            self._pinch_start_zoom = self.zoom
            self._drag_start = None
        return True

    def _dist(self, t1, t2):
        return math.hypot(t1.x - t2.x, t1.y - t2.y)

    def on_touch_move(self, touch):
        if touch.id not in self._touches:
            return False
        if len(self._touches) == 2 and self._pinch_start_dist:
            ids = list(self._touches.keys())
            d = self._dist(self._touches[ids[0]], self._touches[ids[1]])
            self.zoom = max(0.5, min(3.0, self._pinch_start_zoom * d / self._pinch_start_dist))
            self.redraw()
            return True
        if self._drag_start and len(self._touches) == 1:
            self.pan_x += touch.x - self._drag_start[0]
            self.pan_y += touch.y - self._drag_start[1]
            self._drag_start = (touch.x, touch.y)
            self.redraw()
            return True
        return False

    def on_touch_up(self, touch):
        if touch.id not in self._touches:
            return False
        was_pinch = len(self._touches) == 2
        del self._touches[touch.id]
        self._pinch_start_dist = None
        if len(self._touches) == 0:
            self._drag_start = None
            if not was_pinch and not touch.is_double_tap:
                self._try_tap(touch)
        return True

    def _board_coord(self, x, y):
        cs = self.cell_size()
        ox, oy = self.origin()
        col = round((x - ox) / cs)
        row = round((y - oy) / cs)
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            return row, col
        return None

    def _try_tap(self, touch):
        pos = self._board_coord(touch.x, touch.y)
        if pos is None:
            return
        row, col = pos
        if self.replay_mode:
            return
        if self.game_over or self.awaiting_ai:
            return
        if self.board[row][col] != gc.EMPTY:
            return

        if config.mode == "DOUBLE":
            if self._try_move(row, col, self.current_player):
                win, cells = gc.check_win(self.board, self.board_size, row, col,
                                          self.current_player, config.six_in_row)
                if win:
                    self.finish_game(self.current_player, cells)
                else:
                    self.current_player = gc.other(self.current_player)
                    who = self.tr("black") if self.current_player == gc.BLACK else self.tr("white")
                    self.set_status(self.tr("move", n=self.step_count) + " · " + who)
            return

        if config.mode == "AI":
            if config.forbidden_enabled and gc.is_forbidden(self.board, self.board_size,
                                                            row, col, gc.BLACK):
                self.play_sound("lose")
                self.set_status(self.tr("forbidden"), (1, 0.2, 0.2, 1))
                self.finish_game(gc.WHITE, None, forbidden=True)
                return
            if self._try_move(row, col, gc.BLACK):
                self.hint_move = None
                win, cells = gc.check_win(self.board, self.board_size, row, col,
                                          gc.BLACK, config.six_in_row)
                if win:
                    self.finish_game(gc.BLACK, cells)
                    return
                self.set_status(self.tr("ai_thinking"), (1, 1, 1, 1))
                self.awaiting_ai = True
                self.timer_running = False
                Clock.schedule_once(self.ai_play, 0.25)
            return

        if config.mode == "ONLINE":
            if not self.my_turn:
                self.set_status("等待对方落子...", (1, 1, 1, 1))
                return
            if self._try_move(row, col, gc.BLACK):
                self.network.send_move(row, col)
                self.my_turn = False
                win, cells = gc.check_win(self.board, self.board_size, row, col,
                                          gc.BLACK, config.six_in_row)
                if win:
                    self.finish_game(gc.BLACK, cells)
                else:
                    self.set_status("等待对方...", (1, 1, 1, 1))
            return

        if config.mode == "CHALLENGE":
            # 玩家执黑解题；禁手对黑棋也生效（可选）
            if config.forbidden_enabled and gc.is_forbidden(self.board, self.board_size,
                                                            row, col, gc.BLACK):
                self.play_sound("lose")
                self.set_status(self.tr("forbidden"), (1, 0.2, 0.2, 1))
                self.finish_game(gc.WHITE, None, forbidden=True)
                return
            if self._try_move(row, col, gc.BLACK):
                self.hint_move = None
                win, cells = gc.check_win(self.board, self.board_size, row, col,
                                          gc.BLACK, config.six_in_row)
                if win:
                    self.finish_game(gc.BLACK, cells)
                    return
                # 超过步数限制即失败
                if self.ai_steps >= self._challenge_win_in():
                    self.finish_game(gc.WHITE, None)
                    return
                self.set_status(self.tr("ai_thinking"), (1, 1, 1, 1))
                self.awaiting_ai = True
                Clock.schedule_once(self.ai_play, 0.25)

    def _try_move(self, row, col, who):
        if self.board[row][col] != gc.EMPTY or self.game_over:
            return False
        if config.timer_enabled and who == self._timer_player() and self.timer_running:
            if self.time_left <= 0:
                self.set_status(self.tr("timeout"), (1, 0.2, 0.2, 1))
                self.finish_game(gc.other(who), None)
                return False
        self.board[row][col] = who
        self.last_move = (row, col)
        self.step_count += 1
        self.history.append((row, col, who))
        self.piece_anim[(row, col)] = time.time()
        if config.mode == "CHALLENGE" and who == gc.BLACK:
            self.ai_steps += 1
        self.redraw()
        self.play_sound("place")
        self.vibrate()
        if config.timer_enabled:
            self.time_left = config.timer_seconds
            self.timer_running = True
        return True

    def _timer_player(self):
        if config.mode == "AI":
            return gc.BLACK
        if config.mode == "DOUBLE":
            return self.current_player
        if config.mode == "CHALLENGE":
            return gc.BLACK  # 玩家（黑）解题方被计时
        return None

    # ---------- AI ----------
    def ai_play(self, dt):
        self.awaiting_ai = False
        if self.game_over:
            return
        if config.mode == "CHALLENGE":
            # AI 执白防守
            pos = gc.defense_move(self.board, self.board_size, gc.BLACK, gc.WHITE)
            if pos is None:
                return
            r, c = pos
            self._try_move(r, c, gc.WHITE)
            win, cells = gc.check_win(self.board, self.board_size, r, c, gc.WHITE, config.six_in_row)
            if win:
                self.finish_game(gc.WHITE, cells)
                return
            if gc.board_full(self.board, self.board_size):
                self.finish_game(None, None)
                return
            # 玩家未在限内取胜
            if self.ai_steps >= self._challenge_win_in():
                self.finish_game(gc.WHITE, None)
                return
            self.set_status(f"你已走 {self.ai_steps}/{self._challenge_win_in()} 手，继续！",
                            (1, 1, 1, 1))
            return
        pos = gc.ai_move(self.board, self.board_size, gc.WHITE, config.difficulty, config.ai_style)
        if pos is None:
            return
        r, c = pos
        self._try_move(r, c, gc.WHITE)
        win, cells = gc.check_win(self.board, self.board_size, r, c, gc.WHITE, config.six_in_row)
        if win:
            self.finish_game(gc.WHITE, cells)
            return
        if gc.board_full(self.board, self.board_size):
            self.finish_game(None, None)
            return
        self.set_status(self.tr("your_turn"), (1, 1, 1, 1))
        self.timer_running = True
        self.time_left = config.timer_seconds

    def _challenge_win_in(self):
        try:
            return gc.CHALLENGES[self.challenge_idx - 1]["win_in"]
        except Exception:
            return 3

    # ---------- 提示 / 威胁 ----------
    def show_hint(self):
        if self.game_over:
            return
        if config.mode == "CHALLENGE":
            if not self.replay_mode:
                pos = gc.ai_hint(self.board, self.board_size, gc.BLACK, "高")
                if pos:
                    self.hint_move = pos
                    self.set_status(self.tr("challenge_hint") + f"{pos[0] + 1},{pos[1] + 1}",
                                    (0.2, 1, 0.3, 1))
        elif self.history and config.mode in ("AI", "DOUBLE", "ONLINE"):
            who = gc.BLACK if config.mode in ("AI", "ONLINE") else self.current_player
            pos = gc.ai_hint(self.board, self.board_size, who, "高")
            if pos:
                self.hint_move = pos
                self.set_status(self.tr("hint_show", r=pos[0] + 1, c=pos[1] + 1), (0.2, 1, 0.3, 1))
        self.redraw()

    def hint_autoplay(self):
        if config.mode != "AI" or self.game_over or self.awaiting_ai:
            return
        pos = gc.ai_hint(self.board, self.board_size, gc.BLACK, config.difficulty, config.ai_style)
        if pos is None:
            return
        r, c = pos
        if gc.is_forbidden(self.board, self.board_size, r, c, gc.BLACK, config.forbidden_enabled):
            self.set_status(self.tr("forbidden"), (1, 0.2, 0.2, 1))
            return
        self._try_move(r, c, gc.BLACK)
        self.hint_move = None
        win, cells = gc.check_win(self.board, self.board_size, r, c, gc.BLACK, config.six_in_row)
        if win:
            self.finish_game(gc.BLACK, cells)
            return
        self.set_status(self.tr("ai_thinking"), (1, 1, 1, 1))
        self.awaiting_ai = True
        Clock.schedule_once(self.ai_play, 0.25)

    # ---------- 胜负 / 统计 ----------
    def finish_game(self, winner, cells, forbidden=False, ai_won=False, challenge_pass=False):
        self.game_over = True
        self.winning_cells = cells
        self.timer_running = False
        if self.timer_event:
            self.timer_event.cancel()
        if winner is not None and (winner == gc.BLACK or winner == gc.WHITE):
            self.play_sound("win" if winner == gc.BLACK else "lose")
        elif winner is None:
            self.play_sound("ui")
        self.redraw()
        self.start_confetti()

        result = None
        info = {"moves": self.step_count,
                "six": config.six_in_row,
                "forbidden": forbidden}
        if config.mode == "AI":
            if winner == gc.BLACK:
                result, msg = "win", self.tr("you_win")
            elif winner == gc.WHITE:
                result, msg = "lose", self.tr("ai_win")
            else:
                result, msg = "draw", self.tr("draw")
            info["fast"] = config.timer_enabled and self.step_count <= 20
        elif config.mode == "DOUBLE":
            result = "draw"
            msg = self.tr("draw")
            if winner == gc.BLACK:
                result, msg = "win", self.tr("black") + " " + self.tr("you_win")
            elif winner == gc.WHITE:
                result, msg = "win", self.tr("white") + " " + self.tr("you_win")
        elif config.mode == "CHALLENGE":
            info["challenge"] = True
            if winner == gc.BLACK or challenge_pass:
                result, msg = "win", self.tr("challenge_pass")
            else:
                result, msg = "lose", self.tr("challenge_fail")
            info["fast"] = self.ai_steps <= 3
        elif config.mode == "ONLINE":
            info["online"] = True
            if winner == gc.BLACK:
                result, msg = "win", self.tr("you_win")
            elif winner == gc.WHITE:
                result, msg = "lose", self.tr("ai_win")
            else:
                result, msg = "draw", self.tr("draw")

        if result == "win":
            self.set_status(msg, (0.3, 1, 0.3, 1))
        elif result == "lose":
            self.set_status(msg, (1, 0.3, 0.3, 1))
        else:
            self.set_status(msg, (1, 1, 0, 1))

        stats = gc.load_stats(self.stats_path())
        unlocked = gc.record_game(stats, config.mode.lower(), result, info)
        gc.save_stats(self.stats_path(), stats)
        if unlocked:
            name, desc = gc.achievement_name(unlocked[0])
            self.show_achievement(name, desc)
        self.save_sgf(auto=True)
        if config.auto_save:
            self.save_game()

    def show_achievement(self, name, desc):
        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
        content.add_widget(CJK(self.tr("achievement", name=name), 18, (1, 0.85, 0.2, 1),
                               halign="center"))
        content.add_widget(CJK(desc, 14, halign="center"))
        popup = Popup(title="", content=content, size_hint=(0.85, 0.35))
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2.2)

    def stats_path(self):
        return os.path.join(self._data_dir(), "stats.json")

    def _data_dir(self):
        try:
            return os.path.dirname(os.path.abspath(__file__)) or "."
        except Exception:
            return "."

    # ---------- 悔棋 / 重开 ----------
    def undo(self):
        if self.replay_mode or self.game_over or self.awaiting_ai or config.mode == "ONLINE":
            return
        if not self.history:
            return
        if config.undo_limit >= 0 and self.undo_used >= config.undo_limit:
            self.set_status(self.tr("no_undo"), (1, 0.5, 0.2, 1))
            return
        if config.mode == "CHALLENGE":
            if len(self.history) >= 2:
                for _ in range(2):
                    r, c, who = self.history.pop()
                    self.board[r][c] = gc.EMPTY
                    self.step_count -= 1
                    if who == gc.BLACK:
                        self.ai_steps -= 1
                self.last_move = self.history[-1][:2] if self.history else None
                self.undo_used += 1
                self.redraw()
                self.play_sound("undo")
                self.set_status(self.tr("undo_done", n=max(0, config.undo_limit - self.undo_used)))
            return
        if len(self.history) >= 2:
            for _ in range(2):
                r, c, who = self.history.pop()
                self.board[r][c] = gc.EMPTY
                self.step_count -= 1
            self.last_move = self.history[-1][:2] if self.history else None
            self.undo_used += 1
            self.redraw()
            self.play_sound("undo")
            if config.mode == "DOUBLE":
                if self.history:
                    self.current_player = gc.other(self.history[-1][2])
                else:
                    self.current_player = gc.BLACK
            self.set_status(self.tr("undo_done", n=max(0, config.undo_limit - self.undo_used)))
        else:
            self.set_status(self.tr("no_undo"), (1, 0.5, 0.2, 1))

    def reset(self):
        self.board_size = config.board_size
        self.board = gc.make_board(self.board_size)
        self.history = []
        self.last_move = None
        self.winning_cells = None
        self.game_over = False
        self.awaiting_ai = False
        self.step_count = 0
        self.undo_used = 0
        self.current_player = gc.BLACK
        self.hint_move = None
        self.time_left = config.timer_seconds
        self.ai_steps = 0
        self.piece_anim = {}
        self.confetti = []
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.replay_mode = False
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        if self.replay_event:
            self.replay_event.cancel()
            self.replay_event = None
        if config.mode == "CHALLENGE":
            board, size, who, win_in, hint = gc.challenge_board(self.challenge_idx)
            self.board = board
            self.board_size = size
            self.challenge_active = True
            data = gc.CHALLENGES[self.challenge_idx - 1]
            # 玩家执黑解题（win_in 手内取胜），AI 执白防守
            self.current_player = gc.BLACK
            self.set_status(f"残局 {self.challenge_idx}/10 · {data['name']} · "
                            f"你执黑，{win_in} 手内取胜", (1, 1, 0.6, 1))
        elif config.mode == "AI" and config.ai_first:
            m = self.board_size // 2
            opening = config.opening
            if opening == "星位" and self.board_size >= 9:
                s = 3 if self.board_size >= 13 else 2
                first = (s, s)
            elif opening == "随机":
                rnd = random.Random()
                r = rnd.randint(max(0, m - 3), min(self.board_size - 1, m + 3))
                c = rnd.randint(max(0, m - 3), min(self.board_size - 1, m + 3))
                first = (r, c)
            else:
                first = (m, m)
            self._try_move(first[0], first[1], gc.BLACK)
            self.current_player = gc.WHITE
            self.set_status(f"AI 先手 · {self.tr('white')} 轮到", (1, 1, 1, 1))
        else:
            self.current_player = gc.BLACK
            self.set_status(self.tr("new_game"), (1, 1, 1, 1))
        if config.timer_enabled:
            self.timer_running = True
        # 通知 App 更新回放条可见性
        try:
            app = App.get_running_app()
            if app and hasattr(app, "update_replay_bar"):
                app.update_replay_bar()
        except Exception:
            pass
        self.redraw()

    # ---------- 棋谱 ----------
    def save_sgf(self, auto=False):
        if not self.history:
            return
        d = self._data_dir()
        filename = os.path.join(d, f"game_{int(time.time())}.sgf") if auto else \
            os.path.join(d, "game.sgf")
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(gc.sgf_from_history(self.history, self.board_size))
            if not auto:
                self.set_status(self.tr("saved"), (0.3, 1, 0.3, 1))
        except Exception as e:
            Logger.error("save sgf: %s", e)

    def load_sgf_replay(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                text = f.read()
            moves = gc.parse_sgf(text)
            if not moves:
                self.set_status("无有效棋谱", (1, 0.5, 0.2, 1))
                return
            self.reset()
            self.replay_mode = True
            self.replay_steps = moves
            self.replay_index = 0
            self.board = gc.make_board(self.board_size)
            self.history = []
            self.step_count = 0
            self.set_status(f"回放：{len(moves)} 手", (0.5, 0.9, 1, 1))
            try:
                app = App.get_running_app()
                if app and hasattr(app, "update_replay_bar"):
                    app.update_replay_bar()
            except Exception:
                pass
            self.redraw()
        except Exception as e:
            self.set_status("载入失败", (1, 0.3, 0.3, 1))
            Logger.error("load sgf: %s", e)

    def replay_step(self, delta=1):
        if not self.replay_mode:
            return
        if delta > 0:
            for _ in range(delta):
                if self.replay_index < len(self.replay_steps):
                    r, c, who = self.replay_steps[self.replay_index]
                    self.board[r][c] = who
                    self.last_move = (r, c)
                    self.history.append((r, c, who))
                    self.step_count += 1
                    self.replay_index += 1
        else:
            for _ in range(-delta):
                if self.replay_index > 0:
                    self.replay_index -= 1
                    r, c, who = self.history.pop()
                    self.board[r][c] = gc.EMPTY
                    self.step_count -= 1
                    self.last_move = self.history[-1][:2] if self.history else None
        self.redraw()

    def replay_play_pause(self):
        if not self.replay_mode:
            return
        self.replay_playing = not self.replay_playing
        if self.replay_playing:
            self.replay_event = Clock.schedule_interval(self._replay_tick, 0.7 / self.replay_speed)
        elif self.replay_event:
            self.replay_event.cancel()
            self.replay_event = None

    def _replay_tick(self, dt):
        if self.replay_index >= len(self.replay_steps):
            self.replay_playing = False
            if self.replay_event:
                self.replay_event.cancel()
                self.replay_event = None
            self.set_status("回放结束", (0.5, 0.9, 1, 1))
            return
        self.replay_step(1)

    # ---------- 计时 ----------
    def start_timer(self):
        if not config.timer_enabled:
            return
        if self.timer_event:
            self.timer_event.cancel()
        self.timer_running = True
        self.time_left = config.timer_seconds
        self.timer_event = Clock.schedule_interval(self.update_timer, 1)

    def update_timer(self, dt):
        if self.game_over or not self.timer_running or not config.timer_enabled:
            return
        if self.awaiting_ai:
            return
        self.time_left -= 1
        if self.time_left <= 0:
            self.time_left = 0
            loser = self._timer_player()
            if loser:
                self.set_status(self.tr("timeout"), (1, 0.2, 0.2, 1))
                self.finish_game(gc.other(loser), None)

    # ---------- 自动保存 / 恢复 ----------
    def save_game(self):
        if not config.auto_save or self.replay_mode:
            return
        try:
            data = {
                "mode": config.mode, "size": self.board_size,
                "board": self.board, "history": self.history,
                "step": self.step_count, "current": self.current_player,
                "challenge_idx": self.challenge_idx, "ai_steps": self.ai_steps,
                "ts": time.time(),
            }
            with open(os.path.join(self._data_dir(), "savegame.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass

    def has_savegame(self):
        return os.path.exists(os.path.join(self._data_dir(), "savegame.json"))

    def load_game(self, data):
        self.reset()
        self.board_size = data.get("size", config.board_size)
        self.board = data.get("board", gc.make_board(self.board_size))
        self.history = data.get("history", [])
        self.step_count = data.get("step", len(self.history))
        self.current_player = data.get("current", gc.BLACK)
        self.challenge_idx = data.get("challenge_idx", 1)
        self.ai_steps = data.get("ai_steps", 0)
        if self.history:
            self.last_move = self.history[-1][:2]
        self.set_status("已恢复对局", (0.4, 1, 0.6, 1))
        self.redraw()

    def clear_savegame(self):
        try:
            os.remove(os.path.join(self._data_dir(), "savegame.json"))
        except Exception:
            pass

    # ---------- 网络 ----------
    def start_network(self, is_server, ip=""):
        from network import Network
        self.network = Network()
        if is_server:
            ip = self.network.create_room(on_connected=self.on_net_connect,
                                          on_move_received=self.on_net_move,
                                          on_chat_received=self.on_net_chat,
                                          on_quit=self.on_net_quit)
            return ip
        else:
            self.network.join_room(ip, on_connected=self.on_net_connect,
                                   on_move_received=self.on_net_move,
                                   on_chat_received=self.on_net_chat,
                                   on_quit=self.on_net_quit)

    def on_net_connect(self, success):
        if success:
            self.online = True
            self.my_turn = not self.network.is_server()
            self.set_status("联机成功！" + ("你的回合" if self.my_turn else "等待对方"), (0.3, 1, 0.3, 1))
        else:
            self.set_status("连接失败", (1, 0.3, 0.3, 1))

    def on_net_move(self, r, c):
        if self.board[r][c] != gc.EMPTY:
            return
        self._try_move(r, c, gc.WHITE)
        self.my_turn = True
        win, cells = gc.check_win(self.board, self.board_size, r, c, gc.WHITE, config.six_in_row)
        if win:
            self.finish_game(gc.WHITE, cells)
        else:
            self.set_status("你的回合", (1, 1, 1, 1))

    def on_net_chat(self, text):
        self.chat_lines.append("对方: " + text)
        if len(self.chat_lines) > 30:
            self.chat_lines = self.chat_lines[-30:]

    def on_net_quit(self):
        self.online = False
        self.set_status("对方已断开", (1, 0.5, 0.2, 1))


# =========================
# 主 UI
# =========================
class GomokuApp(App):
    def build(self):
        top_inset, right_inset, bottom_inset, left_inset = get_insets()
        self.top_inset = top_inset
        Window.clearcolor = (0.07, 0.07, 0.1, 1)
        self.root_box = BoxLayout(
            orientation="vertical",
            padding=[dp(4) + left_inset, dp(4) + bottom_inset,
                     dp(4) + right_inset, dp(4) + top_inset],
            spacing=dp(4))

        # 顶栏
        top = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(40), spacing=dp(6))
        self.title_label = CJK(self.tr("title"), 24, (1, 0.85, 0.3, 1), bold=True)
        top.add_widget(self.title_label)
        self.root_box.add_widget(top)

        # 状态栏
        self.status_label = CJK(self.tr("new_game"), 17, size_hint=(1, None), height=dp(30))
        self.root_box.add_widget(self.status_label)

        # 信息行
        info = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(26), spacing=dp(10))
        self.timer_label = CJK("", 14, size_hint_x=0.33, halign="left")
        self.move_label = CJK("", 14, size_hint_x=0.34)
        self.undo_label = CJK("", 14, size_hint_x=0.33, halign="right")
        info.add_widget(self.timer_label)
        info.add_widget(self.move_label)
        info.add_widget(self.undo_label)
        self.root_box.add_widget(info)

        # 棋盘
        self.board = BoardWidget(self.status_label, size_hint=(1, 1))
        self.root_box.add_widget(self.board, index=3)  # 棋盘占满剩余空间

        # 底部控制区（滚动）
        panel = ScrollView(size_hint=(1, None), height=dp(208), do_scroll_x=False)
        grid = GridLayout(cols=4, spacing=dp(6), padding=[dp(2), dp(2), dp(2), dp(2)],
                          size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        def mk_toggle(text, cb, down=False, group=None):
            b = ToggleButton(text=text, font_name="Chinese", font_size=sp(15),
                             state="down" if down else "normal", group=group,
                             size_hint_y=None, height=dp(46))
            def handler(x):
                if x.state == "down":   # 只在“按下生效”时触发，避免组内联动误触
                    cb(x)
            b.bind(on_release=handler)
            return b

        # 模式切换
        self.mode_toggles = {}
        b_ai = mk_toggle(self.tr("mode_ai"), lambda x: self.set_mode("AI"),
                         down=(config.mode == "AI"), group="mode")
        b_double = mk_toggle(self.tr("mode_double"), lambda x: self.set_mode("DOUBLE"),
                             down=(config.mode == "DOUBLE"), group="mode")
        b_challenge = mk_toggle(self.tr("mode_challenge"), lambda x: self.set_mode("CHALLENGE"),
                                down=(config.mode == "CHALLENGE"), group="mode")
        b_online = mk_toggle(self.tr("mode_online"), lambda x: self.online_click(),
                             down=(config.mode == "ONLINE"), group="mode")
        self.mode_toggles = {"AI": b_ai, "DOUBLE": b_double,
                             "CHALLENGE": b_challenge, "ONLINE": b_online}
        grid.add_widget(b_ai)
        grid.add_widget(b_double)
        grid.add_widget(b_challenge)
        grid.add_widget(b_online)

        # 功能按钮
        def add_btn(text, cb):
            b = CJKBtn(text, 15)
            b.bind(on_release=cb)
            grid.add_widget(b)

        add_btn(self.tr("restart"), lambda x: self.board.reset())
        add_btn(self.tr("undo"), lambda x: self.board.undo())
        add_btn(self.tr("hint"), lambda x: self.board.show_hint())
        add_btn(self.tr("ai_move"), lambda x: self.board.hint_autoplay())
        add_btn(self.tr("settings"), lambda x: self.open_settings())
        add_btn(self.tr("stats"), lambda x: self.open_stats())
        add_btn(self.tr("save_sgf"), lambda x: self.board.save_sgf())
        add_btn(self.tr("challenge_sel"), lambda x: self.open_challenge_sel())
        add_btn("威胁", lambda x: self.toggle_threats())
        add_btn(self.tr("fullscreen"), lambda x: self.board.toggle_fullscreen())
        add_btn(self.tr("lang"), lambda x: self.toggle_lang())
        add_btn(self.tr("replay"), lambda x: self.open_replay())

        panel.add_widget(grid)
        self.root_box.add_widget(panel)

        # 回放控制条（默认隐藏，进入回放时显示）
        replay_bar = BoxLayout(orientation="horizontal", size_hint=(1, None),
                               height=dp(44), spacing=dp(4))
        rb1 = CJKBtn(self.tr("prev"), 13)
        rb1.bind(on_release=lambda x: self.board.replay_step(-1))
        rb2 = CJKBtn(self.tr("play"), 13)
        rb2.bind(on_release=lambda x: self.board.replay_play_pause())
        rb3 = CJKBtn(self.tr("next"), 13)
        rb3.bind(on_release=lambda x: self.board.replay_step(1))
        rb4 = CJKBtn(self.tr("speed") + " x2", 13)
        rb4.bind(on_release=lambda x: self.cycle_speed())
        replay_bar.add_widget(rb1)
        replay_bar.add_widget(rb2)
        replay_bar.add_widget(rb3)
        replay_bar.add_widget(rb4)
        self.replay_bar = replay_bar
        self.replay_btns = (rb1, rb2, rb3, rb4)
        self.root_box.add_widget(self.replay_bar)
        self.update_replay_bar()

        Clock.schedule_interval(self.tick_info, 0.5)
        self.board.start_timer()

        if self.board.has_savegame():
            Clock.schedule_once(self.prompt_resume, 0.6)

        return self.root_box

    def update_replay_bar(self):
        """回放条仅在回放模式显示，避免“没反应”的按钮误导用户"""
        visible = getattr(self.board, "replay_mode", False)
        self.replay_bar.opacity = 1.0 if visible else 0.0
        self.replay_bar.disabled = not visible
        for b in self.replay_btns:
            b.disabled = not visible

    def tr(self, key, **kw):
        s = TXT.get(config.lang, TXT["zh"]).get(key, TXT["zh"].get(key, key))
        try:
            return s.format(**kw)
        except Exception:
            return s

    def tick_info(self, dt):
        b = self.board
        if config.timer_enabled and b.timer_running and not b.game_over:
            self.timer_label.text = self.tr("time_left", t=max(0, int(b.time_left)))
        else:
            self.timer_label.text = ""
        self.move_label.text = self.tr("move", n=b.step_count)
        if config.undo_limit >= 0:
            left = max(0, config.undo_limit - b.undo_used)
            self.undo_label.text = f"{self.tr('undo_limit')}: {left}"
        else:
            self.undo_label.text = ""

    def set_mode(self, mode):
        config.mode = mode
        config.save()
        self.board.reset()
        if mode == "CHALLENGE":
            self.board.challenge_idx = 1
        self._sync_mode_ui()

    def _sync_mode_ui(self):
        """让模式切换按钮与当前模式保持一致"""
        try:
            for m, btn in self.mode_toggles.items():
                btn.state = "down" if config.mode == m else "normal"
        except Exception:
            pass

    def toggle_threats(self):
        config.show_threats = not config.show_threats
        config.save()
        self.board.redraw()

    def toggle_lang(self):
        config.lang = "en" if config.lang == "zh" else "zh"
        config.save()
        self.title_label.text = self.tr("title")
        self.status_label.text = self.board.tr("new_game")

    def cycle_speed(self):
        b = self.board
        b.replay_speed = {1.0: 2.0, 2.0: 4.0, 4.0: 0.5, 0.5: 1.0}[b.replay_speed]
        self.replay_btns[3].text = self.tr("speed") + (" x2" if b.replay_speed == 2.0 else
                                                       (" x4" if b.replay_speed == 4.0 else " x0.5" if b.replay_speed == 0.5 else " x1"))
        if b.replay_playing and b.replay_event:
            b.replay_event.cancel()
            b.replay_event = Clock.schedule_interval(b._replay_tick, 0.7 / b.replay_speed)

    # ---------- 弹窗 ----------
    def _popup(self, title, content, size=(0.92, 0.8)):
        box = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        box.add_widget(CJK(title, 18, (1, 0.9, 0.4, 1), size_hint=(1, None), height=dp(32)))
        box.add_widget(content)
        p = Popup(title="", content=box, size_hint=size, auto_dismiss=True)
        self._last_popup = p
        p.open()
        return p

    def open_settings(self):
        b = self.board
        content = BoxLayout(orientation="vertical", padding=dp(4), spacing=dp(6))
        sc = ScrollView()
        gl = GridLayout(cols=2, spacing=dp(8), size_hint_y=None)
        gl.bind(minimum_height=gl.setter("height"))

        def label(t):
            return CJK(t, 15, halign="left", size_hint_x=0.5)

        def spinner(values, value, cb):
            s = Spinner(text=value, values=values, font_name="Chinese",
                        font_size=sp(15), size_hint_y=None, height=dp(44))
            s.bind(text=lambda spn, v: cb(v))
            return s

        def toggle(text, value, cb):
            t = ToggleButton(text=text, state="down" if value else "normal",
                             font_name="Chinese", font_size=sp(15),
                             size_hint_y=None, height=dp(44))
            t.bind(on_release=lambda x: cb(t))
            return t

        gl.add_widget(label("棋盘尺寸"))
        gl.add_widget(spinner([str(v) for v in gc.BOARD_SIZES], str(config.board_size),
                              lambda v: setattr(config, "board_size", int(v))))
        gl.add_widget(label("AI 难度"))
        gl.add_widget(spinner(["低", "中", "高"], config.difficulty,
                              lambda v: setattr(config, "difficulty", v)))
        gl.add_widget(label("AI 风格"))
        gl.add_widget(spinner(["进攻", "防守", "平衡"], config.ai_style,
                              lambda v: setattr(config, "ai_style", v)))
        gl.add_widget(label("棋盘主题"))
        gl.add_widget(spinner(list(THEMES.keys()), config.theme,
                              lambda v: (setattr(config, "theme", v), b.redraw())))
        gl.add_widget(label("棋子风格"))
        gl.add_widget(spinner(["圆形", "方块", "序号"], config.piece_style,
                              lambda v: (setattr(config, "piece_style", v), b.redraw())))

        def forbid_cb(t):
            config.forbidden_enabled = not config.forbidden_enabled
            t.text = "开" if config.forbidden_enabled else "关"
        gl.add_widget(label("禁手规则（黑棋）"))
        gl.add_widget(toggle("开" if config.forbidden_enabled else "关",
                             config.forbidden_enabled, forbid_cb))

        def six_cb(t):
            config.six_in_row = not config.six_in_row
            t.text = "开" if config.six_in_row else "关"
        gl.add_widget(label("六子棋模式"))
        gl.add_widget(toggle("开" if config.six_in_row else "关", config.six_in_row, six_cb))

        def timer_cb(t):
            self.cycle_timer(t, b)
        gl.add_widget(label("每步限时"))
        gl.add_widget(toggle(f"{config.timer_seconds}秒" if config.timer_enabled else "关",
                             config.timer_enabled, timer_cb))

        gl.add_widget(label("悔棋次数（0=禁止）"))
        und_box = BoxLayout(orientation="horizontal", spacing=dp(6))
        und = Slider(min=0, max=10, step=1, value=config.undo_limit)
        und_label = CJK(str(config.undo_limit), 15)
        und.bind(value=lambda s, v: (setattr(config, "undo_limit", int(v)),
                                     setattr(und_label, "text", str(int(v)))))
        und_box.add_widget(und)
        und_box.add_widget(und_label)
        gl.add_widget(und_box)

        def aif_cb(t):
            config.ai_first = not config.ai_first
            t.text = "开" if config.ai_first else "关"
        gl.add_widget(label("AI 先手"))
        gl.add_widget(toggle("开" if config.ai_first else "关", config.ai_first, aif_cb))

        gl.add_widget(label("开局（AI先手）"))
        gl.add_widget(spinner(["天元", "星位", "随机"], config.opening,
                              lambda v: setattr(config, "opening", v)))

        def snd_cb(t):
            config.sound_enabled = not config.sound_enabled
            t.text = "开" if config.sound_enabled else "关"
        gl.add_widget(label("音效"))
        gl.add_widget(toggle("开" if config.sound_enabled else "关", config.sound_enabled, snd_cb))

        def coord_cb(t):
            config.show_coords = not config.show_coords
            t.text = "开" if config.show_coords else "关"
            b.redraw()
        gl.add_widget(label("坐标显示"))
        gl.add_widget(toggle("开" if config.show_coords else "关", config.show_coords, coord_cb))

        gl.add_widget(label("网格颜色"))
        gmap = {"默认": None, "红": (0.8, 0.1, 0.1, 1), "绿": (0.1, 0.6, 0.2, 1),
                "蓝": (0.1, 0.3, 0.8, 1), "白": (0.9, 0.9, 0.9, 1)}
        gl.add_widget(spinner(list(gmap.keys()), "默认",
                              lambda v: (setattr(config, "grid_color", gmap.get(v)), b.redraw())))

        def autos_cb(t):
            config.auto_save = not config.auto_save
            t.text = "开" if config.auto_save else "关"
        gl.add_widget(label("自动保存/恢复"))
        gl.add_widget(toggle("开" if config.auto_save else "关", config.auto_save, autos_cb))

        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        save_btn = CJKBtn(self.tr("ok"), 15)
        save_btn.bind(on_release=lambda x: (config.save(), self._dismiss_last()))
        apply_btn = CJKBtn(self.tr("apply"), 15)
        apply_btn.bind(on_release=lambda x: (config.save(), b.reset()))
        btn_row.add_widget(save_btn)
        btn_row.add_widget(apply_btn)
        gl.add_widget(btn_row)

        sc.add_widget(gl)
        content.add_widget(sc)
        self._popup(self.tr("settings"), content, (0.94, 0.88))

    def _dismiss_last(self):
        try:
            if getattr(self, "_last_popup", None):
                self._last_popup.dismiss()
        except Exception:
            pass

    def cycle_timer(self, btn, board):
        if not config.timer_enabled:
            config.timer_enabled = True
            if config.timer_seconds <= 0:
                config.timer_seconds = 30
        else:
            order = {10: 30, 30: 60, 60: 120, 120: 10}
            config.timer_seconds = order.get(config.timer_seconds, 10)
        btn.text = f"{config.timer_seconds}秒"
        board.time_left = config.timer_seconds

    def open_stats(self):
        stats = gc.load_stats(self.board.stats_path())
        content = BoxLayout(orientation="vertical", padding=dp(4), spacing=dp(4))
        total = stats["total"]
        lines = [
            f"总场次: {total['win'] + total['lose'] + total['draw']}   "
            f"胜: {total['win']}  负: {total['lose']}  平: {total['draw']}",
            f"胜率: {gc.win_rate(stats)}%   当前连胜: {stats['streak']}   "
            f"最佳连胜: {stats['best_streak']}",
            f"残局完成: {stats['challenges_done']}/10",
        ]
        for mode, name in [("ai", "人机"), ("double", "双人"), ("challenge", "残局"),
                           ("online", "联机")]:
            m = stats["modes"][mode]
            lines.append(f"{name}: {m['win']}胜 {m['lose']}负 {m['draw']}平")
        lines.append("")
        lines.append("成就")
        for a in gc.ACHIEVEMENTS:
            got = "已解锁" if a["id"] in stats["achievements"] else "未解锁"
            lines.append(f"[{got}] {a['name']} - {a['desc']}")
        gl = GridLayout(cols=1, size_hint_y=None)
        gl.bind(minimum_height=gl.setter("height"))
        for line in lines:
            gl.add_widget(CJK(line, 14, halign="left", size_hint_y=None, height=dp(28)))
        sc = ScrollView()
        sc.add_widget(gl)
        content.add_widget(sc)
        self._popup(self.tr("stats"), content, (0.94, 0.85))

    def open_replay(self):
        d = self.board._data_dir()
        sgf_files = [f for f in os.listdir(d) if f.endswith(".sgf")] if os.path.isdir(d) else []
        content = BoxLayout(orientation="vertical", padding=dp(4), spacing=dp(6))
        if sgf_files:
            for f in sorted(sgf_files)[-10:]:
                b = CJKBtn(f, 13, size=(dp(360), dp(40)))
                b.bind(on_release=lambda x, fn=f: self._load_replay(fn))
                content.add_widget(b)
        else:
            content.add_widget(CJK("暂无棋谱，先保存一局吧", 15))
        self._popup(self.tr("replay"), content, (0.94, 0.6))

    def _load_replay(self, fn):
        self.board.load_sgf_replay(os.path.join(self.board._data_dir(), fn))

    def open_challenge_sel(self):
        content = BoxLayout(orientation="vertical", padding=dp(4), spacing=dp(6))
        sc = ScrollView()
        gl = GridLayout(cols=2, spacing=dp(6), size_hint_y=None)
        gl.bind(minimum_height=gl.setter("height"))
        for c in gc.CHALLENGES:
            b = CJKBtn(f"{c['id']}. {c['name']}\n{c['desc']}", 13,
                       size=(dp(170), dp(64)))
            b.bind(on_release=lambda x, idx=c["id"]: self._start_challenge(idx))
            gl.add_widget(b)
        sc.add_widget(gl)
        content.add_widget(sc)
        self._popup(self.tr("challenge_sel"), content, (0.94, 0.85))

    def _start_challenge(self, idx):
        config.mode = "CHALLENGE"
        config.save()
        self.board.challenge_idx = idx
        self.board.reset()
        self._sync_mode_ui()

    # ---------- 联机 ----------
    def online_click(self):
        content = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        ip_input = TextInput(hint_text=self.tr("enter_ip"), font_name="Chinese",
                             multiline=False, size_hint_y=None, height=dp(40))
        ip_label = CJK("", 13)

        def do_create(x):
            ip = self.board.start_network(True)
            ip_label.text = f"{self.tr('my_ip')}: {ip}"
            config.mode = "ONLINE"
            self.board.reset()

        def do_join(x):
            ip = ip_input.text.strip()
            if not ip:
                return
            self.board.start_network(False, ip)
            config.mode = "ONLINE"
            self.board.reset()

        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        b1 = CJKBtn(self.tr("create_room"), 14)
        b1.bind(on_release=do_create)
        b2 = CJKBtn(self.tr("join_room"), 14)
        b2.bind(on_release=do_join)
        btn_row.add_widget(b1)
        btn_row.add_widget(b2)
        content.add_widget(btn_row)
        content.add_widget(ip_input)
        content.add_widget(ip_label)
        chat_scroll = ScrollView(size_hint=(1, 0.5))
        chat_gl = GridLayout(cols=1, size_hint_y=None)
        chat_gl.bind(minimum_height=chat_gl.setter("height"))
        chat_scroll.add_widget(chat_gl)
        content.add_widget(chat_scroll)
        chat_input = TextInput(hint_text=self.tr("chat_placeholder"), font_name="Chinese",
                               multiline=False, size_hint_y=None, height=dp(36))
        content.add_widget(chat_input)

        def send_chat(x):
            t = chat_input.text.strip()
            if t and self.board.network and self.board.network.connected:
                self.board.network.send_chat(t)
                self.board.chat_lines.append("我: " + t)
                chat_input.text = ""
            chat_gl.clear_widgets()
            for line in self.board.chat_lines[-20:]:
                chat_gl.add_widget(CJK(line, 13, size_hint_y=None, height=dp(24),
                                       halign="left"))

        def refresh_chat(dt):
            chat_gl.clear_widgets()
            for line in self.board.chat_lines[-20:]:
                chat_gl.add_widget(CJK(line, 13, size_hint_y=None, height=dp(24),
                                       halign="left"))

        chat_input.bind(on_text_validate=send_chat)
        send_btn = CJKBtn(self.tr("send"), 14, size=(dp(120), dp(40)))
        send_btn.bind(on_release=send_chat)
        content.add_widget(send_btn)
        pop = Popup(title="", content=content, size_hint=(0.94, 0.88))
        Clock.schedule_interval(refresh_chat, 1.0)
        pop.bind(on_dismiss=lambda x: Clock.unschedule(refresh_chat))
        pop.open()

    # ---------- 恢复 ----------
    def prompt_resume(self, dt):
        def do_resume(x):
            try:
                with open(os.path.join(self.board._data_dir(), "savegame.json"),
                          "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.board.load_game(data)
                config.mode = data.get("mode", "AI")
            except Exception:
                pass

        def do_discard(x):
            self.board.clear_savegame()

        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        content.add_widget(CJK(self.tr("resume"), 17))
        row = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(46))
        b1 = CJKBtn(self.tr("resume_yes"), 15)
        b1.bind(on_release=do_resume)
        b2 = CJKBtn(self.tr("resume_no"), 15)
        b2.bind(on_release=do_discard)
        row.add_widget(b1)
        row.add_widget(b2)
        content.add_widget(row)
        self._popup("", content, (0.88, 0.38))

    def on_pause(self):
        self.board.save_game()
        return True

    def on_stop(self):
        self.board.save_game()


if __name__ == "__main__":
    GomokuApp().run()
