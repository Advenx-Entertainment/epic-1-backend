# timer_ui.py
import asyncio
import websockets
import json
import tkinter as tk
from tkinter import messagebox
import threading

class TimerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CO Timer Control - Fast/Slow Power")
        self.root.geometry("450x350")
        self.root.configure(bg='#2c3e50')
        
        self.main_timer = 300  # 5 minutes
        self.speed = "normal"
        self.websocket = None
        self.running = True
        self.loop = None
        
        self.setup_ui()
        self.start_websocket_thread()
        
    def setup_ui(self):
        # Timer display
        self.timer_label = tk.Label(self.root, text="05:00", font=("Arial", 60, "bold"), 
                                    bg='#2c3e50', fg='#ecf0f1')
        self.timer_label.pack(pady=30)
        
        # Speed indicator
        self.speed_label = tk.Label(self.root, text="⚡ SPEED: NORMAL ⚡", 
                                    font=("Arial", 16, "bold"), 
                                    bg='#2c3e50', fg='#2ecc71')
        self.speed_label.pack(pady=10)
        
        # Buttons frame
        button_frame = tk.Frame(self.root, bg='#2c3e50')
        button_frame.pack(pady=30)
        
        # Fast button
        self.fast_btn = tk.Button(button_frame, text="⚡ FAST MODE", 
                                   font=("Arial", 14, "bold"), 
                                   bg='#e74c3c', fg='white',
                                   command=self.apply_fast, 
                                   width=12, height=2)
        self.fast_btn.pack(side=tk.LEFT, padx=15)
        
        # Slow button
        self.slow_btn = tk.Button(button_frame, text="🐢 SLOW MODE",
                                   font=("Arial", 14, "bold"),
                                   bg='#3498db', fg='white',
                                   command=self.apply_slow, 
                                   width=12, height=2)
        self.slow_btn.pack(side=tk.LEFT, padx=15)
        
        # Status label
        self.status_label = tk.Label(self.root, text="✅ Ready", 
                                     font=("Arial", 10), 
                                     bg='#2c3e50', fg='#95a5a6')
        self.status_label.pack(pady=20)
        
        # Start timer updates
        self.update_timer_display()
        
    def start_websocket_thread(self):
        """Start WebSocket connection in separate thread"""
        thread = threading.Thread(target=self.run_websocket, daemon=True)
        thread.start()
        
    def run_websocket(self):
        """Run WebSocket connection"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect_websocket())
        
    async def connect_websocket(self):
        try:
            self.websocket = await websockets.connect("ws://localhost:8766")
            self.update_status("WebSocket Connected!")
            asyncio.create_task(self.listen_messages())
        except Exception as e:
            self.update_status(f"Connection failed: {e}")
            
    async def listen_messages(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                if data.get("event") == "timer_speed_changed":
                    self.speed = data["speed"]
                    self.update_speed_display()
                elif data.get("event") == "current_timer_speed":
                    self.speed = data["speed"]
                    self.update_speed_display()
        except Exception as e:
            print(f"WebSocket error: {e}")
            
    def apply_fast(self):
        asyncio.run_coroutine_threadsafe(self.send_power("fast"), self.loop)
        
    def apply_slow(self):
        asyncio.run_coroutine_threadsafe(self.send_power("slow"), self.loop)
        
    async def send_power(self, power_type):
        if not self.websocket:
            self.update_status("WebSocket not connected!")
            return
        
        message = {"action": "apply_timer_power", "type": power_type}
        await self.websocket.send(json.dumps(message))
        self.update_status(f"{power_type.upper()} mode applied for 1 minute!")
        self.root.after(3000, lambda: self.update_status("✅ Ready"))
        
    def update_speed_display(self):
        if self.speed == "fast":
            self.speed_label.config(text="⚡ SPEED: FAST ⚡", fg="#e74c3c")
        elif self.speed == "slow":
            self.speed_label.config(text="🐢 SPEED: SLOW 🐢", fg="#3498db")
        else:
            self.speed_label.config(text="⚡ SPEED: NORMAL ⚡", fg="#2ecc71")
            
    def update_status(self, message):
        self.status_label.config(text=message)
        
    def update_timer_display(self):
        if not self.running:
            return
            
        decrement = 1.0
        if self.speed == "fast":
            decrement = 2.0
        elif self.speed == "slow":
            decrement = 0.5
            
        self.main_timer -= decrement
        if self.main_timer < 0:
            self.main_timer = 0
            
        minutes = int(self.main_timer // 60)
        seconds = int(self.main_timer % 60)
        self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
        
        self.root.after(1000, self.update_timer_display)

def main():
    root = tk.Tk()
    app = TimerUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()