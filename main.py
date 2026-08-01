# -*- coding: utf-8 -*-
"""
五子棋 人机对战
=================
新手向注释版本。核心分四块：
1. 棋盘数据 + 绘制 (Kivy Widget)
2. 胜负判断（附带返回连成五子的具体坐标，用于高亮）
3. AI 对手（基于棋型打分，不用递归 minimax，速度快、逻辑简单，适合入门）
4. 界面交互：悔棋 / 撤回 / 重新开始 + 胜利弹窗反馈
"""

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.clock import Clock

BOARD_SIZE = 15      # 15x15 标准五子棋棋盘
EMPTY, PLAYER, AI = 0, 1, 2


# ---------- 胜负判断 ----------
def check_win(board, row, col, who):
    """检查以 (row, col) 为中心，四个方向是否连成五子。
    返回 (是否获胜, 连成一线的所有坐标列表)，坐标列表用于界面高亮显示。
    """
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for dr, dc in directions:
        cells = [(row, col)]
        # 往一个方向数
        r, c = row + dr, col + dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == who:
            cells.append((r, c))
            r += dr
            c += dc
        # 往反方向数
        r, c = row - dr, col - dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == who:
            cells.append((r, c))
            r -= dr
            c -= dc
        if len(cells) >= 5:
            return True, cells
    return False, None


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
        self.move_history = []   # 记录每一步 (row, col, who)，用于悔棋/撤回
        self.winning_cells = None  # 获胜的连线坐标，用于高亮
        self.game_over = False
        self.awaiting_ai = False   # True 表示玩家已落子，正在等 AI 回应
        self.ai_event = None       # Clock 调度句柄，方便撤回时取消
        self.on_win_callback = None  # 由 App 注入，触发胜利弹窗
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

            # 获胜后，给连成五子的棋子加金色高亮圈
            if self.winning_cells:
                Color(1, 0.82, 0.1, 0.95)
                for (r, c) in self.winning_cells:
                    x = ox + c * cs
                    y = oy + r * cs
                    radius = cs * 0.48
                    Line(circle=(x, y, radius), width=2.4)

    def on_touch_down(self, touch):
        if self.game_over or self.awaiting_ai or not self.collide_point(*touch.pos):
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
        self.move_history.append((row, col, PLAYER))
        self.redraw()

        won, cells = check_win(self.board, row, col, PLAYER)
        if won:
            self.finish_game(PLAYER, cells)
            return
        if self.is_full():
            self.finish_game(None, None)
            return

        self.set_status("AI 思考中...", (0.9, 0.75, 0.3, 1))
        self.awaiting_ai = True
        # 延迟一点点再让 AI 走，避免界面卡顿感；同时留出"撤回"的操作窗口
        self.ai_event = Clock.schedule_once(self.do_ai_move, 0.35)

    def do_ai_move(self, dt):
        self.awaiting_ai = False
        self.ai_event = None
        pos = ai_move(self.board)
        if pos is None:
            self.finish_game(None, None)
            return
        r, c = pos
        self.board[r][c] = AI
        self.move_history.append((r, c, AI))
        self.redraw()

        won, cells = check_win(self.board, r, c, AI)
        if won:
            self.finish_game(AI, cells)
            return
        if self.is_full():
            self.finish_game(None, None)
            return
        self.set_status("轮到你了（黑棋）", (1, 1, 1, 1))

    def is_full(self):
        return all(self.board[r][c] != EMPTY for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))

    def set_status(self, text, color):
        self.status_label.text = text
        self.status_label.color = color

    def finish_game(self, winner, cells):
        """统一处理游戏结束：更新状态文字颜色、高亮连线、弹出结果弹窗。
        winner 为 None 表示平局。
        """
        self.game_over = True
        self.winning_cells = cells
        self.redraw()
        if winner == PLAYER:
            self.set_status("🎉 你赢了！", (0.3, 0.85, 0.35, 1))
        elif winner == AI:
            self.set_status("😅 AI 赢了，再来一局吧", (0.9, 0.35, 0.3, 1))
        else:
            self.set_status("🤝 平局！", (0.8, 0.8, 0.3, 1))
        if self.on_win_callback:
            self.on_win_callback(winner)

    # ---------- 悔棋 / 撤回 ----------
    def retract_last(self):
        """撤回我刚下的这一步：只在"AI 还没回应"的短暂窗口内可用。"""
        if not self.awaiting_ai:
            self.set_status("现在没有可撤回的棋步", self.status_label.color)
            return
        if self.ai_event:
            self.ai_event.cancel()
            self.ai_event = None
        self.awaiting_ai = False
        if self.move_history:
            r, c, who = self.move_history.pop()
            if who == PLAYER:
                self.board[r][c] = EMPTY
        self.set_status("已撤回，轮到你了（黑棋）", (1, 1, 1, 1))
        self.redraw()

    def undo_move(self):
        """悔棋：撤销最近的一整回合（AI 的这步 + 你的上一步），回到你重新落子。
        游戏已结束时也可以悔棋，重新回到对局中。
        """
        if self.awaiting_ai:
            self.set_status("AI 还没落子，请先用「撤回」", self.status_label.color)
            return
        if len(self.move_history) < 2:
            self.set_status("还没有足够的棋步可以悔棋", self.status_label.color)
            return
        for _ in range(2):
            if not self.move_history:
                break
            r, c, who = self.move_history.pop()
            self.board[r][c] = EMPTY
        self.game_over = False
        self.winning_cells = None
        self.set_status("已悔棋，轮到你了（黑棋）", (1, 1, 1, 1))
        self.redraw()

    def reset(self):
        if self.ai_event:
            self.ai_event.cancel()
            self.ai_event = None
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.move_history = []
        self.winning_cells = None
        self.game_over = False
        self.awaiting_ai = False
        self.set_status("轮到你了（黑棋）", (1, 1, 1, 1))
        self.redraw()


