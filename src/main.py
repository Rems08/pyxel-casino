import pyxel
import random
from enum import Enum

# --- Configuration Constants ---
SCREEN_W, SCREEN_H = 256, 256
STARTING_BALANCE = 500
BET_INCREMENT = 10
NUM_HORSES = 4

# Roulette numbers (American single‑zero wheel for simplicity)
ROULETTE_NUMBERS = list(range(37))  # 0‑36
ROULETTE_COLORS = {0: "G"}
for n in ROULETTE_NUMBERS[1:]:
    # Red if number is odd on first dozen else black (rough approximation)
    ROULETTE_COLORS[n] = "R" if (n % 2 == 1) else "B"

# --- Scene Enumeration ---
class Scene(Enum):
    MENU = 0
    ROULETTE_BET = 1
    ROULETTE_SPIN = 2
    BLACKJACK = 3
    HORSE_BET = 4
    HORSE_RACE = 5

# --- Helper Functions ---

def draw_text_center(text, y, col=7):
    w = len(text) * 4
    x = (SCREEN_W - w) // 2
    pyxel.text(x, y, text, col)

    # ===========================================================
    #                    Main Casino Game Class
    # ===========================================================
class CasinoGame:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="Rems Casino 🏨🎰")
        self.scene = Scene.MENU
        self.balance = STARTING_BALANCE
        self.menu_index = 0
        self.menu_items = ["Roulette", "Blackjack", "Horse Race"]

        # Roulette state
        self.roulette_bet_num = 0
        self.roulette_bet_amount = BET_INCREMENT
        self.roulette_result = None
        self.spin_ticks = 0

        # Blackjack state
        self.deck = []
        self.player_hand = []
        self.dealer_hand = []
        self.blackjack_bet = BET_INCREMENT
        self.blackjack_outcome = ""
        self.player_stand = False

        # Horse race state
        self.horse_odds = [0.4, 0.3, 0.2, 0.1]  # Probabilities sum to 1
        self.horse_bet_idx = 0
        self.horse_bet_amount = BET_INCREMENT
        self.horse_positions = [0 for _ in range(NUM_HORSES)]
        self.horse_winner = None
        
        # --- Key hold acceleration ---
        # Dict keyed by Pyxel key constant → frames held
        self.hold_counters = {}

        pyxel.run(self.update, self.draw)
    
    # ===========================================================
    #                    Utility / Shared Logic
    # ===========================================================
    def accelerated_press(self, key: int, base_interval: int = 12, min_interval: int = 2, accel_rate: int = 10) -> bool:
        """Return True when the key should trigger a repeated action.

        * First frame the key is pressed (`pyxel.btnp`) → immediate True.
        * While held (`pyxel.btn`) → repeat with an interval that shrinks the
          longer the key is held (accelerates).
        """
        # Immediate action on fresh press
        if pyxel.btnp(key):
            self.hold_counters[key] = 0
            return True

        # While still held – accelerate
        if pyxel.btn(key):
            self.hold_counters[key] = self.hold_counters.get(key, 0) + 1
            frames = self.hold_counters[key]
            interval = max(min_interval, base_interval - frames // accel_rate)
            # Trigger when we've waited "interval" frames
            if frames % interval == 0:
                return True
        else:
            # Key released → reset
            self.hold_counters.pop(key, None)
        return False

    def clear_holds(self):
        """Reset all hold counters – call when switching scenes."""
        self.hold_counters.clear()

    # --- Deck helpers for Blackjack ---
    def build_deck(self):
        self.deck = [(v, s) for v in range(1, 14) for s in range(4)]
        random.shuffle(self.deck)

    def card_value(self, card):
        v, _ = card
        return 10 if v > 10 else (11 if v == 1 else v)

    def hand_value(self, hand):
        value = sum(self.card_value(c) for c in hand)
        # Adjust for aces
        aces = sum(1 for c in hand if c[0] == 1)
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    # --- Scene Navigation ---
    def update(self):
        scene = self.scene
        if scene == Scene.MENU:
            self.update_menu()
        elif scene == Scene.ROULETTE_BET:
            self.update_roulette_bet()
        elif scene == Scene.ROULETTE_SPIN:
            self.update_roulette_spin()
        elif scene == Scene.BLACKJACK:
            self.update_blackjack()
        elif scene == Scene.HORSE_BET:
            self.update_horse_bet()
        elif scene == Scene.HORSE_RACE:
            self.update_horse_race()

    # -----------------------------------------------------------
    #                          Menu
    # -----------------------------------------------------------
    def update_menu(self):
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.menu_index = (self.menu_index + 1) % len(self.menu_items)
        if pyxel.btnp(pyxel.KEY_UP):
            self.menu_index = (self.menu_index - 1) % len(self.menu_items)
        if pyxel.btnp(pyxel.KEY_RETURN):
            choice = self.menu_items[self.menu_index]
            self.clear_holds()
            if choice == "Roulette":
                self.scene = Scene.ROULETTE_BET
            elif choice == "Blackjack":
                self.scene = Scene.BLACKJACK
                self.start_blackjack()
            elif choice == "Horse Race":
                self.scene = Scene.HORSE_BET

    # -----------------------------------------------------------
    #                         Roulette
    # -----------------------------------------------------------
    def update_roulette_bet(self):
        if pyxel.btnp(pyxel.KEY_LEFT):
            self.roulette_bet_num = (self.roulette_bet_num - 1) % len(ROULETTE_NUMBERS)
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.roulette_bet_num = (self.roulette_bet_num + 1) % len(ROULETTE_NUMBERS)
        if self.accelerated_press(pyxel.KEY_UP):
            if self.roulette_bet_amount + BET_INCREMENT <= self.balance:
                self.roulette_bet_amount += BET_INCREMENT
        if self.accelerated_press(pyxel.KEY_DOWN):
            if self.roulette_bet_amount - BET_INCREMENT >= BET_INCREMENT:
                self.roulette_bet_amount -= BET_INCREMENT
        if pyxel.btnp(pyxel.KEY_SPACE):
            # Place bet
            self.balance -= self.roulette_bet_amount
            self.roulette_result = None
            self.spin_ticks = 60  # frames for spin animation
            self.clear_holds()
            self.scene = Scene.ROULETTE_SPIN
        if pyxel.btnp(pyxel.KEY_Q):
            self.clear_holds()
            self.scene = Scene.MENU

    def update_roulette_spin(self):
        self.spin_ticks -= 1
        # Slow down spin visually (optional)
        if self.spin_ticks == 0:
            self.roulette_result = random.choice(ROULETTE_NUMBERS)
            # Determine payout
            if self.roulette_result == self.roulette_bet_num:
                payout = 35 * self.roulette_bet_amount
            else:
                payout = 0
            self.balance += payout
            self.scene = Scene.ROULETTE_BET  # back to bet screen to continue

    # -----------------------------------------------------------
    #                         Blackjack
    # -----------------------------------------------------------

    def start_blackjack(self):
        self.build_deck()
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]
        self.blackjack_bet = min(BET_INCREMENT, self.balance)
        self.balance -= self.blackjack_bet
        self.player_stand = False
        self.blackjack_outcome = ""
        self.clear_holds()

    def update_blackjack(self):
        if self.blackjack_outcome:
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.clear_holds()
                self.scene = Scene.MENU
            return

        # Player phase
        if not self.player_stand:
            if pyxel.btnp(pyxel.KEY_H):
                self.player_hand.append(self.deck.pop())
                if self.hand_value(self.player_hand) > 21:
                    self.blackjack_outcome = "Bust! Dealer wins."
            if pyxel.btnp(pyxel.KEY_S):
                self.player_stand = True
        else:
            # Dealer phase
            if self.hand_value(self.dealer_hand) < 17:
                self.dealer_hand.append(self.deck.pop())
            else:
                p_val = self.hand_value(self.player_hand)
                d_val = self.hand_value(self.dealer_hand)
                if d_val > 21 or p_val > d_val:
                    self.blackjack_outcome = "Player wins!"
                    self.balance += self.blackjack_bet * 2
                elif p_val == d_val:
                    self.blackjack_outcome = "Push. Bet returned."
                    self.balance += self.blackjack_bet
                else:
                    self.blackjack_outcome = "Dealer wins."

        if pyxel.btnp(pyxel.KEY_Q):
            self.clear_holds()
            self.scene = Scene.MENU

    # -----------------------------------------------------------
    #                        Horse Racing
    # -----------------------------------------------------------

    def update_horse_bet(self):
        if pyxel.btnp(pyxel.KEY_LEFT):
            self.horse_bet_idx = (self.horse_bet_idx - 1) % NUM_HORSES
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.horse_bet_idx = (self.horse_bet_idx + 1) % NUM_HORSES

        # Bet amount with acceleration
        if self.accelerated_press(pyxel.KEY_UP):
            if self.horse_bet_amount + BET_INCREMENT <= self.balance:
                self.horse_bet_amount += BET_INCREMENT
        if self.accelerated_press(pyxel.KEY_DOWN):
            if self.horse_bet_amount - BET_INCREMENT >= BET_INCREMENT:
                self.horse_bet_amount -= BET_INCREMENT

        if pyxel.btnp(pyxel.KEY_SPACE):
            self.balance -= self.horse_bet_amount
            self.horse_positions = [0 for _ in range(NUM_HORSES)]
            self.horse_winner = None
            self.clear_holds()
            self.scene = Scene.HORSE_RACE
        if pyxel.btnp(pyxel.KEY_Q):
            self.clear_holds()
            self.scene = Scene.MENU

    def update_horse_race(self):
        if self.horse_winner is None:
            for i in range(NUM_HORSES):
                # Move proportionally to odds each frame
                self.horse_positions[i] += random.randint(0, int(3 + self.horse_odds[i] * 5))
                if self.horse_positions[i] >= SCREEN_W - 20:
                    self.horse_winner = i
            if self.horse_winner is not None:
                payout = int(self.horse_bet_amount / self.horse_odds[self.horse_winner]) if self.horse_winner == self.horse_bet_idx else 0
                self.balance += payout
        else:
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.clear_holds()
                self.scene = Scene.HORSE_BET
        if pyxel.btnp(pyxel.KEY_Q):
            self.clear_holds()
            self.scene = Scene.MENU

    # ===========================================================
    #                         Drawing
    # ===========================================================

    def draw(self):
        pyxel.cls(0)
        draw_text_center(f"Balance: ${self.balance}", 2, 10)
        scene = self.scene
        if scene == Scene.MENU:
            self.draw_menu()
        elif scene == Scene.ROULETTE_BET:
            self.draw_roulette_bet()
        elif scene == Scene.ROULETTE_SPIN:
            self.draw_roulette_spin()
        elif scene == Scene.BLACKJACK:
            self.draw_blackjack()
        elif scene == Scene.HORSE_BET:
            self.draw_horse_bet()
        elif scene == Scene.HORSE_RACE:
            self.draw_horse_race()

    # ----- Draw helpers -----
    def draw_menu(self):
        draw_text_center("=== Rems Casino ===", 40, 7)
        for idx, item in enumerate(self.menu_items):
            color = 11 if idx == self.menu_index else 7
            draw_text_center(item, 60 + idx * 10, color)
        draw_text_center("Use ↑↓ to move, Enter to select", 200, 5)

    # Roulette Draws
    def draw_roulette_bet(self):
        draw_text_center("Roulette: Pick a number", 30, 7)
        draw_text_center(f"Bet Number: {self.roulette_bet_num}", 50, 11)
        draw_text_center(f"Bet Amount: ${self.roulette_bet_amount}", 70, 11)
        draw_text_center("← → change number, ↑ ↓ bet, Space to spin, Q to quit", 220, 5)

    def draw_roulette_spin(self):
        draw_text_center("Spinning...", 100, 7)
        if self.spin_ticks == 0:
            color_code = {"R": 8, "B": 12, "G": 11}[ROULETTE_COLORS[self.roulette_result]]
            draw_text_center(f"Result: {self.roulette_result} {ROULETTE_COLORS[self.roulette_result]}", 120, color_code)
            draw_text_center("Press any key", 140, 7)
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
                self.scene = Scene.ROULETTE_BET

    # Blackjack Draws
    def draw_blackjack(self):
        y = 30
        draw_text_center("Blackjack", y, 7)
        y += 15
        pyxel.text(10, y, f"Dealer: {self.hand_value(self.dealer_hand) if self.player_stand or self.blackjack_outcome else '?'}", 7)
        pyxel.text(10, y + 10, " ".join(str(c[0]) for c in self.dealer_hand), 7)
        y += 30
        pyxel.text(10, y, f"Player: {self.hand_value(self.player_hand)}", 7)
        pyxel.text(10, y + 10, " ".join(str(c[0]) for c in self.player_hand), 7)
        y += 30
        pyxel.text(10, y, f"Bet: ${self.blackjack_bet}", 7)
        y += 10
        if self.blackjack_outcome:
            draw_text_center(self.blackjack_outcome, 200, 11)
            draw_text_center("Press Enter to return", 214, 5)
        else:
            pyxel.text(10, 200, "H = Hit, S = Stand, Q = Quit", 5)

    # Horse Draws
    def draw_horse_bet(self):
        draw_text_center("Horse Race Betting", 30, 7)
        for i in range(NUM_HORSES):
            color = 11 if i == self.horse_bet_idx else 7
            draw_text_center(f"Horse {i+1} | Odds: {self.horse_odds[i]:.2f}", 60 + i * 12, color)
        draw_text_center(f"Bet: ${self.horse_bet_amount}", 120, 11)
        draw_text_center("← → select horse, ↑ ↓ bet, Space to start, Q to quit", 220, 5)

    def draw_horse_race(self):
        for i in range(NUM_HORSES):
            y = 40 + i * 20
            pyxel.rect(self.horse_positions[i], y, 16, 8, 8 + i)
        if self.horse_winner is not None:
            draw_text_center(f"Horse {self.horse_winner+1} wins!", 200, 11)
            draw_text_center("Press Enter to bet again", 214, 5)
        else:
            draw_text_center("Racing...", 200, 7)

# --- Run game ---
if __name__ == "__main__":
    CasinoGame()
