"""roulette_wheel_animation.py – self‑contained Pyxel demo

Press <Space> and watch the wheel accelerate, coast, then decelerate so the
randomly‑chosen winning number stops exactly at the pointer (12 o’clock).
You can embed the `RouletteWheel` class into your game or just run this file to
see the effect.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List

import pyxel

# ───────────────────────── config / constants ───────────────────────────
SCREEN_W, SCREEN_H = 256, 256
CENTER_X, CENTER_Y = SCREEN_W // 2, SCREEN_H // 2
WHEEL_RADIUS       = 90
NUM_SLOTS          = 37                             # 0‑36 (single‑zero)

# simple colour mapping (palette index → Pyxel colour)
COL_RED, COL_BLACK, COL_GREEN = 8, 12, 11

SLOT_COLOURS: Dict[int, int] = {0: COL_GREEN}
for n in range(1, NUM_SLOTS):
    SLOT_COLOURS[n] = COL_RED if n % 2 else COL_BLACK

TEXT_COL            = 7
POINTER_COL         = 7
ACCEL_PHASE_FRAMES  = 40      # frames of constant acceleration
CONSTANT_PHASE_FRAMES = 40    # frames at peak speed before braking

MAX_ANGVEL          = 0.45    # radians per frame at peak (empirical)
BRAKE_RATE          = 0.985   # multiply ω each frame while braking

# Pre‑compute slot angles (0 at 12 o’clock, clockwise positive)
SLOT_ANGLE: List[float] = [i * 2 * math.pi / NUM_SLOTS for i in range(NUM_SLOTS)]


# ─────────────────────────── helper class ───────────────────────────────
class RouletteWheel:
    """
    A self-contained wheel that can be dropped into any Pyxel scene.

    Added since the first version
    ─────────────────────────────
    • Accepts custom centre (cx, cy) and radius – so your casino scene can
      decide where/how big the wheel is.
    • start_spin(target_number) lets the caller predetermine the result (or
      omit the argument to get a random one).
    • `is_spinning` property used by roulette.py to know when the wheel stops.
    """

    def __init__(self, cx: int = CENTER_X, cy: int = CENTER_Y,
                 radius: int = WHEEL_RADIUS) -> None:
        self.cx      = cx
        self.cy      = cy
        self.radius  = radius
        self.reset()

    # ---------------------------------------------------------- state ----
    def reset(self) -> None:
        self.phase      = "idle"          # idle | accel | cruise | brake | done
        self.angle      = 0.0
        self.ang_vel    = 0.0
        self.timer      = 0
        self.result: int | None = None
        self.target_angle = 0.0            # filled in start_spin()

    # ---------------------------------------------------------- spin -----
    def start_spin(self, target_number: int | None = None) -> None:
        """
        Begin a new spin.

        • target_number 0-36 → wheel will stop on that pocket  
        • target_number None → a random number is chosen
        """
        self.reset()
        self.result = (random.randrange(NUM_SLOTS)
                       if target_number is None else target_number)
        # compute the angle needed so that the chosen pocket ends at 12 o’clock
        self.target_angle = (-SLOT_ANGLE[self.result]) % (2 * math.pi)

        self.phase   = "accel"
        self.ang_vel = 0.0
        self.timer   = 0

    # ----------------------------------------------------- handy flag ----
    @property
    def is_spinning(self) -> bool:
        return self.phase not in {"idle", "done"}

    # ---------------------------------------------------------- update ---
    def update(self) -> None:
        if self.phase in {"idle", "done"}:
            return

        # accelerate → cruise → brake
        if self.phase == "accel":
            self.ang_vel += MAX_ANGVEL / ACCEL_PHASE_FRAMES
            self.timer   += 1
            if self.timer >= ACCEL_PHASE_FRAMES:
                self.phase, self.timer = "cruise", 0

        elif self.phase == "cruise":
            self.timer += 1
            if self.timer >= CONSTANT_PHASE_FRAMES:
                self.phase, self.timer = "brake", 0

        elif self.phase == "brake":
            self.ang_vel *= BRAKE_RATE
            if self.ang_vel < 0.01:                 # slow enough → snap
                self.angle = self.angle % (2 * math.pi)
                delta      = (self.target_angle - self.angle) % (2 * math.pi)
                self.angle += delta
                self.phase = "done"

        # advance rotation
        self.angle += self.ang_vel

    # ---------------------------------------------------------- draw -----
    def draw(self) -> None:
        # outer ring
        pyxel.circ(self.cx, self.cy, self.radius + 12, COL_BLACK)
        pyxel.circ(self.cx, self.cy, self.radius + 10, 0)

        # slot labels
        for n in range(NUM_SLOTS):
            ang = self.angle + SLOT_ANGLE[n]
            sx  = self.cx + math.sin(ang) * self.radius
            sy  = self.cy - math.cos(ang) * self.radius
            col = SLOT_COLOURS[n]
            txt = str(n)
            pyxel.text(int(sx) - (2 if n < 10 else 4), int(sy) - 2, txt, col)

        # pointer
        pyxel.tri(self.cx - 6, self.cy - self.radius - 18,
                  self.cx + 6, self.cy - self.radius - 18,
                  self.cx,     self.cy - self.radius - 6, POINTER_COL)

        # finished? show result banner
        if self.phase == "done":
            colour_char = ("R" if SLOT_COLOURS[self.result] == COL_RED
                           else "B" if SLOT_COLOURS[self.result] == COL_BLACK
                           else "G")
            msg = f"Number: {self.result}   Colour: {colour_char}"
            draw_text_center(msg, 220, TEXT_COL)



# ────────────────────────────── demo app ───────────────────────────────
class RouletteDemo:
    def __init__(self) -> None:
        pyxel.init(SCREEN_W, SCREEN_H, title="Roulette Wheel Demo 🏆")
        self.wheel = RouletteWheel()
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        if pyxel.btnp(pyxel.KEY_SPACE) and self.wheel.phase in {"idle", "done"}:
            self.wheel.start_spin()
        self.wheel.update()

    def draw(self) -> None:
        pyxel.cls(0)
        self.wheel.draw()
        if self.wheel.phase in {"idle", "done"}:
            draw_text_center("Press <Space> to spin", 10, TEXT_COL)


# ─────────────────────────── utility fn ────────────────────────────────

def draw_text_center(text: str, y: int, col: int = 7) -> None:
    w = len(text) * 4  # 4×6 font width
    pyxel.text((SCREEN_W - w) // 2, y, text, col)


# ──────────────────────────── script entry ─────────────────────────────
if __name__ == "__main__":
    RouletteDemo()
