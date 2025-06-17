import pyxel
from common import SCREEN_W, SCREEN_H, STARTING_BALANCE, draw_text_center, InputHelper
from roulette import RouletteGame
from blackjack import BlackjackGame
from horse_racing import HorseRaceGame


class CasinoApp:
    """Top‑level application – holds balance, menu, game‑over screen."""

    def __init__(self) -> None:
        pyxel.init(SCREEN_W, SCREEN_H, title="Rems Casino 🏨🎰")

        self.balance = STARTING_BALANCE
        self.input   = InputHelper()

        # ---------------------------- state ----------------------------
        self.scene      = "menu"   # "menu" | "Roulette" | "Blackjack" | "Horse" | "game_over"
        self.menu_idx   = 0
        self.menu_items = ["Roulette", "Blackjack", "Horse Race"]

        # ------------------------- sub‑games ---------------------------
        self.roulette  = RouletteGame(self)
        self.blackjack = BlackjackGame(self)
        self.horse     = HorseRaceGame(self)

        pyxel.run(self.update, self.draw)

    # ------------------------------------------------ scene helpers ----
    def to_menu(self) -> None:
        self.scene = "menu"
        self.input.reset()
        self.menu_idx = 0

    # ------------------------------------------------ update loop ------
    def update(self) -> None:
        """Delegates to current scene and monitors bankrupt condition."""
        # bankrupcy check *before* doing anything else
        if self.balance <= 0 and self.scene != "game_over":
            self.scene = "game_over"
            self.input.reset()
            return

        if self.scene == "menu":
            self._update_menu()
        elif self.scene == "Roulette":
            self.roulette.update()
        elif self.scene == "Blackjack":
            self.blackjack.update()
        elif self.scene == "Horse":
            self.horse.update()
        elif self.scene == "game_over":
            self._update_game_over()

    # ---------------------- per‑scene update helpers ------------------
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

    def _update_game_over(self) -> None:
        # Any key? we'll stick to Enter / Space so it matches other screens
        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE):
            self.balance = STARTING_BALANCE
            self.roulette.reset()
            self.blackjack.reset()
            self.horse.reset()
            self.to_menu()

    # ------------------------------------------------ draw loop --------
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
        elif self.scene == "game_over":
            self._draw_game_over()

    # ---------------------- per‑scene draw helpers --------------------
    def _draw_menu(self) -> None:
        draw_text_center("=== Rems Casino ===", 40, 7)
        for idx, name in enumerate(self.menu_items):
            col = 11 if idx == self.menu_idx else 7
            draw_text_center(name, 60 + idx * 10, col)
        draw_text_center("↑↓ move  •  Enter select", 200, 5)

    def _draw_game_over(self) -> None:
        draw_text_center("GAME OVER", 100, 8)
        draw_text_center("You are out of money!", 120, 7)
        draw_text_center("Press Enter to restart with $500", 140, 11)


if __name__ == "__main__":
    CasinoApp()
