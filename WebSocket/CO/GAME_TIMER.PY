import time
import threading

class GameTimer:
    def __init__(self, total_seconds, on_tick=None, on_expire=None):
        """
        total_seconds : kitna bada countdown hai (e.g. 300 for 5 min)
        on_tick       : callback(remaining_game_seconds) — har second call hoga
        on_expire     : callback() — jab timer 0 ho jaye
        """
        self.total_seconds      = total_seconds
        self.remaining          = float(total_seconds)
        self.on_tick            = on_tick
        self.on_expire          = on_expire

        self.speed_mode         = None    # "fast" | "slow" | None
        self.speed_start_real   = None    # real timestamp jab mode laga
        self.game_at_speed_start = None   # remaining game time jab mode laga

        self._lock              = threading.Lock()
        self._running           = False
        self._thread            = None

    # ------------------------------------------------------------------ #
    #  Public controls                                                     #
    # ------------------------------------------------------------------ #

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def apply_fast(self):
        with self._lock:
            if self.speed_mode is not None:
                return False                   # already in a speed mode, ignore
            self.speed_mode          = "fast"
            self.speed_start_real    = time.time()
            self.game_at_speed_start = self.remaining
            return True

    def apply_slow(self):
        with self._lock:
            if self.speed_mode is not None:
                return False
            self.speed_mode          = "slow"
            self.speed_start_real    = time.time()
            self.game_at_speed_start = self.remaining
            return True

    def is_speed_active(self):
        return self.speed_mode is not None

    # ------------------------------------------------------------------ #
    #  Internal tick loop                                                  #
    # ------------------------------------------------------------------ #

    def _loop(self):
        TICK = 0.1                             # 100ms resolution
        last_real = time.time()

        while self._running and self.remaining > 0:
            time.sleep(TICK)
            now       = time.time()
            real_delta = now - last_real
            last_real  = now

            with self._lock:
                game_delta = self._to_game_delta(real_delta)
                self.remaining -= game_delta
                self.remaining  = max(0.0, self.remaining)

                self._check_normalize()

            if self.on_tick:
                self.on_tick(self.remaining)

        if self.remaining <= 0 and self.on_expire:
            self.on_expire()

    def _to_game_delta(self, real_delta):
        """Convert a real-time delta to game-time delta based on current mode."""
        if self.speed_mode == "fast":
            return real_delta * 2              # 1 real sec = 2 game sec

        elif self.speed_mode == "slow":
            elapsed_real = time.time() - self.speed_start_real
            prev_elapsed = elapsed_real - real_delta

            # game = max(0, real - 1)
            prev_game = max(0.0, prev_elapsed - 1.0)
            curr_game = max(0.0, elapsed_real  - 1.0)
            return curr_game - prev_game       # could be 0 in the first second

        return real_delta                      # normal ×1

    def _check_normalize(self):
        """Normalize speed back to ×1 when the impact window is over."""
        if self.speed_mode is None:
            return

        elapsed_real = time.time() - self.speed_start_real

        if self.speed_mode == "fast":
            # 30 real sec = 1 full game minute consumed
            if elapsed_real >= 30.0:
                self._normalize()

        elif self.speed_mode == "slow":
            # slow runs until exactly 1 game-minute has been subtracted
            game_consumed = max(0.0, elapsed_real - 1.0)
            if game_consumed >= 60.0:
                self._normalize()

    def _normalize(self):
        self.speed_mode          = None
        self.speed_start_real    = None
        self.game_at_speed_start = None