# -*- coding: utf-8 -*-

import os
import random
import threading

from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.clock import Clock

from network import Network

# =========================
# 中文字体注册
# =========================
FONT_PATH = "NotoSansCJK-Regular.otf"
if os.path.exists(FONT_PATH):
    LabelBase.register(name="Chinese", fn_regular=FONT_PATH)
else:
    # 预防字体文件未找到时的退化处理
    LabelBase.register(name="Chinese", fn_regular=None)

# =========================
# 游戏常量与变量
# =========================
BOARD_SIZE = 19
EMPTY = 0
PLAYER = 1
AI = 2

MODE = "AI"
AI_LEVEL = "中"

# =========================
# 胜利判断
# =========================
def check_win(board, row, col, who):
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for dr, dc in directions:
        cells = [(row, col)]
        
        r, c = row + dr, col + dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == who:
            cells.append((r, c))
            r += dr
            c += dc

        r, c = row - dr, col - dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == who:
            cells.append((r, c))
            r -= dr
            c -= dc

        if len(cells) >= 5:
            return True, cells
    return False, None

# =========================
# AI 评估算法
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
        for i in range(-4, 5):
            r, c = row + dr * i, col + dc * i
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                if i == 0 or board[r][c] == target:
                    result.append("O")
                elif board[r][c] == EMPTY:
                    result.append(".")
                else:
                    result.append("X")
            else:
                result.append("X")
        return result

    for dr, dc in [(1, 0), (0, 1), (1, 1), (1, -1)]:
        total += pattern_score(line(dr, dc, who))
        total += int(pattern_score(line(dr, dc, enemy)) * 0.9)
    return total

