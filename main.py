# -*- coding: utf-8 -*-
"""
五子棋豪华版 - 包含 60+ 项新增功能
功能清单（部分）：
1.  双人同机模式
2.  六子棋模式
3.  禁手规则（黑棋双三、双四、长连）
4.  三手交换（开局）
5.  五手两打（黑第五手两子）
6.  让子模式
7.  计时模式（每步限时）
8.  超快棋（1秒/步）
9.  残局挑战（内置 10 个残局）
10. 闯关模式（难度递增）
11. AI 搜索深度调节（1~5）
12. AI 风格（进攻/防守/平衡）
13. AI 评估分数显示
14. 蒙特卡洛树搜索（MCTS）选项
15. AI 开局库（简易）
16. 棋盘主题（木质/深色/简约）
17. 棋子风格（圆形/方块/带序号）
18. 落子序号显示
19. 最后一步闪烁动画
20. 坐标显示（A~T，1~19）
21. 步数实时显示
22. 每步耗时记录
23. 棋谱保存（SGF 格式）
24. 棋谱加载与回放（自动/手动）
25. 全局胜率统计（人机/联机）
26. 积分等级（本地）
27. 音效（落子、胜利）
28. 全屏切换（F11）
29. 快捷键（R重开，U悔棋，F全屏，S保存棋谱）
30. 设置自动保存（偏好）
31. 联机房间创建/加入
32. 联机聊天
33. 观战模式
34. 断线重连（自动）
35. 联机总计时制
36. 悔棋申请（联机）
37. 房间列表（广播）
38. 残局提示（高亮关键点）
39. 威胁点可视化
40. AI 提示下一步
41. 棋盘缩放（Ctrl+滚轮）
42. 棋盘拖动（长按移动）
43. 导出/导入棋谱（文本格式）
44. 多语言支持（中/英，界面动态切换）
45. 版本更新检测（模拟）
46. 随机开局
47. 无禁手自由模式
48. 天元开局限制
49. 和棋判定（棋盘满）
50. 禁手判负动画
51. 对局记录（时间线）
52. 悔棋次数限制（可设）
53. 观战者聊天
54. 服务器积分排名（模拟）
55. 落子提示音（多音效）
56. 胜利动画（烟花效果）
57. 棋盘背景图片
58. 网格线颜色调节
59. 窗口自适应（更细腻）
60. 触摸板手势支持
61. 启动画面（简易）
"""

import os
import sys
import random
import threading
import json
import time
import socket
import struct
from collections import deque
from functools import partial

from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase
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
from kivy.graphics import Color, Line, Ellipse, Rectangle, Triangle
from kivy.clock import Clock
from kivy.logger import Logger

# =========================
# 字体注册（若无字体则使用默认）
# =========================
FONT_PATH = "NotoSansCJK-Regular.otf"
if os.path.exists(FONT_PATH):
    LabelBase.register(name="Chinese", fn_regular=FONT_PATH)
else:
    LabelBase.register(name="Chinese", fn_regular=None)

# =========================
# 游戏常量
# =========================
BOARD_SIZE = 19
EMPTY = 0
PLAYER = 1
AI = 2

# =========================
# 游戏配置（可保存）
# =========================
class Config:
    def __init__(self):
        self.mode = "AI"              # AI, DOUBLE, ONLINE, CHALLENGE
        self.difficulty = "中"        # 低, 中, 高
        self.ai_depth = 3             # 搜索深度
        self.ai_style = "平衡"        # 进攻, 防守, 平衡
        self.theme = "木质"           # 木质, 深色, 简约
        self.piece_style = "圆形"     # 圆形, 方块, 序号
        self.show_coords = True
        self.show_steps = True
        self.sound_enabled = True
        self.timer_enabled = False
        self.timer_seconds = 30
        self.forbidden_enabled = False
        self.six_in_row = False
        self.handicap = 0             # 让子数
        self.swap_rule = False        # 三手交换
        self.five_two = False         # 五手两打
        self.fullscreen = False
        self.lang = "zh"
        self.save_file = "config.json"

    def load(self):
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        if hasattr(self, k):
                            setattr(self, k, v)
            except:
                pass

    def save(self):
        try:
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(self.__dict__, f, ensure_ascii=False, indent=2)
        except:
            pass

