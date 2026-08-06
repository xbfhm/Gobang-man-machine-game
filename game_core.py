# -*- coding: utf-8 -*-
"""
game_core.py — 五子棋核心逻辑（纯 Python，无 Kivy 依赖，便于单元测试与复用）

包含：
  * 棋盘、胜负判断（支持连六等变体）
  * 禁手检测（长连 / 双三 / 双四）
  * 威胁点分析（活三、冲四、活四）
  * AI 走子（启发式评估 + 战术：立即获胜 / 防守 / 造活四 / 双杀）
  * 残局挑战（内置 10 关，含“强制性着法”校验）
  * SGF 棋谱 保存 / 解析
  * 统计与成就系统
"""

import json
import os
import random

EMPTY = 0
BLACK = 1   # 黑棋（人机模式中玩家执黑）
WHITE = 2   # 白棋（人机模式中 AI 执白）

DIRS = [(1, 0), (0, 1), (1, 1), (1, -1)]

BOARD_SIZES = [9, 13, 15, 19]


# ============================================================
# 棋盘工具
# ============================================================
def make_board(size, occupied=None):
    """创建 size x size 空棋盘；occupied: [(r,c,who), ...]"""
    board = [[EMPTY] * size for _ in range(size)]
    if occupied:
        for r, c, who in occupied:
            board[r][c] = who
    return board


def in_bounds(size, r, c):
    return 0 <= r < size and 0 <= c < size


def run_ends(board, size, r, c, dr, dc, who):
    """
    返回 (n, plus_end, minus_end)：
      n        —— 过 (r,c) 的连续同色棋子总数
      plus_end —— 正向（+dr,+dc）方向连子外第一格的棋盘值（出界为 None）
      minus_end—— 反向连子外第一格的棋盘值（出界为 None）
    """
    n = 1
    rr, cc = r + dr, c + dc
    while in_bounds(size, rr, cc) and board[rr][cc] == who:
        n += 1
        rr += dr
        cc += dc
    plus_end = board[rr][cc] if in_bounds(size, rr, cc) else None
    rr, cc = r - dr, c - dc
    while in_bounds(size, rr, cc) and board[rr][cc] == who:
        n += 1
        rr -= dr
        cc -= dc
    minus_end = board[rr][cc] if in_bounds(size, rr, cc) else None
    return n, plus_end, minus_end


def count_line(board, size, r, c, dr, dc, who):
    """沿 (dr,dc) 方向统计以 (r,c) 为其中一子的连续同色棋子数"""
    n = 1
    rr, cc = r + dr, c + dc
    while in_bounds(size, rr, cc) and board[rr][cc] == who:
        n += 1
        rr += dr
        cc += dc
    rr, cc = r - dr, c - dc
    while in_bounds(size, rr, cc) and board[rr][cc] == who:
        n += 1
        rr -= dr
        cc -= dc
    return n


def get_cells_line(board, size, r, c, dr, dc, who):
    cells = [(r, c)]
    rr, cc = r + dr, c + dc
    while in_bounds(size, rr, cc) and board[rr][cc] == who:
        cells.append((rr, cc))
        rr += dr
        cc += dc
    rr, cc = r - dr, c - dc
    while in_bounds(size, rr, cc) and board[rr][cc] == who:
        cells.append((rr, cc))
        rr -= dr
        cc -= dc
    return cells


def check_win(board, size, r, c, who, six=False):
    """在 (r,c) 刚落下 who 后，判断是否获胜。返回 (是否获胜, 连子坐标列表)"""
    need = 6 if six else 5
    for dr, dc in DIRS:
        cells = get_cells_line(board, size, r, c, dr, dc, who)
        if len(cells) >= need:
            return True, cells
    return False, None


def any_win(board, size, who, six=False):
    """全盘扫描 who 是否已经获胜"""
    for r in range(size):
        for c in range(size):
            if board[r][c] == who:
                win, cells = check_win(board, size, r, c, who, six)
                if win:
                    return True, cells
    return False, None


