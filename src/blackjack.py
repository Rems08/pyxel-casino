"""blackjack.py – revamped
--------------------------------
• Card ranks are now rendered as A‑K‑Q‑J‑T‑9… instead of raw numbers so the
  displayed hand value always matches what you see.
• Dealer’s hole card stays hidden until the player stands/busts.
• Minor clean‑ups (type hints, constants, early returns, docstrings).

This file fully replaces the previous version.
"""

from __future__ import annotations

import random
from typing import List, Tuple

import pyxel

from common import BET_INCREMENT, draw_text_center

# ────────────────────────────── constants ──────────────────────────────
RANK_STR = {1: "A", 11: "J", 12: "Q", 13: "K"}
SUIT_STR = {0: "♠", 1: "♥", 2: "♦", 3: "♣"}  # will display as simple letters on Pyxel

Card = Tuple[int, int]  # (rank 1‑13, suit 0‑3)


# ────────────────────────────── helpers ────────────────────────────────

def card_str(card: Card) -> str:
    """Human‑friendly one‑character rank + optional suit."""
    rank, suit = card
    rank_s = RANK_STR.get(rank, str(rank))
    suit_s = SUIT_STR.get(suit, "S")
    # Pyxel’s default font is narrow – we drop suit to save space if needed
    return f"{rank_s}{suit_s}"


def hand_value(hand: List[Card]) -> int:
    """Return blackjack value, treating aces as 11 or 1 as appropriate."""
    total = sum(10 if r > 10 else 11 if r == 1 else r for r, _ in hand)
    aces = sum(1 for r, _ in hand if r == 1)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


# ────────────────────────────── main class ─────────────────────────────
class BlackjackGame:
    """Self‑contained blackjack mini‑game (update/draw API)."""

    def __init__(self, app) -> None:
        self.app = app  # backlink to CasinoApp for balance & input helpers
        self.reset()

    # ───────────────────────── public lifecycle ────────────────────────
    def reset(self) -> None:
        """Return to bet selection screen."""
        self.bet: int = BET_INCREMENT
        self.stage: str = "bet"  # bet | play | result
        self.deck: List[Card] = []
        self.player: List[Card] = []
        self.dealer: List[Card] = []
        self.outcome: str = ""
        self.player_stand: bool = False
        self.app.input.reset()

    start_new = reset  # alias expected by main menu

    # ───────────────────────── update entrypoint ───────────────────────
    def update(self) -> None:
        if self.stage == "bet":
            self._update_bet()
        elif self.stage == "play":
            self._update_play()
        else:  # result
            self._update_result()

    # ────────────────────────── draw entrypoint ────────────────────────
    def draw(self) -> None:
        if self.stage == "bet":
            self._draw_bet()
        else:
            self._draw_table()

    # ───────────────────────── bet phase ───────────────────────────────
    def _update_bet(self) -> None:
        ih = self.app.input
        if ih.accelerated_press(pyxel.KEY_UP) and self.bet + BET_INCREMENT <= self.app.balance:
            self.bet += BET_INCREMENT
        if ih.accelerated_press(pyxel.KEY_DOWN) and self.bet - BET_INCREMENT >= BET_INCREMENT:
            self.bet -= BET_INCREMENT

        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
            self._deal_cards()
        if pyxel.btnp(pyxel.KEY_Q):
            self.app.to_menu()

    def _deal_cards(self) -> None:
        self.deck = [(r, s) for r in range(1, 14) for s in range(4)]
        random.shuffle(self.deck)

        self.player = [self.deck.pop(), self.deck.pop()]
        self.dealer = [self.deck.pop(), self.deck.pop()]

        self.bet = min(self.bet, self.app.balance)  # final clamp
        self.app.balance -= self.bet

        self.player_stand = False
        self.outcome = ""
        self.stage = "play"
        self.app.input.reset()

    # ───────────────────────── play phase ──────────────────────────────
    def _update_play(self) -> None:
        if not self.player_stand:
            if pyxel.btnp(pyxel.KEY_H):
                self.player.append(self.deck.pop())
                if hand_value(self.player) > 21:
                    self._settle("Bust! Dealer wins.")
            if pyxel.btnp(pyxel.KEY_S):
                self.player_stand = True
        else:
            if hand_value(self.dealer) < 17:
                self.dealer.append(self.deck.pop())
            else:
                self._evaluate_winner()

        if pyxel.btnp(pyxel.KEY_Q):
            self.app.to_menu()

    def _evaluate_winner(self) -> None:
        p, d = hand_value(self.player), hand_value(self.dealer)
        if d > 21 or p > d:
            self._settle("Player wins!", payout=2)
        elif p == d:
            self._settle("Push – bet returned.", payout=1)
        else:
            self._settle("Dealer wins.")

    def _settle(self, message: str, *, payout: int = 0) -> None:
        if payout:
            self.app.balance += self.bet * payout
        self.outcome = message
        self.stage = "result"

    # ───────────────────────── result phase ─────────────────────────────
    def _update_result(self) -> None:
        if pyxel.btnp(pyxel.KEY_RETURN):
            self.reset()
        if pyxel.btnp(pyxel.KEY_Q):
            self.app.to_menu()

    # ─────────────────────────── drawing ───────────────────────────────
    def _draw_bet(self) -> None:
        draw_text_center("Blackjack – place your bet", 40, 7)
        draw_text_center(f"Bet: ${self.bet}", 70, 11)
        draw_text_center("↑ ↓ change  •  Space/Enter deal  •  Q menu", 200, 5)

    def _draw_table(self) -> None:
        y = 30
        draw_text_center("Blackjack", y, 7)
        y += 15

        # dealer hand (hide hole card until player stands/busts)
        if self.stage == "play" and not self.player_stand and not self.outcome:
            dealer_cards = f"{card_str(self.dealer[0])} ??"
            dealer_val = "?"
        else:
            dealer_cards = " ".join(card_str(c) for c in self.dealer)
            dealer_val = str(hand_value(self.dealer))

        pyxel.text(10, y, f"Dealer: {dealer_val}", 7)
        pyxel.text(10, y + 10, dealer_cards, 7)

        # player hand
        y += 30
        pyxel.text(10, y, f"Player: {hand_value(self.player)}", 7)
        pyxel.text(10, y + 10, " ".join(card_str(c) for c in self.player), 7)

        # bet amount
        y += 30
        pyxel.text(10, y, f"Bet: ${self.bet}", 7)

        # footer
        if self.stage == "result":
            draw_text_center(self.outcome, 200, 11)
            draw_text_center("Enter = new bet  •  Q = menu", 214, 5)
        else:
            pyxel.text(10, 200, "H = Hit   S = Stand   Q = Quit", 5)
