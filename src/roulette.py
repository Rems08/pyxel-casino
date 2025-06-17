"""roulette.py – all common bet types + bug‑fixes

New features / fixes
────────────────────
• Added **Even / Odd** betting (2 : 1 payout).
• Controls characters are plain ASCII (`<`, `>`, `^`, `v`) so Pyxel’s 4×6 font
  shows them correctly.
• You can now press **Q** on the result screen to go back to the main menu.
• Result facts are centred for a neat layout.

Bet summary
───────────
    Bet Type        | Keys to cycle | Payout (net)
    ----------------|---------------|--------------
    Number (0‑36)   | TAB           | 35 : 1
    Red / Black     | TAB           | 1 : 1
    Even / Odd      | TAB           | 1 : 1
    Dozen 1‑12 etc. | TAB           | 2 : 1

Keys in betting screen
──────────────────────
    TAB        Cycle bet type
    <  >       Change number / colour / dozen / parity
    ^  v       Stake ± BET_INCREMENT
    Space/Ent  Spin
    Q          Menu
"""
from __future__ import annotations

import random
from enum import Enum, auto
from typing import Dict, List, Tuple

import pyxel
from common import BET_INCREMENT, draw_text_center, InputHelper

# ───────────────────────── wheel layout ────────────────────────────────
ROULETTE_NUMBERS = list(range(37))                # 0‑36
ROULETTE_COLORS: Dict[int, str] = {0: "G"}
for n in ROULETTE_NUMBERS[1:]:                    # simple colour map
    ROULETTE_COLORS[n] = "R" if n % 2 else "B"


# ─────────────────────────── bet types ─────────────────────────────────
class BetType(Enum):
    NUMBER = auto()
    COLOR  = auto()
    PARITY = auto()      # Even / Odd
    DOZEN  = auto()

COLOR_OPTS   = ["R", "B"]           # Red, Black
PARITY_OPTS  = ["Even", "Odd"]
DOZEN_RANGES = [(1, 12), (13, 24), (25, 36)]

# stake * multiplier = return (includes original stake)
PAYOUT_MULT = {
    BetType.NUMBER: 36,   # 35:1
    BetType.COLOR:  2,    # 1:1
    BetType.PARITY: 2,    # 1:1
    BetType.DOZEN:  3,    # 2:1
}


