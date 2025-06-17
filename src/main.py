"""
Main entry point – handles the global menu and delegates to each module’s
update/draw.  It is the ONLY file that calls pyxel.run().
"""
import pyxel
from common import SCREEN_W, SCREEN_H, STARTING_BALANCE, draw_text_center, InputHelper
from roulette   import RouletteGame
from blackjack  import BlackjackGame
from horse_racing import HorseRaceGame


class CasinoApp:
    def __init__(self) -> None:
        pyxel.init(SCREEN_W, SCREEN_H, title="Rems Casino 🏨🎰")

        self.balance  = STARTING_BALANCE
        self.input    = InputHelper()

        # --- menu state ---
        self.scene       = "menu"
        self.menu_idx    = 0
        self.menu_items  = ["Roulette", "Blackjack", "Horse Race"]

        # --- sub-games ---
        self.roulette  = RouletteGame(self)
        self.blackjack = BlackjackGame(self)
        self.horse     = HorseRaceGame(self)

        pyxel.run(self.update, self.draw)

    # ----------------------------------------------------- scene helpers --
    def to_menu(self) -> None:
        self.scene = "menu"
        self.input.reset()

    # ----------------------------------------------------- update ---------
    def update(self) -> None:
        if self.scene == "menu":
            self._update_menu()
        elif self.scene == "Roulette":
            self.roulette.update()
        elif self.scene == "Blackjack":
            self.blackjack.update()
        elif self.scene == "Horse":
            self.horse.update()

    def _update_menu(self) -> None:
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.menu_idx = (self.menu_idx + 1) % len(self.menu_items)
        if pyxel.btnp(pyxel.KEY_UP):
            self.menu_idx = (self.menu_idx - 1) % len(self.menu_items)

        if pyxel.btnp(pyxel.KEY_RETURN):
            choice = self.menu_items[self.menu_idx]
            if choice == "Roulette":
                self.scene = "Roulette"
                self.roulette.reset()
            elif choice == "Blackjack":
                self.scene = "Blackjack"
                self.blackjack.start_new()
            else:
                self.scene = "Horse"
                self.horse.reset()

    # ----------------------------------------------------- draw ----------
    def draw(self) -> None:
        pyxel.cls(0)
        draw_text_center(f"Balance: ${self.balance}", 2, 10)

        if self.scene == "menu":
            self._draw_menu()
        elif self.scene == "Roulette":
            self.roulette.draw()
        elif self.scene == "Blackjack":
            self.blackjack.draw()
        elif self.scene == "Horse":
            self.horse.draw()

    def _draw_menu(self) -> None:
        draw_text_center("=== Rems Casino ===", 40, 7)
        for idx, name in enumerate(self.menu_items):
            col = 11 if idx == self.menu_idx else 7
            draw_text_center(name, 60 + idx * 10, col)
        draw_text_center("↑↓ move  •  Enter select", 200, 5)


if __name__ == "__main__":
    CasinoApp()