def board_full(board, size):
    for r in range(size):
        for c in range(size):
            if board[r][c] == EMPTY:
                return False
    return True


def other(who):
    return WHITE if who == BLACK else BLACK


# ============================================================
# 威胁 / 禁手检测
# ============================================================
def count_four_and_live_three(board, size, r, c, who):
    """
    前提：who 已经落在 (r,c)。
    返回 (fours, live3s)：
      fours  —— 该点参与形成的“四”（冲四 / 活四 / 跳四），每个方向最多计 1
      live3s —— 该点参与形成的“活三”（含跳活三），每个方向最多计 1
    只有“包含新落子点”的威胁才被计入（符合常规禁手判定口径）。
    """
    fours = 0
    live3s = 0
    for dr, dc in DIRS:
        n, plus_end, minus_end = run_ends(board, size, r, c, dr, dc, who)
        dir_four = False
        dir_live3 = False

        # 连续四：n == 4 且至少一端可延伸
        if n == 4 and (plus_end == EMPTY or minus_end == EMPTY):
            dir_four = True
        # 连续活三：n == 3 且两端皆空
        elif n == 3 and plus_end == EMPTY and minus_end == EMPTY:
            dir_live3 = True

        # 跳四 / 跳活三：扫描沿方向的 5 格窗口（窗口必须包含新落子点）
        if not dir_four and not dir_live3:
            for start in range(-4, 1):
                cells = [(r + dr * (start + i), c + dc * (start + i)) for i in range(5)]
                if any(not in_bounds(size, rr, cc) for rr, cc in cells):
                    continue
                if (r, c) not in cells:
                    continue
                seg = [board[rr][cc] for rr, cc in cells]
                stones = sum(1 for v in seg if v == who)
                empties = [i for i, v in enumerate(seg) if v == EMPTY]
                if stones == 4 and len(empties) == 1:
                    dir_four = True
                    break
                if (stones == 3 and len(empties) == 2
                        and empties[0] == 0 and empties[1] == 4):
                    # 两端皆空的三子窗口（.OOO. / O.OO. / OO.O. 等）→ 活三
                    dir_live3 = True
                    break

        if dir_four:
            fours += 1
        elif dir_live3:
            live3s += 1
    return fours, live3s


def count_live_fours(board, size, r, c, who):
    """
    前提：who 已落在 (r,c)。返回该点参与形成的“活四”（两端皆空的四连）方向数。
    注：跳四（如 OO.O / OOO.O）只有唯一连五点，属于冲四而非活四。
    """
    live4 = 0
    for dr, dc in DIRS:
        n, plus_end, minus_end = run_ends(board, size, r, c, dr, dc, who)
        if n == 4 and plus_end == EMPTY and minus_end == EMPTY:
            live4 += 1
    return live4


def is_forbidden(board, size, r, c, who, forbidden_enabled=True):
    """
    禁手判定（仅对黑棋生效）：
      * 长连（超过五连）
      * 双三 / 双四
    调用时 (r,c) 为待落子空点；函数内部模拟落子再还原。
    """
    if not forbidden_enabled or who != BLACK:
        return False
    if not in_bounds(size, r, c) or board[r][c] != EMPTY:
        return False
    board[r][c] = who
    try:
        # 长连
        for dr, dc in DIRS:
            if count_line(board, size, r, c, dr, dc, who) > 5:
                return True
        fours, live3s = count_four_and_live_three(board, size, r, c, who)
        if fours >= 2:
            return True
        if live3s >= 2:
            return True
        return False
    finally:
        board[r][c] = EMPTY


