from co.game_timer import GameTimer

class TimerUI:
    def __init__(self, timer: GameTimer, mqtt_client, alert_fn, update_display_fn):
        """
        timer            : GameTimer instance
        mqtt_client      : apna MQTT client
        alert_fn         : function(message) — CO screen pe alert dikhao
        update_display_fn: function(seconds) — display update karo
        """
        self.timer           = timer
        self.mqtt            = mqtt_client
        self.alert           = alert_fn
        self.update_display  = update_display_fn

        # Timer ke callbacks wire karo
        self.timer.on_tick   = self._on_tick
        self.timer.on_expire = self._on_expire

    # ------------------------------------------------------------------ #
    #  Button handlers — yeh CO ke buttons se call karo                   #
    # ------------------------------------------------------------------ #

    def on_speed_button_clicked(self):
        """CO screen pe 'Speed' button click hone pe call karo."""
        if self.timer.is_speed_active():
            self.alert("Speed mode already active! Wait for it to normalize.")
            return

        choice = self.alert("Choose speed mode", options=["Fast", "Slow"])
        # Note: alert_fn ko tum apne UI framework se implement karo
        # choice = "fast" ya "slow" return karega

        if choice == "Fast":
            success = self.timer.apply_fast()
            if success:
                self.alert("FAST mode ON — 1 min in 30 seconds!")
                self.mqtt.publish("game/timer/speed", {"mode": "fast"})

        elif choice == "Slow":
            success = self.timer.apply_slow()
            if success:
                self.alert("SLOW mode ON — timer slowed down for 1 min!")
                self.mqtt.publish("game/timer/speed", {"mode": "slow"})

    # ------------------------------------------------------------------ #
    #  Timer callbacks                                                     #
    # ------------------------------------------------------------------ #

    def _on_tick(self, remaining_seconds):
        self.update_display(remaining_seconds)

        # Normalize ho gayi toh CO ko bata do
        if not self.timer.is_speed_active():
            pass  # display normal speed indicator

    def _on_expire(self):
        self.alert("TIMER EXPIRED!")
        self.mqtt.publish("game/timer/expired", {})