def candidate_moves(board):
    moves = set()
    exist = False
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                exist = True
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                            moves.add((nr, nc))
    if not exist:
        return [(BOARD_SIZE // 2, BOARD_SIZE // 2)]
    return list(moves)

def ai_move(board):
    moves = candidate_moves(board)
    if not moves:
        return None

    if AI_LEVEL == "低":
        return random.choice(moves)

    if AI_LEVEL == "高":
        for r, c in moves:
            board[r][c] = AI
            win, _ = check_win(board, r, c, AI)
            board[r][c] = EMPTY
            if win: return r, c

        for r, c in moves:
            board[r][c] = PLAYER
            win, _ = check_win(board, r, c, PLAYER)
            board[r][c] = EMPTY
            if win: return r, c

    best = -1
    result = moves[0]
    for r, c in moves:
        score = evaluate(board, r, c, AI)
        if score > best:
            best = score
            result = (r, c)
    return result

# =========================
# 棋盘 Widget
# =========================
class BoardWidget(Widget):
    def __init__(self, status_label, **kwargs):
        super().__init__(**kwargs)
        self.status_label = status_label
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.history = []
        self.last_move = None
        self.winning_cells = None
        self.game_over = False
        self.awaiting_ai = False

        # 联机相关
        self.network = Network()
        self.online = False
        self.my_turn = False

        self.bind(size=self.redraw, pos=self.redraw)

    def cell_size(self):
        return min(self.width, self.height) / (BOARD_SIZE + 1)

    def origin(self):
        cs = self.cell_size()
        ox = self.x + (self.width - cs * (BOARD_SIZE - 1)) / 2
        oy = self.y + (self.height - cs * (BOARD_SIZE - 1)) / 2
        return ox, oy

    def redraw(self, *args):
        self.canvas.clear()
        cs = self.cell_size()
        ox, oy = self.origin()

        with self.canvas:
            # 背景
            Color(0.86, 0.72, 0.48, 1)
            Rectangle(pos=self.pos, size=self.size)

            # 网格
            Color(0.2, 0.15, 0.1, 1)
            for i in range(BOARD_SIZE):
                Line(points=[ox + i * cs, oy, ox + i * cs, oy + cs * (BOARD_SIZE - 1)], width=1)
                Line(points=[ox, oy + i * cs, ox + cs * (BOARD_SIZE - 1), oy + i * cs], width=1)

            # 棋子
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if self.board[r][c] == EMPTY:
                        continue
                    x, y = ox + c * cs, oy + r * cs
                    radius = cs * 0.4
                    if self.board[r][c] == PLAYER:
                        Color(0.02, 0.02, 0.02, 1)
                    else:
                        Color(0.95, 0.95, 0.95, 1)
                    Ellipse(pos=(x - radius, y - radius), size=(radius * 2, radius * 2))

            # 最后一手提示
            if self.last_move:
                r, c = self.last_move
                Color(1, 0, 0, 1)
                Line(circle=(ox + c * cs, oy + r * cs, cs * 0.15), width=2)

            # 胜利高亮
            if self.winning_cells:
                Color(1, 0.8, 0, 1)
                for r, c in self.winning_cells:
                    Line(circle=(ox + c * cs, oy + r * cs, cs * 0.48), width=3)

    def on_touch_down(self, touch):
        if self.game_over or self.awaiting_ai or not self.collide_point(*touch.pos):
            return

        cs = self.cell_size()
        ox, oy = self.origin()

        col = round((touch.x - ox) / cs)
        row = round((touch.y - oy) / cs)

        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return

        if self.board[row][col] != EMPTY:
            return

        # 联机模式逻辑
        if self.online:
            if not self.my_turn:
                self.set_status("等待对方落子...", (1, 1, 1, 1))
                return

            self.put_piece(row, col, PLAYER)
            self.network.send_move(row, col)
            self.my_turn = False

            win, cells = check_win(self.board, row, col, PLAYER)
            if win:
                self.finish_game(PLAYER, cells)
            else:
                self.set_status("等待对方落子...", (1, 1, 1, 1))
            return

        # 人机模式逻辑
        self.put_piece(row, col, PLAYER)
        win, cells = check_win(self.board, row, col, PLAYER)
        if win:
            self.finish_game(PLAYER, cells)
            return

        self.set_status("AI思考中...", (1, 1, 1, 1))
        self.awaiting_ai = True
        Clock.schedule_once(self.ai_play, 0.3)

    def put_piece(self, row, col, who):
        self.board[row][col] = who
        self.last_move = (row, col)
        self.history.append((row, col, who))
        self.redraw()

    def ai_play(self, dt):
        self.awaiting_ai = False
        pos = ai_move(self.board)
        if not pos:
            return

        r, c = pos
        self.put_piece(r, c, AI)

        win, cells = check_win(self.board, r, c, AI)
        if win:
            self.finish_game(AI, cells)
            return

        self.set_status("轮到你了（黑棋）", (1, 1, 1, 1))

    def online_piece_received(self, r, c):
        """处理网络接收到的对手机"""
        self.put_piece(r, c, AI)
        self.my_turn = True

        win, cells = check_win(self.board, r, c, AI)
        if win:
            self.finish_game(AI, cells)
        else:
            self.set_status("你的回合！", (1, 1, 1, 1))

    def set_status(self, text, color):
        self.status_label.text = text
        self.status_label.color = color

    def finish_game(self, winner, cells):
        self.game_over = True
        self.winning_cells = cells
        self.redraw()

        if winner == PLAYER:
            self.set_status("你赢了！🎉", (0.3, 1, 0.3, 1))
        else:
            self.set_status("对方赢了！", (1, 0.3, 0.3, 1))

    def undo(self):
        """新增：悔棋功能实现"""
        if self.game_over or self.online or self.awaiting_ai:
            return

        # 人机模式：撤销玩家和AI的两步棋
        if len(self.history) >= 2:
            for _ in range(2):
                r, c, _ = self.history.pop()
                self.board[r][c] = EMPTY

            if self.history:
                self.last_move = (self.history[-1][0], self.history[-1][1])
            else:
                self.last_move = None

            self.redraw()
            self.set_status("已悔棋，轮到你了", (1, 1, 1, 1))

    def reset(self):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.history = []
        self.last_move = None
        self.winning_cells = None
        self.game_over = False
        self.awaiting_ai = False
        self.redraw()
        self.set_status("轮到你了", (1, 1, 1, 1))

# =========================
# UI 辅助构建
# =========================
def make_button(text):
    return Button(
        text=text,
        font_name="Chinese",
        font_size=18,
        background_normal="",
        background_color=(0.25, 0.45, 0.7, 1)
    )

# =========================
# 主程序
# =========================
class GomokuApp(App):
    def build(self):
        global MODE

        Window.clearcolor = (0.08, 0.08, 0.1, 1)
        root = BoxLayout(orientation="vertical", padding=10, spacing=8)

        title = Label(text="五子棋对战", font_name="Chinese", font_size=30, size_hint=(1, 0.08))
        status = Label(text="人机模式", font_name="Chinese", font_size=20, size_hint=(1, 0.06))
        board = BoardWidget(status, size_hint=(1, 0.55))

        # 模式切换
        mode_box = BoxLayout(size_hint=(1, 0.08), spacing=5)
        ai_btn = make_button("人机")
        net_btn = make_button("联机")
        mode_box.add_widget(ai_btn)
        mode_box.add_widget(net_btn)

        # 联机区域
        online_box = BoxLayout(size_hint=(1, 0.1), spacing=5)
        ip_input = TextInput(hint_text="输入IP", font_name="Chinese", font_size=16, multiline=False)
        create_btn = make_button("创建房间")
        join_btn = make_button("加入")
        online_box.add_widget(ip_input)
        online_box.add_widget(create_btn)
        online_box.add_widget(join_btn)
        online_box.opacity = 0
        online_box.disabled = True

        # 难度选择
        level_box = BoxLayout(size_hint=(1, 0.08), spacing=5)
        def change_level(level):
            global AI_LEVEL
            AI_LEVEL = level
            status.text = f"难度：{level}"

        for t in ["低", "中", "高"]:
            b = make_button(t)
            b.bind(on_release=lambda x, l=t: change_level(l))
            level_box.add_widget(b)

        # 功能按钮
        button_box = BoxLayout(size_hint=(1, 0.1), spacing=5)
        restart = make_button("重新开始")
        undo = make_button("悔棋")

        restart.bind(on_release=lambda x: board.reset())
        undo.bind(on_release=lambda x: board.undo())

        button_box.add_widget(restart)
        button_box.add_widget(undo)

        # 模式切换事件
        def set_ai(*args):
            global MODE
            MODE = "AI"
            board.online = False
            online_box.opacity = 0
            online_box.disabled = True
            level_box.disabled = False
            status.text = "人机模式"
            board.reset()

        def set_online(*args):
            global MODE
            MODE = "ONLINE"
            board.online = True
            online_box.opacity = 1
            online_box.disabled = False
            level_box.disabled = True
            status.text = "联机模式（请创建或加入房间）"
            board.reset()

        ai_btn.bind(on_release=set_ai)
        net_btn.bind(on_release=set_online)

        # 联机逻辑响应
        def on_network_connect(success):
            if success:
                status.text = "连接成功！你的回合" if board.my_turn else "连接成功！等待对方落子"
            else:
                status.text = "连接失败/中断，请重试"

        def create_room(*args):
            board.my_turn = True
            ip = board.network.create_room(
                on_connected=on_network_connect,
                on_move_received=board.online_piece_received
            )
            status.text = f"房间已创建，本机IP: {ip}"

        def join_room(*args):
            ip = ip_input.text.strip()
            if not ip:
                status.text = "请输入正确的IP"
                return
            board.my_turn = False
            status.text = "正在连接服务器..."
            board.network.join_room(
                ip,
                on_connected=on_network_connect,
                on_move_received=board.online_piece_received
            )

        create_btn.bind(on_release=create_room)
        join_btn.bind(on_release=join_room)

        # 挂载节点
        root.add_widget(title)
        root.add_widget(status)
        root.add_widget(board)
        root.add_widget(mode_box)
        root.add_widget(online_box)
        root.add_widget(level_box)
        root.add_widget(button_box)

        return root

if __name__ == "__main__":
    GomokuApp().run()
