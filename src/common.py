import pyxel
import collections

# ---------- global configuration ----------
SCREEN_W, SCREEN_H = 256, 256
STARTING_BALANCE = 500
BET_INCREMENT     = 10
NUM_HORSES        = 4

# ---------- helpers ----------
def draw_text_center(text: str, y: int, col: int = 7) -> None:
    """8×8-font text centered on (y)."""
    w = len(text) * 4          # each glyph is 4 px wide in the 8×8 font
    x = (SCREEN_W - w) // 2
    pyxel.text(x, y, text, col)


class InputHelper:
    """
    Handles key-repeat with acceleration so every mini-game can share the
    exact same feel without duplicating code.
    """
    def __init__(self) -> None:
        self._hold = collections.defaultdict(int)

    def accelerated_press(
        self,
        key: int,
        base_interval: int = 12,
        min_interval: int  = 2,
        accel_rate: int    = 10,
    ) -> bool:
        if pyxel.btnp(key):                 # fresh press → immediate trigger
            self._hold[key] = 0
            return True

        if pyxel.btn(key):                  # key held → accelerate
            self._hold[key] += 1
            frames   = self._hold[key]
            interval = max(min_interval, base_interval - frames // accel_rate)
            return frames % interval == 0

        self._hold.pop(key, None)           # released → forget counter
        return False

    def reset(self) -> None:
        self._hold.clear()
