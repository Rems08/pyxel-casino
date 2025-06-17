import random
import pyxel
from common import BET_INCREMENT, SCREEN_W, draw_text_center, InputHelper

# ----- wheel layout -----
ROULETTE_NUMBERS = list(range(37))          # 0-36
ROULETTE_COLORS  = {0: "G"}                 # green zero
for n in ROULETTE_NUMBERS[1:]:
    ROULETTE_COLORS[n] = "R" if n % 2 else "B"  # crude red/black map


class RouletteGame:
    def __init__(self, app) -> None:
        """
        app is the main CasinoApp instance (for shared balance & scene switch)
        """
        self.app          = app
        self.bet_num      = 0
        self.bet_amount   = BET_INCREMENT
        self.result       = None
        self._spin_ticks  = 0                # >0 means wheel is spinning

    # ------------------------------------------------------------------ logic
    def reset(self) -> None:
        self.bet_num    = 0
        self.bet_amount = BET_INCREMENT
        self.result     = None
        self._spin_ticks = 0
        self.app.input.reset()

    def update(self) -> None:
        ih = self.app.input
        if self._spin_ticks:                 # animation phase -------------
            self._spin_ticks -= 1
            if not self._spin_ticks:         # spin finished: settle bet
                self.result = random.choice(ROULETTE_NUMBERS)
                if self.result == self.bet_num:
                    self.app.balance += 35 * self.bet_amount
            # allow player to leave at any time
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
                self.reset()
        else:                                # betting phase ---------------
            if pyxel.btnp(pyxel.KEY_LEFT):
                self.bet_num = (self.bet_num - 1) % len(ROULETTE_NUMBERS)
            if pyxel.btnp(pyxel.KEY_RIGHT):
                self.bet_num = (self.bet_num + 1) % len(ROULETTE_NUMBERS)

            if ih.accelerated_press(pyxel.KEY_UP)  and \
               self.bet_amount + BET_INCREMENT <= self.app.balance:
                self.bet_amount += BET_INCREMENT
            if ih.accelerated_press(pyxel.KEY_DOWN) and \
               self.bet_amount - BET_INCREMENT >= BET_INCREMENT:
                self.bet_amount -= BET_INCREMENT

            if pyxel.btnp(pyxel.KEY_SPACE):          # place bet & spin
                self.app.balance -= self.bet_amount
                self._spin_ticks = 60                # frames
                self.result = None

            if pyxel.btnp(pyxel.KEY_Q):              # back to menu
                self.app.to_menu()

    # ----------------------------------------------------------------- draw
    def draw(self) -> None:
        if self._spin_ticks:                         # spinning -------------
            draw_text_center("Spinning...", 100, 7)
            if self._spin_ticks == 0:                # just finished
                col = {"R": 8, "B": 12, "G": 11}[ROULETTE_COLORS[self.result]]
                draw_text_center(f"Result: {self.result} "
                                  f"{ROULETTE_COLORS[self.result]}",
                                  120, col)
                draw_text_center("Press Space / Enter", 140, 7)
        else:                                        # betting --------------
            draw_text_center("Roulette – pick a number", 30, 7)
            draw_text_center(f"Bet number : {self.bet_num}",   50, 11)
            draw_text_center(f"Bet amount : ${self.bet_amount}", 70, 11)
            draw_text_center("← → number  •  ↑ ↓ amount  •  Space spin  •  Q menu",
                             220, 5)
