import tkinter as tk
import threading
import time

from timer_speed_handler import TimerSpeedController


class TimerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CO Timer Control - Fast/Slow Power")
        self.root.geometry("450x400")
        self.root.configure(bg="#1a1a2e")

        # MAIN TIMER (5 min)
        self.main_timer = 300

        # SPEED CONTROLLER (IMPORTANT)
        self.speed_controller = TimerSpeedController()

        self.setup_ui()

        # Start countdown loop
        self.update_timer_display()

    # ---------------- UI ----------------
    def setup_ui(self):

        self.timer_label = tk.Label(
            self.root,
            text="05:00",
            font=("Arial", 60, "bold"),
            bg="#1a1a2e",
            fg="#e94560"
        )
        self.timer_label.pack(pady=20)

        self.speed_label = tk.Label(
            self.root,
            text="⚡ SPEED: NORMAL ⚡",
            font=("Arial", 16, "bold"),
            bg="#1a1a2e",
            fg="#00ff88"
        )
        self.speed_label.pack(pady=10)

        # Buttons frame
        frame = tk.Frame(self.root, bg="#1a1a2e")
        frame.pack(pady=20)

        fast_btn = tk.Button(
            frame,
            text="⚡ FAST MODE",
            font=("Arial", 14, "bold"),
            bg="#ff5733",
            fg="white",
            padx=20,
            pady=10,
            command=self.set_fast_mode
        )
        fast_btn.grid(row=0, column=0, padx=10)

        slow_btn = tk.Button(
            frame,
            text="🐢 SLOW MODE",
            font=("Arial", 14, "bold"),
            bg="#3498db",
            fg="white",
            padx=20,
            pady=10,
            command=self.set_slow_mode
        )
        slow_btn.grid(row=0, column=1, padx=10)

    # ---------------- BUTTON FUNCTIONS ----------------
    def set_fast_mode(self):
        self.speed_controller.apply_fast()
        self.speed_label.config(text="⚡ SPEED: FAST ⚡")
        print("FAST MODE ACTIVATED")

    def set_slow_mode(self):
        self.speed_controller.apply_slow()
        self.speed_label.config(text="🐢 SPEED: SLOW 🐢")
        print("SLOW MODE ACTIVATED")

    # ---------------- TIMER LOOP (MAIN MAGIC) ----------------
    def update_timer_display(self):

        # Auto back to normal after 60 sec
        if self.speed_controller.effect_end_time:
            if time.time() > self.speed_controller.effect_end_time:
                self.speed_controller.speed = "normal"
                self.speed_controller.effect_end_time = None
                self.speed_label.config(text="⚡ SPEED: NORMAL ⚡")
                print("Back to NORMAL speed")

        # Get speed multiplier
        decrement = self.speed_controller.calculate_decrement()

        # Decrease timer based on speed
        if self.main_timer > 0:
            self.main_timer -= decrement

        # Prevent negative
        self.main_timer = max(0, self.main_timer)

        # Convert to MM:SS
        minutes = int(self.main_timer // 60)
        seconds = int(self.main_timer % 60)

        self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")

        # Loop every 1 second
        self.root.after(1000, self.update_timer_display)


# ---------------- RUN APP ----------------
root = tk.Tk()
app = TimerUI(root)
root.mainloop()