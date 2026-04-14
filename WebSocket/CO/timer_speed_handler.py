import asyncio
import time

class TimerSpeedController:
    def __init__(self):
        self.speed = "normal"  # normal, fast, slow
        self.effect_end_time = None
    
    def apply_fast(self):
        """Fast: 1 min actual time = 30 sec timer countdown"""
        self.speed = "fast"
        self.effect_end_time = time.time() + 60  # 1 min impact
        return {"status": "fast_applied", "duration": 60}
    
    def apply_slow(self):
        """Slow: 1 min actual time = 2 min timer countdown"""
        self.speed = "slow"
        self.effect_end_time = time.time() + 60
        return {"status": "slow_applied", "duration": 60}
    
    def get_current_speed(self):
        # Check if effect expired
        if self.effect_end_time and time.time() > self.effect_end_time:
            self.speed = "normal"
            self.effect_end_time = None
        return self.speed
    
    def calculate_decrement(self):
        """Returns how many seconds to decrement from timer per real second"""
        speed = self.get_current_speed()
        if speed == "fast":
            return 2.0   # 1 real sec = 2 timer sec
        elif speed == "slow":
            return 0.5   # 1 real sec = 0.5 timer sec
        else:
            return 1.0
        













        # timer_speed_handler.py
import time
import asyncio

class TimerSpeedController:
    def __init__(self):
        self.speed = "normal"
        self.effect_end_time = None
        self.callback = None  # Callback function when speed changes
    
    def set_callback(self, callback):
        """Set callback for broadcasting speed changes"""
        self.callback = callback
    
    def apply_fast(self):
        self.speed = "fast"
        self.effect_end_time = time.time() + 60
        if self.callback:
            self.callback("fast")
        return {"status": "fast_applied", "duration": 60}
    
    def apply_slow(self):
        self.speed = "slow"
        self.effect_end_time = time.time() + 60
        if self.callback:
            self.callback("slow")
        return {"status": "slow_applied", "duration": 60}
    
    def get_current_speed(self):
        if self.effect_end_time and time.time() > self.effect_end_time:
            self.speed = "normal"
            self.effect_end_time = None
            if self.callback:
                self.callback("normal")
        return self.speed
    
    def calculate_decrement(self):
        speed = self.get_current_speed()
        if speed == "fast":
            return 2.0
        elif speed == "slow":
            return 0.5
        return 1.0
    
    def get_remaining_effect_time(self):
        if self.effect_end_time:
            remaining = self.effect_end_time - time.time()
            return max(0, remaining)
        return 0