# ============================================================
# AI 启发式评估
# ============================================================
# 按优先级排列的模式表（贪心匹配，防止重复计分）
PATTERNS = [
    ("OOOOO", 10000000),   # 连五
    (".OOOO.", 2000000),   # 活四
    ("OO.OO", 1500000),    # 跳活四
    ("OOOO.", 800000),     # 冲四
    (".OOOO", 800000),
    ("OOO.O", 700000),     # 跳冲四
    ("O.OOO", 700000),
    (".OOO.", 600000),     # 活三
    ("OOO..", 100000),     # 眠三
    ("..OOO", 100000),
    (".OO.O", 90000),
    ("O.OO.", 90000),
    (".OO.", 50000),       # 活二
    ("OO..", 8000),
    ("..OO", 8000),
    (".O.O", 8000),
]


def _line_str(board, size, r, c, dr, dc, who):
    """以 (r,c) 为中心取 9 格直线字符串：who→'O'，空→'.'，对方/边界→'X'"""
    s = []
    for i in range(-4, 5):
        rr, cc = r + dr * i, c + dc * i
        if not in_bounds(size, rr, cc):
            s.append("X")
        elif board[rr][cc] == who:
            s.append("O")
        elif board[rr][cc] == EMPTY:
            s.append(".")
        else:
            s.append("X")
    return "".join(s)


def pattern_score(line):
    score = 0
    for pat, val in PATTERNS:
        if pat in line:
            score += val
    return score


def evaluate_point(board, size, r, c, who, style="平衡"):
    """评估 who 落在 (r,c) 的价值（含对对方威胁的防守权重）"""
    enemy = other(who)
    own = 0
    opp = 0
    for dr, dc in DIRS:
        own += pattern_score(_line_str(board, size, r, c, dr, dc, who))
        opp += pattern_score(_line_str(board, size, r, c, dr, dc, enemy))
    if style == "进攻":
        return own * 1.25 + opp * 0.75
    if style == "防守":
        return own * 0.85 + opp * 1.2
    return own + opp * 0.95


