# -*- coding: utf-8 -*-
"""game_core 单元测试：python3 tests/test_core.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import game_core as gc


class TestWin(unittest.TestCase):
    def test_five_wins(self):
        b = gc.make_board(15)
        for i in range(4):
            b[7][3 + i] = gc.BLACK
        self.assertFalse(gc.check_win(b, 15, 7, 6, gc.BLACK)[0])
        b[7][7] = gc.BLACK
        ok, cells = gc.check_win(b, 15, 7, 7, gc.BLACK)
        self.assertTrue(ok)
        self.assertEqual(len(cells), 5)

    def test_diagonal(self):
        b = gc.make_board(15)
        for i in range(5):
            b[3 + i][3 + i] = gc.WHITE
        ok, _ = gc.check_win(b, 15, 7, 7, gc.WHITE)
        self.assertTrue(ok)

    def test_six_mode(self):
        b = gc.make_board(15)
        for i in range(6):
            b[7][5 + i] = gc.BLACK
        ok, _ = gc.check_win(b, 15, 7, 10, gc.BLACK, six=True)
        self.assertTrue(ok)
        # 非六子模式：6 连也算胜
        ok2, _ = gc.check_win(b, 15, 7, 10, gc.BLACK, six=False)
        self.assertTrue(ok2)


class TestForbidden(unittest.TestCase):
    def test_double_three(self):
        b = gc.make_board(9)
        for (r, c) in [(3, 4), (4, 3), (4, 5), (5, 4)]:
            b[r][c] = gc.BLACK
        self.assertTrue(gc.is_forbidden(b, 9, 4, 4, gc.BLACK, True))

    def test_double_four(self):
        b = gc.make_board(9)
        for (r, c) in [(4, 1), (4, 2), (4, 3), (5, 4), (6, 4), (7, 4)]:
            b[r][c] = gc.BLACK
        b[4][0] = gc.WHITE
        b[8][4] = gc.WHITE
        self.assertTrue(gc.is_forbidden(b, 9, 4, 4, gc.BLACK, True))

    def test_overline(self):
        b = gc.make_board(15)
        for i in range(6):
            b[7][3 + i] = gc.BLACK
        self.assertTrue(gc.is_forbidden(b, 15, 7, 9, gc.BLACK, True))

    def test_single_live_three_ok(self):
        b = gc.make_board(15)
        for i in range(3):
            b[7][5 + i] = gc.BLACK
        self.assertFalse(gc.is_forbidden(b, 15, 7, 4, gc.BLACK, True))

    def test_disabled(self):
        b = gc.make_board(9)
        for (r, c) in [(3, 4), (4, 3), (4, 5), (5, 4)]:
            b[r][c] = gc.BLACK
        self.assertFalse(gc.is_forbidden(b, 9, 4, 4, gc.BLACK, False))


class TestChallenges(unittest.TestCase):
    def test_all_solvable(self):
        for c in gc.CHALLENGES:
            ok, steps = gc.solve_challenge(c["id"], seed=2024)
            self.assertTrue(ok and steps <= c["win_in"],
                            f"challenge #{c['id']} {c['name']} not solvable in {c['win_in']}")


class TestAI(unittest.TestCase):
    def test_ai_takes_win(self):
        b = gc.make_board(19)
        for i in range(4):
            b[9][5 + i] = gc.WHITE
        r, c = gc.ai_move(b, 19, gc.WHITE, "高")
        self.assertIn((r, c), [(9, 4), (9, 9)])

    def test_ai_blocks(self):
        b = gc.make_board(19)
        for i in range(4):
            b[5][8 + i] = gc.BLACK
        r, c = gc.ai_move(b, 19, gc.WHITE, "高")
        self.assertIn((r, c), [(5, 7), (5, 12)])

    def test_ai_legal(self):
        b = gc.make_board(13)
        b[6][6] = gc.BLACK
        mv = gc.ai_move(b, 13, gc.WHITE, "中")
        self.assertEqual(b[mv[0]][mv[1]], gc.EMPTY)

    def test_full_game_no_crash(self):
        b = gc.make_board(19)
        turn = gc.BLACK
        for _ in range(60):
            mv = gc.ai_move(b, 19, turn, "高")
            if mv is None:
                break
            r, c = mv
            b[r][c] = turn
            win, _ = gc.check_win(b, 19, r, c, turn)
            if win:
                return
            turn = gc.other(turn)
        self.assertTrue(True)  # 没崩溃即可


class TestSGF(unittest.TestCase):
    def test_roundtrip(self):
        hist = [(9, 9, gc.BLACK), (10, 10, gc.WHITE), (8, 8, gc.BLACK)]
        sgf = gc.sgf_from_history(hist, 19)
        parsed = gc.parse_sgf(sgf)
        self.assertEqual(hist, parsed)


class TestStats(unittest.TestCase):
    def test_record_and_achievements(self):
        st = gc.load_stats("/nonexistent")
        unlocked = gc.record_game(st, "ai", "win", {"fast": True, "moves": 10})
        self.assertIn("first_win", unlocked)
        self.assertIn("fast_win", unlocked)
        unlocked2 = gc.record_game(st, "ai", "win", {"fast": True})
        self.assertEqual(unlocked2, [])
        self.assertEqual(gc.win_rate(st), 100.0)
        st2 = gc.load_stats("/nonexistent")
        for _ in range(5):
            gc.record_game(st2, "ai", "win")
        self.assertIn("streak5", st2["achievements"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
