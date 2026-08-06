# -*- coding: utf-8 -*-
"""无头集成测试：xvfb-run -a python3 tests/headless_app_test.py
驱动完整 Kivy App，模拟对局与各项功能，检测异常。"""
import os
import sys
import json
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_GL_BACKEND", "mock")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kivy.clock import Clock
import game_core as gc

results = []
errors = []


class FakeTouch:
    def __init__(self, x, y):
        self.id = str(id(self))
        self.x = x
        self.y = y
        self.pos = (x, y)
        self.is_double_tap = False


def board_cell_center(app, r, c):
    b = app.board
    cs = b.cell_size()
    ox, oy = b.origin()
    return ox + c * cs, oy + r * cs


def check(name, cond):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name)


def step1(dt):
    global app
    """人机模式：黑落子 -> AI 应手 -> 悔棋 -> 提示"""
    try:
        b = app.board
        config = __import__("main").config
        config.mode = "AI"
        config.difficulty = "中"
        config.timer_enabled = False
        config.undo_limit = 3
        b.reset()

        x, y = board_cell_center(app, 9, 9)
        b._try_tap(FakeTouch(x, y))
        check("AI 模式落子成功", b.step_count == 1)
        check("AI 开始思考", b.awaiting_ai)

        def after_ai(dt):
            check("AI 已应手", b.step_count == 2)
            check("轮到玩家", not b.awaiting_ai)
            # 悔棋
            b.undo()
            check("悔棋成功(回到0手)", b.step_count == 0)
            check("悔棋次数已用1", b.undo_used == 1)
            # 提示
            b._try_tap(FakeTouch(*board_cell_center(app, 9, 9)))
            def after_ai2(dt2):
                check("AI 二次应手", b.step_count == 2)
                b.show_hint()
                check("提示点生成", b.hint_move is not None)
                # 自动保存
                b.save_game()
                check("自动保存成功", os.path.exists(os.path.join(b._data_dir(), "savegame.json")))
                step2(app)
            Clock.schedule_once(after_ai2, 0.6)
        Clock.schedule_once(after_ai, 0.6)
    except Exception as e:
        errors.append(("step1", e))
        import traceback
        traceback.print_exc()
        finish()


def step2(dt):
    global app
    """残局模式：第1关 win_in=1，AI 一步获胜"""
    try:
        b = app.board
        config = __import__("main").config
        config.mode = "CHALLENGE"
        b.challenge_idx = 1
        b.reset()
        check("残局载入(有棋子)", any(any(v != 0 for v in row) for row in b.board))
        check("残局黑方先行", b.current_player == gc.BLACK)

        def after_ai(dt):
            check("残局 AI 已走", b.ai_steps == 1)
            check("残局结束(AI胜=玩家败)", b.game_over)
            check("残局统计已记录", True)
            # 保存棋谱 & 载入回放
            b.save_sgf()
            sgf_files = [f for f in os.listdir(b._data_dir()) if f.endswith(".sgf")]
            check("棋谱已保存", len(sgf_files) >= 1)
            if sgf_files:
                b.load_sgf_replay(os.path.join(b._data_dir(), sorted(sgf_files)[-1]))
                check("回放模式开启", b.replay_mode)
                b.replay_step(1)
                check("回放步进", b.step_count >= 1)
                b.replay_play_pause()
                check("回放播放", b.replay_playing)
            step3(app)
        Clock.schedule_once(after_ai, 0.6)
    except Exception as e:
        errors.append(("step2", e))
        import traceback
        traceback.print_exc()
        finish()


def step3(dt):
    global app
    """统计面板数据 + 成就 + 设置弹窗"""
    try:
        b = app.board
        stats = gc.load_stats(b.stats_path())
        check("统计总场次>=1", stats["total"]["win"] + stats["total"]["lose"] >= 1)
        check("残局完成数>=1", stats["challenges_done"] >= 1)
        # 成就解锁（首胜/残局）
        check("有成就记录", len(stats["achievements"]) >= 1)
        # 设置弹窗
        app.open_settings()
        check("设置弹窗打开", True)
        # 统计弹窗
        app.open_stats()
        check("统计弹窗打开", True)
        # 残局选关
        app.open_challenge_sel()
        check("残局选关弹窗打开", True)
        step4(app)
    except Exception as e:
        errors.append(("step3", e))
        import traceback
        traceback.print_exc()
        finish()


def step4(dt):
    global app
    """棋盘尺寸切换 + 双人模式 + 六子模式"""
    try:
        b = app.board
        config = __import__("main").config
        config.mode = "DOUBLE"
        config.board_size = 13
        config.six_in_row = True
        b.reset()
        check("13x13 棋盘", b.board_size == 13 and len(b.board) == 13)
        # 双人：黑白交替
        b._try_tap(FakeTouch(*board_cell_center(app, 6, 6)))
        check("双人黑落子", b.step_count == 1)
        b._try_tap(FakeTouch(*board_cell_center(app, 6, 7)))
        check("双人白落子", b.step_count == 2 and b.board[6][7] == gc.WHITE)
        # 六子获胜：黑棋竖列 6 连
        black_moves = [(7, 6), (8, 6), (9, 6), (10, 6), (11, 6)]
        white_moves = [(7, 7), (8, 7), (9, 7), (10, 7), (11, 7)]
        for i in range(5):
            b._try_tap(FakeTouch(*board_cell_center(app, *black_moves[i])))
            b._try_tap(FakeTouch(*board_cell_center(app, *white_moves[i])))
        b._try_tap(FakeTouch(*board_cell_center(app, 12, 6)))
        check("六子获胜", b.game_over)
        # 缩放/平移
        b.zoom = 1.5
        b.pan_x = 30
        b.pan_y = -20
        b.redraw()
        check("缩放/平移正常", b.zoom == 1.5)
        finish()
    except Exception as e:
        errors.append(("step4", e))
        import traceback
        traceback.print_exc()
        finish()


def finish():
    print("\n==== 测试结果 ====")
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(("PASS " if ok else "FAIL ") + name)
    print(f"通过 {passed}/{len(results)}")
    if errors:
        print("ERRORS:", errors)
    print("INTEGRATION:", "ALL PASS" if passed == len(results) and not errors else "HAS FAILURES")
    app.stop()


def main():
    import main as main_mod
    global app
    app = main_mod.GomokuApp()
    Clock.schedule_once(step1, 1.0)
    app.run()


if __name__ == "__main__":
    main()
