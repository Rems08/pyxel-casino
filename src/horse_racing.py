import random
import pyxel
from common import BET_INCREMENT, NUM_HORSES, SCREEN_W, draw_text_center

class HorseRaceGame:
    def __init__(self, app) -> None:
        self.app  = app
        self.odds = [0.4, 0.3, 0.2, 0.1]        # must sum to 1
        self.reset()

    # ----------------------------------------------------------------------
    def reset(self) -> None:
        self.bet_idx     = 0
        self.bet_amount  = BET_INCREMENT
        self.positions   = [0] * NUM_HORSES
        self.winner      = None     # None = betting, -1 = racing, >=0 = finished
        self.app.input.reset()

    # ----------------------------------------------------------------------
    def update(self) -> None:
        ih = self.app.input

        # ------------------------ betting phase ----------------------------
        if self.winner is None:
            if pyxel.btnp(pyxel.KEY_LEFT):
                self.bet_idx = (self.bet_idx - 1) % NUM_HORSES
            if pyxel.btnp(pyxel.KEY_RIGHT):
                self.bet_idx = (self.bet_idx + 1) % NUM_HORSES

            if ih.accelerated_press(pyxel.KEY_UP) and \
               self.bet_amount + BET_INCREMENT <= self.app.balance:
                self.bet_amount += BET_INCREMENT
            if ih.accelerated_press(pyxel.KEY_DOWN) and \
               self.bet_amount - BET_INCREMENT >= BET_INCREMENT:
                self.bet_amount -= BET_INCREMENT

            if pyxel.btnp(pyxel.KEY_SPACE):          # start the race
                self.app.balance -= self.bet_amount
                self.positions   = [0] * NUM_HORSES
                self.winner      = -1                 # now racing

            if pyxel.btnp(pyxel.KEY_Q):
                self.app.to_menu()
                return

        # ------------------------ racing phase -----------------------------
        if self.winner == -1:
            for i in range(NUM_HORSES):
                self.positions[i] += random.randint(
                    0, int(3 + self.odds[i] * 5)
                )
                if self.positions[i] >= SCREEN_W - 20:
                    self.winner = i

            if self.winner >= 0:                      # race finished
                payout = int(self.bet_amount / self.odds[self.winner]) \
                         if self.winner == self.bet_idx else 0
                self.app.balance += payout

        # ------------------------ post-race phase --------------------------
        if self.winner is not None and self.winner >= 0:
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.reset()

        if pyxel.btnp(pyxel.KEY_Q):
            self.app.to_menu()

    # ----------------------------------------------------------------------
    def draw(self) -> None:
        if self.winner is None:                       # betting screen ------
            draw_text_center("Horse-race betting", 30, 7)
            for i in range(NUM_HORSES):
                color = 11 if i == self.bet_idx else 7
                draw_text_center(f"Horse {i+1}  |  Odds {self.odds[i]:.2f}",
                                 60 + i * 12, color)
            draw_text_center(f"Bet: ${self.bet_amount}", 120, 11)
            draw_text_center("← → horse  •  ↑ ↓ bet  •  Space start  •  Q menu",
                             220, 5)

        else:                                         # race in progress / end
            for i in range(NUM_HORSES):
                y = 40 + i * 20
                pyxel.rect(self.positions[i], y, 16, 8, 8 + i)
            if self.winner == -1:                     # still racing
                draw_text_center("Racing…", 200, 7)
            else:                                     # finished
                draw_text_center(f"Horse {self.winner + 1} wins!", 200, 11)
                draw_text_center("Press Enter to bet again", 214, 5)
