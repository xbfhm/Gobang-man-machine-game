# -*- coding: utf-8 -*-
"""
五子棋 人机对战
=================
新手向注释版本。核心分三块：
1. 棋盘数据 + 绘制 (Kivy Widget)
2. 胜负判断
3. AI 对手（基于棋型打分，不用递归 minimax，速度快、逻辑简单，适合入门）
"""

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Line, Ellipse
from kivy.clock import Clock

BOARD_SIZE = 15      # 15x15 标准五子棋棋盘
EMPTY, PLAYER, AI = 0, 1, 2


# ---------- 胜负判断 ----------
def check_win(board, row, col, who):
    """检查以 (row, col) 为中心，四个方向是否连成五子"""
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1
        # 往一个方向数
        r, c = row + dr, col + dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == who:
            count += 1
            r += dr
            c += dc
        # 往反方向数
        r, c = row - dr, col - dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == who:
            count += 1
            r -= dr
            c -= dc
        if count >= 5:
            return True
    return False


# ---------- AI：给每个候选点打分，选分数最高的 ----------
# 棋型分数表：数字越大表示这个棋型威胁越大
PATTERN_SCORES = {
    "win": 100000,        # 连五
    "open4": 10000,       # 活四 _OOOO_
    "block4": 1000,       # 冲四 OOOO_
    "open3": 1000,        # 活三 _OOO_
    "block3": 200,        # 眠三
    "open2": 100,         # 活二
    "block2": 20,
}


def line_score(cells, who):
    """给一条线（字符串形式，'O'=自己, 'X'=对方, '.'=空）打分"""
    s = "".join(cells)
    my = "O" * 5
    score = 0
    if my in s:
        score += PATTERN_SCORES["win"]
    if "." + "O" * 4 + "." in s:
        score += PATTERN_SCORES["open4"]
    if "OOOO." in s or ".OOOO" in s:
        score += PATTERN_SCORES["block4"]
    if "." + "O" * 3 + "." in s:
        score += PATTERN_SCORES["open3"]
    if "OOO." in s or ".OOO" in s:
        score += PATTERN_SCORES["block3"]
    if "." + "OO" + "." in s:
        score += PATTERN_SCORES["open2"]
    return score


def evaluate_point(board, row, col, who):
    """评估在 (row, col) 落 who 的子之后，四个方向的棋型分数总和"""
    opponent = PLAYER if who == AI else AI

    def get_line(dr, dc, mark_who):
        cells = []
        for i in range(-4, 5):
            r, c = row + dr * i, col + dc * i
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                v = board[r][c]
                if i == 0:
                    cells.append("O")  # 假设这里落子
                elif v == mark_who:
                    cells.append("O")
                elif v == EMPTY:
                    cells.append(".")
                else:
                    cells.append("X")
            else:
                cells.append("X")  # 棋盘外当成堵住
        return cells

    total = 0
    for dr, dc in [(1, 0), (0, 1), (1, 1), (1, -1)]:
        total += line_score(get_line(dr, dc, who), who)          # 进攻分
        total += int(line_score(get_line(dr, dc, opponent), opponent) * 0.9)  # 防守分（挡对方）
    return total


def candidate_moves(board):
    """只考虑已有棋子附近 2 格范围内的空位，减少计算量"""
    candidates = set()
    has_stone = False
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                has_stone = True
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                            candidates.add((nr, nc))
    if not has_stone:
        return [(BOARD_SIZE // 2, BOARD_SIZE // 2)]  # 棋盘为空则下天元
    return list(candidates)


def ai_move(board):
    """遍历候选点，返回分数最高的落子位置"""
    best_score = -1
    best_pos = None
    for r, c in candidate_moves(board):
        score = evaluate_point(board, r, c, AI)
        if score > best_score:
            best_score = score
            best_pos = (r, c)
    return best_pos


# ---------- 界面：棋盘绘制 + 触摸落子 ----------
class BoardWidget(Widget):
    def __init__(self, status_label, **kwargs):
        super().__init__(**kwargs)
        self.status_label = status_label
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.game_over = False
        self.bind(size=self.redraw, pos=self.redraw)

    def cell_size(self):
        return min(self.width, self.height) / (BOARD_SIZE + 1)

    def grid_origin(self):
        cs = self.cell_size()
        # 棋盘居中留边
        ox = self.x + (self.width - cs * (BOARD_SIZE - 1)) / 2
        oy = self.y + (self.height - cs * (BOARD_SIZE - 1)) / 2
        return ox, oy

    def redraw(self, *args):
        self.canvas.clear()
        cs = self.cell_size()
        ox, oy = self.grid_origin()
        with self.canvas:
            Color(0.85, 0.7, 0.45, 1)  # 棋盘底色（木色）
            from kivy.graphics import Rectangle
            Rectangle(pos=self.pos, size=self.size)

            Color(0.2, 0.15, 0.1, 1)
            for i in range(BOARD_SIZE):
                Line(points=[ox + i * cs, oy, ox + i * cs, oy + cs * (BOARD_SIZE - 1)], width=1)
                Line(points=[ox, oy + i * cs, ox + cs * (BOARD_SIZE - 1), oy + i * cs], width=1)

            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    v = self.board[r][c]
                    if v == EMPTY:
                        continue
                    x = ox + c * cs
                    y = oy + r * cs
                    radius = cs * 0.4
                    if v == PLAYER:
                        Color(0.05, 0.05, 0.05, 1)  # 玩家黑棋
                    else:
                        Color(0.95, 0.95, 0.95, 1)  # AI 白棋
                    Ellipse(pos=(x - radius, y - radius), size=(radius * 2, radius * 2))

    def on_touch_down(self, touch):
        if self.game_over or not self.collide_point(*touch.pos):
            return
        cs = self.cell_size()
        ox, oy = self.grid_origin()
        col = round((touch.x - ox) / cs)
        row = round((touch.y - oy) / cs)
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return
        if self.board[row][col] != EMPTY:
            return

        # 玩家落子
        self.board[row][col] = PLAYER
        self.redraw()
        if check_win(self.board, row, col, PLAYER):
            self.status_label.text = "你赢了！"
            self.game_over = True
            return
        if self.is_full():
            self.status_label.text = "平局！"
            self.game_over = True
            return

        self.status_label.text = "AI 思考中..."
        # 延迟一点点再让 AI 走，避免界面卡顿感
        Clock.schedule_once(self.do_ai_move, 0.15)

    def do_ai_move(self, dt):
        pos = ai_move(self.board)
        if pos is None:
            self.status_label.text = "平局！"
            self.game_over = True
            return
        r, c = pos
        self.board[r][c] = AI
        self.redraw()
        if check_win(self.board, r, c, AI):
            self.status_label.text = "AI 赢了，再来一局！"
            self.game_over = True
            return
        if self.is_full():
            self.status_label.text = "平局！"
            self.game_over = True
            return
        self.status_label.text = "轮到你了（黑棋）"

    def is_full(self):
        return all(self.board[r][c] != EMPTY for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))

    def reset(self):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.game_over = False
        self.status_label.text = "轮到你了（黑棋）"
        self.redraw()


class GomokuApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical")
        status_label = Label(text="轮到你了（黑棋）", size_hint=(1, 0.08), font_size=20)
        board = BoardWidget(status_label, size_hint=(1, 0.84))
        restart_btn = Button(text="重新开始", size_hint=(1, 0.08))
        restart_btn.bind(on_release=lambda *_: board.reset())

        root.add_widget(status_label)
        root.add_widget(board)
        root.add_widget(restart_btn)
        return root


if __name__ == "__main__":
    GomokuApp().run()
