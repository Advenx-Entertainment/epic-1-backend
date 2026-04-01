from enum import Enum


class EventType(str, Enum):
    # --- Inbound: from hardware / external ---
    USB_INSERTED = "USB_INSERTED"
    USB_REMOVED = "USB_REMOVED"
    RESET = "RESET"

    # --- Internal: timer lifecycle ---
    START_TIMER = "START_TIMER"
    CANCEL_TIMER = "CANCEL_TIMER"
    TIMEOUT = "TIMEOUT"

    # --- Outbound: broadcast to consumers ---
    STATE_CHANGED = "STATE_CHANGED"
    TRIGGER_OUTPUT = "TRIGGER_OUTPUT"      # GPIO / fireworks / audio


class TimerName(str, Enum):
    MAIN = "main"           # 10-minute round timer (IDLE)
    PLANTING = "planting"   # 1-minute planting window
    SPIKE = "spike"         # 2-minute spike countdown
    DEFUSING = "defusing"   # 1-minute defusal window