def candidate_moves(board, size, radius=2):
    """返回棋盘上棋子周围 radius 格内的候选空点；空盘返回天元"""
    moves = set()
    any_stone = False
    for r in range(size):
        for c in range(size):
            if board[r][c] != EMPTY:
                any_stone = True
                for dr in range(-radius, radius + 1):
                    for dc in range(-radius, radius + 1):
                        nr, nc = r + dr, c + dc
                        if in_bounds(size, nr, nc) and board[nr][nc] == EMPTY:
                            moves.add((nr, nc))
    if not any_stone:
        return [(size // 2, size // 2)]
    return list(moves)


def ai_move(board, size, who, difficulty="中", style="平衡"):
    """
    AI 决策：
      1) 立即获胜
      2) 封堵对方立即获胜
      3) 高难度：制造活四 / 双杀（双四、双活三）
      4) 启发式评估（带中心偏向与随机打破平局）
    """
    enemy = other(who)
    moves = candidate_moves(board, size)
    if not moves:
        return None

    if difficulty == "低":
        return random.choice(moves)

    # 1) 立即获胜
    for r, c in moves:
        board[r][c] = who
        win, _ = check_win(board, size, r, c, who)
        board[r][c] = EMPTY
        if win:
            return (r, c)

    # 2) 封堵对方立即获胜
    for r, c in moves:
        board[r][c] = enemy
        win, _ = check_win(board, size, r, c, enemy)
        board[r][c] = EMPTY
        if win:
            return (r, c)

    # 3) 高难度战术：制造活四 / 双杀（双四、双活三）
    if difficulty == "高":
        best_tactic = None
        best_key = (-1, -1, -1)   # (live4, fours, live3s)
        for r, c in moves:
            board[r][c] = who
            live4 = count_live_fours(board, size, r, c, who)
            fours, live3s = count_four_and_live_three(board, size, r, c, who)
            board[r][c] = EMPTY
            key = (live4, fours, live3s)
            if key > best_key:
                best_key = key
                best_tactic = (r, c)
        l4, f4, l3 = best_key
        # 活四 / 双四 / 双活三 都是强制杀着
        if l4 >= 1 or f4 >= 2 or l3 >= 2:
            return best_tactic

    # 4) 启发式评估
    best_score = -1
    best_moves = []
    center = (size - 1) / 2.0
    for r, c in moves:
        s = evaluate_point(board, size, r, c, who, style)
        s += (size - abs(r - center) - abs(c - center)) * 5.0  # 中心偏向
        if s > best_score:
            best_score = s
            best_moves = [(r, c)]
        elif s == best_score:
            best_moves.append((r, c))
    return random.choice(best_moves)


def ai_hint(board, size, who, difficulty="高", style="平衡"):
    """返回 AI 建议落点（供提示功能 / 残局提示使用）"""
    return ai_move(board, size, who, difficulty, style)


def threat_points(board, size, who, limit=24):
    """返回对方 who 的威胁点：落子后能形成 四 / 活三 的空点（供可视化）"""
    pts = set()
    moves = candidate_moves(board, size)
    if len(moves) > limit:
        moves = moves[:limit]
    for r, c in moves:
        board[r][c] = who
        live4 = count_live_fours(board, size, r, c, who)
        fours, live3s = count_four_and_live_three(board, size, r, c, who)
        board[r][c] = EMPTY
        if live4 >= 1 or fours >= 1 or live3s >= 1:
            pts.add((r, c))
    return pts


# ============================================================
# 残局挑战
# ============================================================
# 每关：9x9 棋盘（rows 为 9 个字符串），B=黑(解题方)，W=白(防守方)
# win_in：黑棋（AI/玩家解题方）需要的最多手数
CHALLENGES = [
    {
        "id": 1, "name": "一子定音", "win_in": 1,
        "desc": "黑棋一步连五取胜",
        "hint": (4, 8),
        "rows": [
            ".........", ".........", ".........", ".........",
            "....BBBB.", ".........", ".........", ".........", ".........",
        ],
    },
    {
        "id": 2, "name": "斜线绝杀", "win_in": 1,
        "desc": "沿斜线完成五连",
        "hint": (8, 8),
        "rows": [
            ".........", ".........", ".........", ".........",
            "....B....", ".....B...", "......B..", ".......B.", ".........",
        ],
    },
    {
        "id": 3, "name": "活四逼宫", "win_in": 2,
        "desc": "先手造出活四，再连五",
        "hint": (4, 2),
        "rows": [
            ".........", ".........", ".........", ".........",
            "...BBB...", ".........", ".........", ".........", ".........",
        ],
    },
    {
        "id": 4, "name": "双三杀局", "win_in": 3,
        "desc": "一手落下形成横竖双活三",
        "hint": (4, 4),
        "rows": [
            ".........", ".........", ".........",
            "....B....", "...B.B...", "....B....",
            ".........", ".........", ".........",
        ],
    },
    {
        "id": 5, "name": "跳四取胜", "win_in": 1,
        "desc": "补上跳四的空档连五",
        "hint": (4, 6),
        "rows": [
            ".........", ".........", ".........", ".........",
            "....BB.BB", ".........", ".........", ".........", ".........",
        ],
    },
    {
        "id": 6, "name": "双三变奏", "win_in": 3,
        "desc": "斜线与竖线的双活三组合",
        "hint": (4, 4),
        "rows": [
            ".........", ".........", ".........",
            "...BB....", ".........", "....BB...",
            ".........", ".........", ".........",
        ],
    },
    {
        "id": 7, "name": "双冲四", "win_in": 2,
        "desc": "一手造出两个冲四，对手应接不暇",
        "hint": (4, 4),
        "rows": [
            ".........", ".........", ".........", ".........",
            "WBBB.....", "....B....", "....B....", "....B....", "....W....",
        ],
    },
    {
        "id": 8, "name": "声东击西", "win_in": 3,
        "desc": "横线与反斜线的双活三",
        "hint": (4, 4),
        "rows": [
            ".........", ".........", ".........",
            ".....B...", "...B.B...", "...B.....",
            ".........", ".........", ".........",
        ],
    },
    {
        "id": 9, "name": "千里突围", "win_in": 3,
        "desc": "堵白棋活三的同时自建双斜活三",
        "hint": (3, 4),
        "rows": [
            ".........",
            "..B...B..",
            "...B.B...",
            ".....WWW.",
            ".........", ".........", ".........", ".........", ".........",
        ],
    },
    {
        "id": 10, "name": "最终试炼", "win_in": 3,
        "desc": "综合战术：堵冲四 + 竖斜双活三",
        "hint": (3, 4),
        "rows": [
            ".........",
            "..B......",
            "...BB....",
            ".....WWWW",
            "....B....",
            ".........", ".........", ".........", ".........",
        ],
    },
]


def challenge_board(idx):
    """按编号（1 起）构造残局棋盘，返回 (board, size, who, win_in, hint)"""
    data = CHALLENGES[idx - 1]
    size = 9
    board = make_board(size)
    rows = data["rows"]
    for r in range(size):
        for c in range(size):
            ch = rows[r][c]
            if ch == "B":
                board[r][c] = BLACK
            elif ch == "W":
                board[r][c] = WHITE
    return board, size, BLACK, data["win_in"], data["hint"]


def _defense_move(board, size, attacker, defender):
    """
    防守方策略（用于残局校验）：
      1) 自己能赢就赢
      2) 堵住对方立即获胜
      3) 堵住对方“四”威胁点
      4) 堵住对方“活三”威胁点
      5) 随机候选点
    """
    moves = candidate_moves(board, size)
    if not moves:
        return None
    for r, c in moves:
        board[r][c] = defender
        win, _ = check_win(board, size, r, c, defender)
        board[r][c] = EMPTY
        if win:
            return (r, c)
    for r, c in moves:
        board[r][c] = attacker
        win, _ = check_win(board, size, r, c, attacker)
        board[r][c] = EMPTY
        if win:
            return (r, c)
    for r, c in moves:
        board[r][c] = attacker
        live4 = count_live_fours(board, size, r, c, attacker)
        fours, _ = count_four_and_live_three(board, size, r, c, attacker)
        board[r][c] = EMPTY
        if live4 >= 1 or fours >= 1:
            return (r, c)
    for r, c in moves:
        board[r][c] = attacker
        _, live3s = count_four_and_live_three(board, size, r, c, attacker)
        board[r][c] = EMPTY
        if live3s >= 1:
            return (r, c)
    return random.choice(moves)


def defense_move(board, size, attacker, defender):
    """公开的防守策略（供残局模式 AI 防守使用）"""
    return _defense_move(board, size, attacker, defender)


def solve_challenge(idx, seed=2024):
    """
    用求解型 AI（黑）对阵防守 AI（白），返回 (是否在 win_in 手内获胜, 实际手数)。
    """
    board, size, attacker, win_in, _ = challenge_board(idx)
    rnd = random.Random(seed)
    steps = 0
    while steps < win_in:
        move = ai_hint(board, size, attacker, "高")
        if move is None:
            return False, steps
        r, c = move
        board[r][c] = attacker
        steps += 1
        win, _ = check_win(board, size, r, c, attacker)
        if win:
            return True, steps
        if board_full(board, size):
            return False, steps
        dm = _defense_move(board, size, attacker, WHITE)
        if dm is None:
            return True, steps
        dr, dc = dm
        board[dr][dc] = WHITE
        win, _ = check_win(board, size, dr, dc, WHITE)
        if win:
            return False, steps
        if board_full(board, size):
            return False, steps
    return False, steps


# ============================================================
# SGF 棋谱
# ============================================================
def sgf_from_history(history, size):
    """history: [(r, c, who), ...] -> SGF 文本"""
    lines = ["(;GM[1]FF[4]CA[UTF-8]SZ[{}]".format(size)]
    for r, c, who in history:
        color = "B" if who == BLACK else "W"
        lines.append(";{}[{}{}]".format(color, chr(ord('a') + c), chr(ord('a') + r)))
    lines.append(")")
    return "\n".join(lines)


def parse_sgf(text):
    """解析 SGF，返回 [(r, c, who), ...]"""
    import re
    moves = []
    for m in re.finditer(r';([BW])\[([a-zA-Z])([a-zA-Z])\]', text):
        color = BLACK if m.group(1).upper() == "B" else WHITE
        c = ord(m.group(2).lower()) - ord('a')
        r = ord(m.group(3).lower()) - ord('a')
        moves.append((r, c, color))
    return moves


# ============================================================
# 统计与成就
# ============================================================
def default_stats():
    return {
        "modes": {"ai": {"win": 0, "lose": 0, "draw": 0},
                  "double": {"win": 0, "lose": 0, "draw": 0},
                  "challenge": {"win": 0, "lose": 0, "draw": 0},
                  "online": {"win": 0, "lose": 0, "draw": 0}},
        "total": {"win": 0, "lose": 0, "draw": 0},
        "streak": 0, "best_streak": 0,
        "challenges_done": 0,
        "achievements": [],
    }


def load_stats(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        base = default_stats()
        for k, v in data.items():
            if k in base:
                base[k] = v
        return base
    except Exception:
        return default_stats()


def save_stats(path, stats):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


ACHIEVEMENTS = [
    {"id": "first_win", "name": "初露锋芒", "desc": "赢下第一局"},
    {"id": "streak3", "name": "三连胜", "desc": "连续赢下 3 局"},
    {"id": "streak5", "name": "五连胜", "desc": "连续赢下 5 局"},
    {"id": "fast_win", "name": "闪电战", "desc": "限时模式下 20 步内获胜"},
    {"id": "forbidden_win", "name": "规则大师", "desc": "靠对手禁手判负获胜"},
    {"id": "challenge5", "name": "残局专家", "desc": "完成 5 个残局挑战"},
    {"id": "long_game", "name": "持久战", "desc": "单局超过 100 手并获胜"},
    {"id": "online_win", "name": "联机首胜", "desc": "赢得一局联机对局"},
    {"id": "six_win", "name": "六子连珠", "desc": "六子棋模式下获胜"},
]


def record_game(stats, mode, result, info=None):
    """
    记录一局结果并返回新解锁的成就 id 列表。
    result: 'win' / 'lose' / 'draw'（以玩家视角）
    info: dict（fast/forbidden/moves/six/online 等）
    """
    info = info or {}
    mode_key = mode if mode in stats["modes"] else "ai"
    stats["modes"][mode_key][result] += 1
    stats["total"][result] += 1
    if result == "win":
        stats["streak"] += 1
        stats["best_streak"] = max(stats["best_streak"], stats["streak"])
    elif result == "lose":
        stats["streak"] = 0
    if info.get("challenge"):
        stats["challenges_done"] += 1

    unlocked = []
    checks = {
        "first_win": stats["total"]["win"] >= 1,
        "streak3": stats["streak"] >= 3,
        "streak5": stats["streak"] >= 5,
        "fast_win": info.get("fast") and result == "win",
        "forbidden_win": info.get("forbidden") and result == "win",
        "challenge5": stats["challenges_done"] >= 5,
        "long_game": info.get("moves", 0) >= 100 and result == "win",
        "online_win": info.get("online") and result == "win",
        "six_win": info.get("six") and result == "win",
    }
    for aid, ok in checks.items():
        if ok and aid not in stats["achievements"]:
            stats["achievements"].append(aid)
            unlocked.append(aid)
    return unlocked


def achievement_name(aid):
    for a in ACHIEVEMENTS:
        if a["id"] == aid:
            return a["name"], a["desc"]
    return aid, ""


def win_rate(stats):
    t = stats["total"]
    played = t["win"] + t["lose"] + t["draw"]
    if played == 0:
        return 0.0
    return round(t["win"] * 100.0 / played, 1)