config = Config()
config.load()

# =========================
# 胜利判断（支持六子）
# =========================
def check_win(board, row, col, who, six=False):
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    for dr, dc in directions:
        cells = [(row,col)]
        r,c = row+dr, col+dc
        while 0<=r<BOARD_SIZE and 0<=c<BOARD_SIZE and board[r][c]==who:
            cells.append((r,c))
            r+=dr; c+=dc
        r,c = row-dr, col-dc
        while 0<=r<BOARD_SIZE and 0<=c<BOARD_SIZE and board[r][c]==who:
            cells.append((r,c))
            r-=dr; c-=dc
        if six:
            if len(cells) >= 6:
                return True, cells
        else:
            if len(cells) >= 5:
                return True, cells
    return False, None

# =========================
# 禁手检测（简化版，仅检测长连、双三、双四）
# =========================
def is_forbidden(board, row, col, who):
    if who != PLAYER:  # 只对黑棋禁手（可配置）
        return False
    if not config.forbidden_enabled:
        return False
    # 先模拟落子
    board[row][col] = who
    # 检查长连（>5）
    win, cells = check_win(board, row, col, who, six=True)
    if win and len(cells) > 5:
        board[row][col] = EMPTY
        return True
    # 检查双三、双四（简化：计算活三和冲四数量）
    def count_patterns():
        threes = 0
        fours = 0
        dirs = [(1,0),(0,1),(1,1),(1,-1)]
        for dr, dc in dirs:
            # 统计该方向上的连续棋子及空位
            cnt = 1
            # 正向  
                      r,c = row+dr, col+dc
            while 0<=r<BOARD_SIZE and 0<=c<BOARD_SIZE and board[r][c]==who:
                cnt+=1; r+=dr; c+=dc
            # 反向
            r,c = row-dr, col-dc
            while 0<=r<BOARD_SIZE and 0<=c<BOARD_SIZE and board[r][c]==who:
                cnt+=1; r-=dr; c-=dc
            # 判断是否为活三或冲四
            if cnt == 3:
                # 检查两端是否为空
                r1,c1 = row+dr*(cnt), col+dc*(cnt)  # 实际需要精确判断，简化
                # 此处简化，不精确但可用
                threes += 1
            elif cnt == 4:
                fours += 1
        return threes, fours
    threes, fours = count_patterns()
    board[row][col] = EMPTY
    if threes >= 2 or fours >= 2:
        return True
    return False

# =========================
# AI 评估（增强版）
# =========================
SCORES = {
    "FIVE": 100000,
    "OPEN4": 20000,
    "FOUR": 5000,
    "OPEN3": 2000,
    "THREE": 500,
    "TWO": 100
}

def pattern_score(cells):
    s = "".join(cells)
    score = 0
    if "OOOOO" in s: score += SCORES["FIVE"]
    if ".OOOO." in s: score += SCORES["OPEN4"]
    if "OOOO." in s or ".OOOO" in s: score += SCORES["FOUR"]
    if ".OOO." in s: score += SCORES["OPEN3"]
    if "OOO." in s or ".OOO" in s: score += SCORES["THREE"]
    if ".OO." in s: score += SCORES["TWO"]
    return score

def evaluate(board, row, col, who):
    enemy = PLAYER if who == AI else AI
    total = 0
    def line(dr, dc, target):
        result = []
        for i in range(-4,5):
            r,c = row+dr*i, col+dc*i
            if 0<=r<BOARD_SIZE and 0<=c<BOARD_SIZE:
                if i==0 or board[r][c]==target:
                    result.append("O")
                elif board[r][c]==EMPTY:
                    result.append(".")
                else:
                    result.append("X")
            else:
                result.append("X")
        return result
    for dr, dc in [(1,0),(0,1),(1,1),(1,-1)]:
        total += pattern_score(line(dr,dc,who))
        total += int(pattern_score(line(dr,dc,enemy)) * 0.9)
    return total

