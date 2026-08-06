# -*- coding: utf-8 -*-
"""验证残局：用求解 AI 对防守 AI，检查能否在 win_in 手内获胜"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game_core import CHALLENGES, solve_challenge

if __name__ == "__main__":
    all_ok = True
    for c in CHALLENGES:
        ok, steps = solve_challenge(c["id"], seed=2024)
        status = "OK " if ok and steps <= c["win_in"] else "FAIL"
        if not (ok and steps <= c["win_in"]):
            all_ok = False
        print(f"[{status}] #{c['id']:02d} {c['name']} win_in={c['win_in']} solved_in={steps}")
    print("ALL OK" if all_ok else "SOME FAILED")
    sys.exit(0 if all_ok else 1)