# ────────────────────────── main class ────────────────────────────────
class RouletteGame:
    def __init__(self, app) -> None:
        self.app   = app
        self.input = app.input  # InputHelper shared across scenes
        self.reset()

    # ----------------------------------------------------------------- state
    def reset(self) -> None:
        self.bet_type      = BetType.NUMBER
        self.selection_idx = 0               # meaning depends on type
        self.bet_amount    = BET_INCREMENT
        self.result: int | None = None
        self._spin_ticks   = 0
        self.win_amount    = 0
        self.input.reset()

    # ---------------------------------------------------------------- helpers
    def _sel_label(self) -> str:
        if self.bet_type is BetType.NUMBER:
            return str(self.selection_idx)
        if self.bet_type is BetType.COLOR:
            return "Red" if COLOR_OPTS[self.selection_idx] == "R" else "Black"
        if self.bet_type is BetType.PARITY:
            return PARITY_OPTS[self.selection_idx]
        lo, hi = DOZEN_RANGES[self.selection_idx]
        return f"{lo}-{hi}"

    def _player_wins(self) -> bool:
        n = self.result
        if self.bet_type is BetType.NUMBER:
            return n == self.selection_idx
        if self.bet_type is BetType.COLOR:
            return ROULETTE_COLORS[n] == COLOR_OPTS[self.selection_idx]
        if self.bet_type is BetType.PARITY:
            if n == 0:
                return False  # house wins on zero
            return (n % 2 == 0) if self.selection_idx == 0 else (n % 2 == 1)
        # dozen
        lo, hi = DOZEN_RANGES[self.selection_idx]
        return lo <= n <= hi

    def _move_sel(self, delta: int) -> None:
        if self.bet_type is BetType.NUMBER:
            self.selection_idx = (self.selection_idx + delta) % 37
        elif self.bet_type is BetType.COLOR:
            self.selection_idx = (self.selection_idx + delta) % len(COLOR_OPTS)
        elif self.bet_type is BetType.PARITY:
            self.selection_idx = (self.selection_idx + delta) % len(PARITY_OPTS)
        else:  # DOZEN
            self.selection_idx = (self.selection_idx + delta) % len(DOZEN_RANGES)

    # ----------------------------------------------------------------- update
    def update(self) -> None:
        if self._spin_ticks:                                # spinning…
            self._spin_ticks -= 1
            if self._spin_ticks == 0:                       # settle
                self.result = random.choice(ROULETTE_NUMBERS)
                if self._player_wins():
                    mult = PAYOUT_MULT[self.bet_type]
                    self.win_amount = self.bet_amount * mult
                    self.app.balance += self.win_amount
        else:
            # result screen (result is not None, spin_ticks == 0)
            if self.result is not None:
                if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
                    self.reset()
                if pyxel.btnp(pyxel.KEY_Q):
                    self.app.to_menu()
                return

            # betting screen -------------------------------------------------
            ih = self.input
            # change bet type
            if pyxel.btnp(pyxel.KEY_TAB):
                self.bet_type = BetType((self.bet_type.value % len(BetType)) + 1)
                self.selection_idx = 0

            # change selection
            if pyxel.btnp(pyxel.KEY_LEFT):
                self._move_sel(-1)
            if pyxel.btnp(pyxel.KEY_RIGHT):
                self._move_sel(1)

            # stake
            if ih.accelerated_press(pyxel.KEY_UP) and self.bet_amount + BET_INCREMENT <= self.app.balance:
                self.bet_amount += BET_INCREMENT
            if ih.accelerated_press(pyxel.KEY_DOWN) and self.bet_amount - BET_INCREMENT >= BET_INCREMENT:
                self.bet_amount -= BET_INCREMENT

            # place bet
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
                self.app.balance -= self.bet_amount
                self._spin_ticks = 60  # ~1 second
                self.result = None
                self.win_amount = 0

            if pyxel.btnp(pyxel.KEY_Q):
                self.app.to_menu()

    # ------------------------------------------------------------------- draw
    def draw(self) -> None:
        if self._spin_ticks:
            draw_text_center("Spinning…", 110, 7)
        elif self.result is not None:        # result screen
            self._draw_result()
        else:                                # betting screen
            draw_text_center("Roulette – place your bet", 30, 7)
            draw_text_center(f"Type   : {self.bet_type.name.title()}", 60, 11)
            draw_text_center(f"Choice : {self._sel_label()}", 75, 11)
            draw_text_center(f"Stake  : ${self.bet_amount}", 90, 11)
            draw_text_center("TAB type  •  < > choice  •  ^ V stake  •  Space spin  •  Q menu", 200, 5)

    # detailed result ----------------------------------------------------
    def _draw_result(self) -> None:
        colour = ROULETTE_COLORS[self.result]
        col_code = {"R": 8, "B": 12, "G": 11}[colour]
        draw_text_center(f"Result: {self.result} {colour}", 80, col_code)

        # info lines centred
        facts = [
            f"Colour: {'Red' if colour=='R' else 'Black' if colour=='B' else 'Green'}",
            f"Parity: {'Even' if self.result and self.result % 2 == 0 else 'Odd' if self.result else '–'}",
            f"Dozen : {self._dozen_label(self.result)}",
        ]
        y = 100
        for line in facts:
            draw_text_center(line, y, 7)
            y += 12

        if self.win_amount:
            draw_text_center(f"You win ${self.win_amount}!", y + 10, 11)
        else:
            draw_text_center("No win this time…", y + 10, 8)

        draw_text_center("Space/Enter = next bet  •  Q = menu", y + 24, 5)

    @staticmethod
    def _dozen_label(n: int) -> str:
        if 1 <= n <= 12:
            return "1-12"
        if 13 <= n <= 24:
            return "13-24"
        if 25 <= n <= 36:
            return "25-36"
        return "–"