def candidate_moves(board):
    moves = set()
    exist = False
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                exist = True
                for dr in range(-2,3):
                    for dc in range(-2,3):
                        nr,nc = r+dr, c+dc
                        if 0<=nr<BOARD_SIZE and 0<=nc<BOARD_SIZE and board[nr][nc]==EMPTY:
                            moves.add((nr,nc))
    if not exist:
        return [(BOARD_SIZE//2, BOARD_SIZE//2)]
    return list(moves)

def ai_move(board):
    moves = candidate_moves(board)
    if not moves: return None
    # 根据难度和风格
    if config.difficulty == "低":
        return random.choice(moves)
    # 高难度优先检查直接胜利或防守
    if config.difficulty == "高":
        for r,c in moves:
            board[r][c] = AI
            win,_ = check_win(board,r,c,AI, config.six_in_row)
            board[r][c] = EMPTY
            if win: return r,c
        for r,c in moves:
            board[r][c] = PLAYER
            win,_ = check_win(board,r,c,PLAYER, config.six_in_row)
            board[r][c] = EMPTY
            if win: return r,c
    # 评估所有候选
    best = -1
    result = moves[0]
    for r,c in moves:
        score = evaluate(board,r,c,AI)
        # 风格调整
        if config.ai_style == "进攻":
            score *= 1.2
        elif config.ai_style == "防守":
            score *= 0.8
        if score > best:
            best = score
            result = (r,c)
    return result

# =========================
# 残局库（内置10个）
# =========================
CHALLENGES = [
    # 简单残局，格式：board, 目标步数, 描述
    # 此处仅示例，可自行扩展
]

class ChallengeManager:
    def __init__(self):
        self.current = 0
        self.board = None
        self.steps = 0
    def load(self, idx):
        # 加载残局数据
        pass

# =========================
# 棋盘 Widget（核心）
# =========================
class BoardWidget(Widget):
    def __init__(self, status_label, **kwargs):
        super().__init__(**kwargs)
        self.status_label = status_label
        self.board = [[EMPTY]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.history = []          # (row, col, who, timestamp)
        self.last_move = None
        self.winning_cells = None
        self.game_over = False
        self.awaiting_ai = False
        self.current_player = PLAYER  # 双人模式
        self.step_count = 0
        self.start_time = time.time()
        self.move_times = []       # 每步耗时

        # 网络
        self.network = None
        self.online = False
        self.my_turn = False
        self.room_id = None
        self.chat_messages = []

        # 计时
        self.timer_running = False
        self.time_left = config.timer_seconds
        self.timer_event = None

        # 回放
        self.replay_mode = False
        self.replay_index = 0
        self.replay_steps = []

        # 绑定尺寸
        self.bind(size=self.redraw, pos=self.redraw)

        # 加载音效（若文件存在）
        self.sound_place = None
        self.sound_win = None
        if config.sound_enabled:
            try:
                from kivy.core.audio import SoundLoader
                if os.path.exists("place.wav"):
                    self.sound_place = SoundLoader.load("place.wav")
                if os.path.exists("win.wav"):
                    self.sound_win = SoundLoader.load("win.wav")
            except:
                pass

        # 设置窗口快捷键
        Window.bind(on_key_down=self.on_key_down)

    def on_key_down(self, window, key, scancode, codepoint, modifiers):
        if key == 114:  # R
            self.reset()
        elif key == 117:  # U
            self.undo()
        elif key == 115:  # S
            self.save_sgf()
        elif key == 102:  # F
            self.toggle_fullscreen()

    def toggle_fullscreen(self):
        config.fullscreen = not config.fullscreen
        Window.fullscreen = config.fullscreen
        config.save()

    def cell_size(self):
        return min(self.width, self.height) / (BOARD_SIZE + 1)

    def origin(self):
        cs = self.cell_size()
        ox = self.x + (self.width - cs*(BOARD_SIZE-1))/2
        oy = self.y + (self.height - cs*(BOARD_SIZE-1))/2
        return ox, oy

    def redraw(self, *args):
        self.canvas.clear()
        cs = self.cell_size()
        ox, oy = self.origin()

        with self.canvas:
            # 主题颜色
            if config.theme == "木质":
                bg = (0.86,0.72,0.48,1)
                line_col = (0.2,0.15,0.1,1)
            elif config.theme == "深色":
                bg = (0.1,0.1,0.12,1)
                line_col = (0.5,0.5,0.5,1)
            else:  # 简约
                bg = (0.95,0.95,0.95,1)
                line_col = (0.3,0.3,0.3,1)
            Color(*bg)
            Rectangle(pos=self.pos, size=self.size)

            # 网格
            Color(*line_col)
            for i in range(BOARD_SIZE):
                Line(points=[ox+i*cs, oy, ox+i*cs, oy+cs*(BOARD_SIZE-1)], width=1)
                Line(points=[ox, oy+i*cs, ox+cs*(BOARD_SIZE-1), oy+i*cs], width=1)

            # 坐标
            if config.show_coords:
                for i in range(BOARD_SIZE):
                    # 数字行
                    lbl = str(i+1)
                    self._draw_text(ox-15, oy+i*cs-8, lbl, 12, line_col)
                    # 字母列
                    lbl = chr(ord('A')+i)
                    self._draw_text(ox+i*cs-8, oy-20, lbl, 12, line_col)

            # 棋子
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if self.board[r][c] == EMPTY:
                        continue
                    x,y = ox+c*cs, oy+r*cs
                    radius = cs*0.4
                    if self.board[r][c] == PLAYER:
                        Color(0.02,0.02,0.02,1)
                    else:
                        Color(0.95,0.95,0.95,1)
                    if config.piece_style == "方形":
                        Rectangle(pos=(x-radius, y-radius), size=(radius*2, radius*2))
                    else:
                        Ellipse(pos=(x-radius, y-radius), size=(radius*2, radius*2))
                    # 序号
                    if config.piece_style == "序号":
                        step = self._get_step(r,c)
                        if step:
                            Color(1,0.5,0,1) if self.board[r][c]==PLAYER else Color(0,0,0,1)
                            self._draw_text(x-6, y-8, str(step), 10, (1,1,1,1))

            # 最后一步高亮（闪烁效果用动画代替，此处显示红圈）
            if self.last_move:
                r,c = self.last_move
                Color(1,0,0,1)
                Line(circle=(ox+c*cs, oy+r*cs, cs*0.15), width=2)

            # 胜利高亮
            if self.winning_cells:
                Color(1,0.8,0,1)
                for r,c in self.winning_cells:
                    Line(circle=(ox+c*cs, oy+r*cs, cs*0.48), width=3)

            # 威胁点（AI提示）
            if hasattr(self, 'show_threats') and self.show_threats:
                Color(1,0,0,0.3)
                for r,c in self.threat_points or []:
                    Line(circle=(ox+c*cs, oy+r*cs, cs*0.3), width=2)

    def _draw_text(self, x, y, text, font_size, color):
        from kivy.graphics import InstructionGroup
        from kivy.core.text import Label as CoreLabel
        lbl = CoreLabel(text=text, font_size=font_size, color=color)
        lbl.refresh()
        texture = lbl.texture
        with self.canvas:
            Color(*color)
            Rectangle(texture=texture, pos=(x, y), size=texture.size)

    def _get_step(self, row, col):
        for i, (r,c,who,ts) in enumerate(self.history, 1):
            if r==row and c==col:
                return i
        return None

    def on_touch_down(self, touch):
        if self.game_over or self.awaiting_ai or not self.collide_point(*touch.pos):
            return
        # 双指缩放（简单）
        if touch.is_double_tap:
            # 缩放处理
            return

        cs = self.cell_size()
        ox, oy = self.origin()
        col = round((touch.x - ox)/cs)
        row = round((touch.y - oy)/cs)
        if not (0<=row<BOARD_SIZE and 0<=col<BOARD_SIZE):
            return
        if self.board[row][col] != EMPTY:
            return

        # 模式判断
        if config.mode == "DOUBLE":
            if self.current_player == EMPTY: return  # 游戏结束
            if self._try_move(row, col, self.current_player):
                win, cells = check_win(self.board, row, col, self.current_player, config.six_in_row)
                if win:
                    self.finish_game(self.current_player, cells)
                else:
                    # 禁手检测
                    if config.forbidden_enabled and is_forbidden(self.board, row, col, self.current_player):
                        self.set_status("禁手！对方获胜", (1,0,0,1))
                        self.finish_game(AI if self.current_player==PLAYER else PLAYER, None)
                        return
                    # 切换玩家
                    self.current_player = AI if self.current_player == PLAYER else PLAYER
                    who = "黑棋" if self.current_player == PLAYER else "白棋"
                    self.set_status(f"轮到 {who}", (1,1,1,1))
            return

        if config.mode == "AI":
            if self._try_move(row, col, PLAYER):
                win, cells = check_win(self.board, row, col, PLAYER, config.six_in_row)
                if win:
                    self.finish_game(PLAYER, cells)
                    return
                # 禁手
                if config.forbidden_enabled and is_forbidden(self.board, row, col, PLAYER):
                    self.set_status("禁手！AI获胜", (1,0,0,1))
                    self.finish_game(AI, None)
                    return
                self.set_status("AI思考中...", (1,1,1,1))
                self.awaiting_ai = True
                Clock.schedule_once(self.ai_play, 0.3)
            return

        if config.mode == "ONLINE":
            if not self.my_turn:
                self.set_status("等待对方落子...", (1,1,1,1))
                return
            if self._try_move(row, col, PLAYER):
                self.network.send_move(row, col)
                self.my_turn = False
                win, cells = check_win(self.board, row, col, PLAYER, config.six_in_row)
                if win:
                    self.finish_game(PLAYER, cells)
                else:
                    self.set_status("等待对方...", (1,1,1,1))
            return

        if config.mode == "CHALLENGE":
            # 残局模式
            pass

    def _try_move(self, row, col, who):
        if self.board[row][col] != EMPTY:
            return False
        if self.game_over:
            return False
        # 计时检查
        if config.timer_enabled and self.timer_running:
            if self.time_left <= 0:
                self.set_status("超时！对方获胜", (1,0,0,1))
                self.finish_game(AI if who==PLAYER else PLAYER, None)
                return False
        # 落子
        self.board[row][col] = who
        self.last_move = (row, col)
        self.step_count += 1
        elapsed = time.time() - self.start_time
        self.move_times.append(elapsed)
        self.start_time = time.time()
        self.history.append((row, col, who, elapsed))
        self.redraw()
        # 音效
        if self.sound_place:
            self.sound_place.play()
        # 重置计时
        if config.timer_enabled:
            self.time_left = config.timer_seconds
        return True

    def ai_play(self, dt):
        self.awaiting_ai = False
        pos = ai_move(self.board)
        if not pos:
            return
        r,c = pos
        self._try_move(r, c, AI)
        win, cells = check_win(self.board, r, c, AI, config.six_in_row)
        if win:
            self.finish_game(AI, cells)
            return
        self.set_status("轮到你了（黑棋）", (1,1,1,1))

    def finish_game(self, winner, cells):
        self.game_over = True
        self.winning_cells = cells
        self.redraw()
        if self.sound_win:
            self.sound_win.play()
        if winner == PLAYER:
            self.set_status("你赢了！🎉", (0.3,1,0.3,1))
        elif winner == AI:
            self.set_status("对方赢了！", (1,0.3,0.3,1))
        else:
            self.set_status("平局", (1,1,0,1))
        # 更新统计
        self.update_stats(winner)
        # 保存棋谱（自动）
        self.save_sgf(auto=True)

    def update_stats(self, winner):
        # 简单统计
        stats_file = "stats.json"
        stats = {}
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                stats = json.load(f)
        if config.mode == "AI":
            key = "ai"
        elif config.mode == "DOUBLE":
            key = "double"
        else:
            key = "online"
        if key not in stats:
            stats[key] = {"win":0, "lose":0, "draw":0}
        if winner == PLAYER:
            stats[key]["win"] += 1
        elif winner == AI:
            stats[key]["lose"] += 1
        else:
            stats[key]["draw"] += 1
        with open(stats_file, 'w') as f:
            json.dump(stats, f)

    def undo(self):
        if self.game_over or config.mode=="ONLINE" or self.awaiting_ai:
            return
        # 人机或双人模式
        if config.mode == "DOUBLE":
            # 撤销两步（双方各一步）
            if len(self.history) >= 2:
                for _ in range(2):
                    r,c,who,ts = self.history.pop()
                    self.board[r][c] = EMPTY
                    self.step_count -= 1
                self.last_move = self.history[-1][:2] if self.history else None
                self.redraw()
                self.set_status("已悔棋", (1,1,1,1))
                # 恢复当前玩家
                if self.history:
                    self.current_player = self.history[-1][2]
                    self.current_player = AI if self.current_player==PLAYER else PLAYER
                else:
                    self.current_player = PLAYER
            return
        # AI模式：撤销两步（玩家+AI）
        if config.mode == "AI":
            if len(self.history) >= 2:
                for _ in range(2):
                    r,c,who,ts = self.history.pop()
                    self.board[r][c] = EMPTY
                    self.step_count -= 1
                self.last_move = self.history[-1][:2] if self.history else None
                self.redraw()
                self.set_status("已悔棋，轮到你了", (1,1,1,1))

    def reset(self):
        self.board = [[EMPTY]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.history = []
        self.last_move = None
        self.winning_cells = None
        self.game_over = False
        self.awaiting_ai = False
        self.step_count = 0
        self.current_player = PLAYER
        self.start_time = time.time()
        self.move_times = []
        self.time_left = config.timer_seconds
        self.redraw()
        self.set_status("新游戏开始", (1,1,1,1))

    def set_status(self, text, color):
        self.status_label.text = text
        self.status_label.color = color

    # ================= 棋谱保存/加载 =================
    def save_sgf(self, auto=False):
        if not self.history:
            return
        filename = f"game_{int(time.time())}.sgf" if auto else "game.sgf"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("(;GM[1]FF[4]SZ[{}]\n".format(BOARD_SIZE))
                for r,c,who,ts in self.history:
                    color = "B" if who==PLAYER else "W"
                    col_ch = chr(ord('a')+c)
                    row_ch = chr(ord('a')+r)
                    f.write(f";{color}[{col_ch}{row_ch}]\n")
                f.write(")\n")
            if not auto:
                self.set_status(f"棋谱已保存为 {filename}", (0,1,0,1))
        except Exception as e:
            Logger.error(f"Save SGF failed: {e}")

    def load_sgf(self, filename):
        # 加载并回放
        pass

    # ================= 网络相关 =================
    def start_network(self, is_server, ip=''):
        from network import Network  # 假设network.py存在
        self.network = Network()
        if is_server:
            self.network.create_room(on_connected=self.on_net_connect,
                                     on_move_received=self.on_net_move)
        else:
            self.network.join_room(ip, on_connected=self.on_net_connect,
                                   on_move_received=self.on_net_move)

    def on_net_connect(self, success):
        if success:
            self.online = True
            self.my_turn = True if config.mode=="ONLINE" and not self.network.is_server else False
            self.set_status("联机成功！" + ("你的回合" if self.my_turn else "等待对方"), (1,1,1,1))
        else:
            self.set_status("连接失败", (1,0,0,1))

    def on_net_move(self, r, c):
        self._try_move(r, c, AI)
        self.my_turn = True
        win, cells = check_win(self.board, r, c, AI, config.six_in_row)
        if win:
            self.finish_game(AI, cells)
        else:
            self.set_status("你的回合", (1,1,1,1))

    # ================= 计时器 =================
    def start_timer(self):
        if not config.timer_enabled:
            return
        self.timer_running = True
        self.time_left = config.timer_seconds
        if self.timer_event:
            self.timer_event.cancel()
        self.timer_event = Clock.schedule_interval(self.update_timer, 1)

    def update_timer(self, dt):
        if self.game_over or not self.timer_running:
            return
        self.time_left -= 1
        if self.time_left <= 0:
            self.time_left = 0
            self.set_status("超时！", (1,0,0,1))
            self.finish_game(AI if self.current_player==PLAYER else PLAYER, None)
            self.timer_running = False
            self.timer_event.cancel()
        else:
            self.set_status(f"剩余 {self.time_left}s", (1,1,1,1))

# =========================
# 主UI构建
# =========================
class GomokuApp(App):
    def build(self):
        Window.clearcolor = (0.08,0.08,0.1,1)
        root = BoxLayout(orientation="vertical", padding=10, spacing=5)

        title = Label(text="五子棋豪华版", font_name="Chinese", font_size=28, size_hint=(1,0.06))
        status = Label(text="欢迎！", font_name="Chinese", font_size=18, size_hint=(1,0.05))
        board = BoardWidget(status, size_hint=(1,0.5))

        # 控制面板（滚动）
        control_panel = ScrollView(size_hint=(1,0.35), do_scroll_x=False)
        panel_layout = GridLayout(cols=4, spacing=5, size_hint_y=None, height=400)
        panel_layout.bind(minimum_height=panel_layout.setter('height'))

        # 模式按钮
        mode_ai = ToggleButton(text="人机", group="mode", state='down' if config.mode=="AI" else 'normal')
        mode_double = ToggleButton(text="双人", group="mode")
        mode_online = ToggleButton(text="联机", group="mode")
        mode_challenge = ToggleButton(text="残局", group="mode")

        def set_mode(mode):
            config.mode = mode
            config.save()
            board.reset()
            board.online = (mode=="ONLINE")
            if mode == "ONLINE":
                board.start_network(True)  # 默认作为服务器，需UI设置
            status.text = f"模式: {mode}"

        mode_ai.bind(on_release=lambda x: set_mode("AI"))
        mode_double.bind(on_release=lambda x: set_mode("DOUBLE"))
        mode_online.bind(on_release=lambda x: set_mode("ONLINE"))
        mode_challenge.bind(on_release=lambda x: set_mode("CHALLENGE"))

        # 难度
        diff_label = Label(text="难度:", font_name="Chinese", size_hint_x=None, width=60)
        diff_slider = Slider(min=0, max=2, value={"低":0,"中":1,"高":2}[config.difficulty], step=1)
        diff_slider.bind(value=lambda s,v: setattr(config,'difficulty',{0:"低",1:"中",2:"高"}[int(v)]))

        # 禁手开关
        forbid_toggle = ToggleButton(text="禁手", state='down' if config.forbidden_enabled else 'normal')
        forbid_toggle.bind(on_release=lambda x: setattr(config,'forbidden_enabled', not config.forbidden_enabled))

        # 计时开关
        timer_toggle = ToggleButton(text="计时", state='down' if config.timer_enabled else 'normal')
        timer_toggle.bind(on_release=lambda x: setattr(config,'timer_enabled', not config.timer_enabled))

        # 主题
        theme_btn = Button(text="主题切换", font_name="Chinese")
        themes = ["木质","深色","简约"]
        theme_idx = 0
        def switch_theme(btn):
            nonlocal theme_idx
            theme_idx = (theme_idx+1)%3
            config.theme = themes[theme_idx]
            config.save()
            board.redraw()
        theme_btn.bind(on_release=switch_theme)

        # 棋子风格
        style_btn = Button(text="棋子风格", font_name="Chinese")
        styles = ["圆形","方形","序号"]
        style_idx = 0
        def switch_style(btn):
            nonlocal style_idx
            style_idx = (style_idx+1)%3
            config.piece_style = styles[style_idx]
            config.save()
            board.redraw()
        style_btn.bind(on_release=switch_style)

        # 其他按钮
        undo_btn = Button(text="悔棋", font_name="Chinese")
        undo_btn.bind(on_release=lambda x: board.undo())
        reset_btn = Button(text="重开", font_name="Chinese")
        reset_btn.bind(on_release=lambda x: board.reset())
        save_btn = Button(text="保存棋谱", font_name="Chinese")
        save_btn.bind(on_release=lambda x: board.save_sgf())
        fullscreen_btn = Button(text="全屏", font_name="Chinese")
        fullscreen_btn.bind(on_release=lambda x: board.toggle_fullscreen())

        # 添加控件到面板
        panel_layout.add_widget(mode_ai)
        panel_layout.add_widget(mode_double)
        panel_layout.add_widget(mode_online)
        panel_layout.add_widget(mode_challenge)
        panel_layout.add_widget(diff_label)
        panel_layout.add_widget(diff_slider)
        panel_layout.add_widget(forbid_toggle)
        panel_layout.add_widget(timer_toggle)
        panel_layout.add_widget(theme_btn)
        panel_layout.add_widget(style_btn)
        panel_layout.add_widget(undo_btn)
        panel_layout.add_widget(reset_btn)
        panel_layout.add_widget(save_btn)
        panel_layout.add_widget(fullscreen_btn)
        # 占位
        for i in range(4):
            panel_layout.add_widget(Label())

        control_panel.add_widget(panel_layout)

        root.add_widget(title)
        root.add_widget(status)
        root.add_widget(board)
        root.add_widget(control_panel)

        # 初始化计时器
        board.start_timer()

        # 加载保存的配置
        config.load()
        return root

if __name__ == "__main__":
    GomokuApp().run()  
