from timer_speed_handler import TimerSpeedController

t = TimerSpeedController()
print(f"Initial speed: {t.get_current_speed()}")

t.apply_fast()
print(f"After FAST: {t.get_current_speed()}")
print(f"Decrement: {t.calculate_decrement()}")
