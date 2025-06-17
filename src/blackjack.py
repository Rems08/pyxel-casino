import random
import pyxel
from common import BET_INCREMENT, draw_text_center

class BlackjackGame:
    def __init__(self, app) -> None:
        self.app = app
        self.deck, self.player, self.dealer = [], [], []
        self.bet        = BET_INCREMENT
        self.outcome    = ""
        self.player_stand = False

    # ----------------------------------------------------------- helpers ---
    def _build_deck(self) -> None:
        self.deck = [(v, s) for v in range(1, 14) for s in range(4)]
        random.shuffle(self.deck)

    @staticmethod
    def _card_value(card) -> int:
        v, _ = card
        return 10 if v > 10 else (11 if v == 1 else v)

    def _hand_value(self, hand) -> int:
        total = sum(self._card_value(c) for c in hand)
        aces  = sum(1 for c in hand if c[0] == 1)
        while total > 21 and aces:
            total -= 10
            aces  -= 1
        return total

    # ----------------------------------------------------------- lifecycle-
    def start_new(self) -> None:
        self._build_deck()
        self.player = [self.deck.pop(), self.deck.pop()]
        self.dealer = [self.deck.pop(), self.deck.pop()]
        self.bet    = min(BET_INCREMENT, self.app.balance)
        self.app.balance -= self.bet
        self.outcome      = ""
        self.player_stand = False
        self.app.input.reset()

    def reset(self) -> None:
        self.start_new()

    # ----------------------------------------------------------- update ----
    def update(self) -> None:
        if self.outcome:                         # round finished
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.app.to_menu()
            return

        # ---------- player phase ----------
        if not self.player_stand:
            if pyxel.btnp(pyxel.KEY_H):          # hit
                self.player.append(self.deck.pop())
                if self._hand_value(self.player) > 21:
                    self.outcome = "Bust! Dealer wins."
            if pyxel.btnp(pyxel.KEY_S):          # stand
                self.player_stand = True
        # ---------- dealer phase ----------
        else:
            if self._hand_value(self.dealer) < 17:
                self.dealer.append(self.deck.pop())
            else:
                p, d = self._hand_value(self.player), self._hand_value(self.dealer)
                if d > 21 or p > d:
                    self.outcome = "Player wins!"
                    self.app.balance += self.bet * 2
                elif p == d:
                    self.outcome = "Push – bet returned."
                    self.app.balance += self.bet
                else:
                    self.outcome = "Dealer wins."

        if pyxel.btnp(pyxel.KEY_Q):
            self.app.to_menu()

    # ----------------------------------------------------------- draw ------
    def draw(self) -> None:
        y = 30
        draw_text_center("Blackjack", y, 7)
        y += 15

        # dealer
        pyxel.text(10, y, f"Dealer: "
                 f"{self._hand_value(self.dealer) if self.player_stand or self.outcome else '?'}", 7)
        pyxel.text(10, y + 10,
                   " ".join(str(c[0]) for c in self.dealer), 7)

        # player
        y += 30
        pyxel.text(10, y, f"Player: {self._hand_value(self.player)}", 7)
        pyxel.text(10, y + 10, " ".join(str(c[0]) for c in self.player), 7)

        # misc
        y += 30
        pyxel.text(10, y, f"Bet: ${self.bet}", 7)

        if self.outcome:
            draw_text_center(self.outcome, 200, 11)
            draw_text_center("Press Enter to return", 214, 5)
        else:
            pyxel.text(10, 200, "H = Hit   S = Stand   Q = Quit", 5)