def flat_button(text, bg_color):
    """生成一个纯色背景的按钮（不用系统默认贴图，颜色更好看）"""
    return Button(
        text=text,
        background_normal="",
        background_color=bg_color,
        color=(1, 1, 1, 1),
        font_size=17,
        bold=True,
    )


class GomokuApp(App):
    def build(self):
        Window.clearcolor = (0.11, 0.11, 0.13, 1)  # 深色背景，棋盘更突出

        root = BoxLayout(orientation="vertical", padding=10, spacing=8)

        title_label = Label(
            text="[b]五子棋对战[/b]",
            markup=True,
            size_hint=(1, 0.08),
            font_size=24,
            color=(0.95, 0.85, 0.55, 1),
        )
        status_label = Label(
            text="轮到你了（黑棋）",
            size_hint=(1, 0.06),
            font_size=17,
        )
        board = BoardWidget(status_label, size_hint=(1, 0.72))

        def show_result_popup(winner):
            if winner == PLAYER:
                title, msg = "胜利", "🎉 恭喜，你赢了！"
            elif winner == AI:
                title, msg = "再接再厉", "😅 AI 赢了，要不要再来一局？"
            else:
                title, msg = "平局", "🤝 势均力敌，打成平局！"

            content = BoxLayout(orientation="vertical", spacing=12, padding=12)
            content.add_widget(Label(text=msg, font_size=18))
            btn_box = BoxLayout(size_hint=(1, 0.4), spacing=8)
            again_btn = flat_button("再来一局", (0.25, 0.55, 0.3, 1))
            close_btn = flat_button("关闭", (0.35, 0.35, 0.4, 1))
            btn_box.add_widget(again_btn)
            btn_box.add_widget(close_btn)
            content.add_widget(btn_box)

            popup = Popup(title=title, content=content, size_hint=(0.8, 0.4), auto_dismiss=False)

            def do_restart(*_):
                board.reset()
                popup.dismiss()

            again_btn.bind(on_release=do_restart)
            close_btn.bind(on_release=popup.dismiss)
            popup.open()

        board.on_win_callback = show_result_popup

        btn_row = BoxLayout(size_hint=(1, 0.09), spacing=8)
        undo_btn = flat_button("悔棋", (0.3, 0.35, 0.55, 1))
        retract_btn = flat_button("撤回", (0.55, 0.45, 0.25, 1))
        restart_btn = flat_button("重新开始", (0.55, 0.3, 0.3, 1))
        undo_btn.bind(on_release=lambda *_: board.undo_move())
        retract_btn.bind(on_release=lambda *_: board.retract_last())
        restart_btn.bind(on_release=lambda *_: board.reset())
        btn_row.add_widget(undo_btn)
        btn_row.add_widget(retract_btn)
        btn_row.add_widget(restart_btn)

        root.add_widget(title_label)
        root.add_widget(status_label)
        root.add_widget(board)
        root.add_widget(btn_row)
        return root


if __name__ == "__main__":
    GomokuApp().run()
