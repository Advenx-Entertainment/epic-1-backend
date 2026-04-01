"""
state_machine.py — Pure deterministic state machine.

Rules (enforced):
  ✓ Holds current state
  ✓ Validates transitions
  ✓ Returns structured events to emit
  ✗ No MQTT calls
  ✗ No WebSocket calls
  ✗ No asyncio timers
  ✗ No GPIO

Every public method returns a list of Event dicts.
The caller (main.py wiring) is responsible for emitting them via the bus.

Transition table
────────────────
  IDLE       + USB_INSERTED  → PLANTING   [STATE_CHANGED, START_TIMER(planting,60)]
  IDLE       + TIMEOUT       → ENDED      [STATE_CHANGED, TRIGGER_OUTPUT(round_end)]
  PLANTING   + USB_REMOVED   → IDLE       [STATE_CHANGED, CANCEL_TIMER(planting)]
  PLANTING   + TIMEOUT       → ACTIVE     [STATE_CHANGED, START_TIMER(spike,120),
                                            TRIGGER_OUTPUT(spike_planted)]
  ACTIVE     + USB_INSERTED  → DEFUSING   [STATE_CHANGED, START_TIMER(defusing,60)]
  ACTIVE     + TIMEOUT       → ENDED      [STATE_CHANGED, TRIGGER_OUTPUT(spike_exploded)]
  DEFUSING   + USB_REMOVED   → ACTIVE     [STATE_CHANGED, CANCEL_TIMER(defusing)]
  DEFUSING   + TIMEOUT       → ENDED      [STATE_CHANGED, TRIGGER_OUTPUT(defuse_failed)]
  DEFUSING   + USB_INSERTED  → ENDED      [STATE_CHANGED, TRIGGER_OUTPUT(defused)]
  ANY        + RESET         → IDLE       [STATE_CHANGED, CANCEL_TIMER(*),
                                            START_TIMER(main,600)]
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from events.event_types import EventType, TimerName

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------

class State(str, Enum):
    IDLE = "IDLE"
    PLANTING = "PLANTING"
    ACTIVE = "ACTIVE"
    DEFUSING = "DEFUSING"
    ENDED = "ENDED"


# ---------------------------------------------------------------------------
# Typed event payload the state machine returns
# ---------------------------------------------------------------------------

@dataclass
class EmittedEvent:
    type: EventType
    data: Any = None

    def to_dict(self) -> dict:
        return {"type": self.type, "data": self.data}


@dataclass
class TransitionResult:
    next_state: State
    events: list[EmittedEvent] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "next_state": self.next_state,
            "events": [e.to_dict() for e in self.events],
        }


# ---------------------------------------------------------------------------
# State Machine
# ---------------------------------------------------------------------------

class SpikePlantingStateMachine:
    """
    Deterministic, side-effect-free state machine.

    Call process_event(event_type, data) → TransitionResult | None
    None means the event was ignored (not valid in current state).
    """

    def __init__(self) -> None:
        self._state: State = State.IDLE

    @property
    def state(self) -> State:
        return self._state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_event(
        self, event_type: EventType, data: Any = None
    ) -> TransitionResult | None:
        """
        Process an inbound event.
        Returns TransitionResult describing next_state + events to emit,
        or None if the event is not valid in the current state.
        """
        handler = self._TRANSITION_TABLE.get((self._state, event_type))
        if handler is None:
            logger.warning(
                "Ignored event %s in state %s", event_type, self._state
            )
            return None

        result: TransitionResult = handler(self, data)
        logger.info(
            "Transition: %s + %s → %s", self._state, event_type, result.next_state
        )
        self._state = result.next_state
        return result

    # ------------------------------------------------------------------
    # Transition handlers (pure functions — no I/O)
    # ------------------------------------------------------------------

    def _idle_usb_inserted(self, _data: Any) -> TransitionResult:
        return TransitionResult(
            next_state=State.PLANTING,
            events=[
                EmittedEvent(EventType.STATE_CHANGED, State.PLANTING),
                EmittedEvent(
                    EventType.START_TIMER,
                    {"name": TimerName.PLANTING, "duration": 60},
                ),
            ],
        )

    def _idle_timeout(self, _data: Any) -> TransitionResult:
        return TransitionResult(
            next_state=State.ENDED,
            events=[
                EmittedEvent(EventType.STATE_CHANGED, State.ENDED),
                EmittedEvent(EventType.TRIGGER_OUTPUT, {"action": "round_end"}),
            ],
        )

    def _planting_usb_removed(self, _data: Any) -> TransitionResult:
        return TransitionResult(
            next_state=State.IDLE,
            events=[
                EmittedEvent(EventType.STATE_CHANGED, State.IDLE),
                EmittedEvent(
                    EventType.CANCEL_TIMER, {"name": TimerName.PLANTING}
                ),
            ],
        )

    def _planting_timeout(self, _data: Any) -> TransitionResult:
        return TransitionResult(
            next_state=State.ACTIVE,
            events=[
                EmittedEvent(EventType.STATE_CHANGED, State.ACTIVE),
                EmittedEvent(EventType.TRIGGER_OUTPUT, {"action": "spike_planted"}),
                EmittedEvent(
                    EventType.START_TIMER,
                    {"name": TimerName.SPIKE, "duration": 120},
                ),
            ],
        )

    def _active_usb_inserted(self, _data: Any) -> TransitionResult:
        return TransitionResult(
            next_state=State.DEFUSING,
            events=[
                EmittedEvent(EventType.STATE_CHANGED, State.DEFUSING),
                EmittedEvent(
                    EventType.START_TIMER,
                    {"name": TimerName.DEFUSING, "duration": 60},
                ),
            ],
        )

    def _active_timeout(self, _data: Any) -> TransitionResult:
        return TransitionResult(
            next_state=State.ENDED,
            events=[
                EmittedEvent(EventType.STATE_CHANGED, State.ENDED),
                EmittedEvent(EventType.TRIGGER_OUTPUT, {"action": "spike_exploded"}),
            ],
        )

    def _defusing_usb_removed(self, _data: Any) -> TransitionResult:
        return TransitionResult(
            next_state=State.ACTIVE,
            events=[
                EmittedEvent(EventType.STATE_CHANGED, State.ACTIVE),
                EmittedEvent(
                    EventType.CANCEL_TIMER, {"name": TimerName.DEFUSING}
                ),
            ],
        )

    def _defusing_timeout(self, _data: Any) -> TransitionResult:
        return TransitionResult(
            next_state=State.ENDED,
            events=[
                EmittedEvent(EventType.STATE_CHANGED, State.ENDED),
                EmittedEvent(EventType.TRIGGER_OUTPUT, {"action": "defuse_failed"}),
            ],
        )

    def _defusing_usb_inserted(self, _data: Any) -> TransitionResult:
        """USB held in long enough → defusal success."""
        return TransitionResult(
            next_state=State.ENDED,
            events=[
                EmittedEvent(EventType.STATE_CHANGED, State.ENDED),
                EmittedEvent(EventType.TRIGGER_OUTPUT, {"action": "defused"}),
            ],
        )

    def _any_reset(self, _data: Any) -> TransitionResult:
        return TransitionResult(
            next_state=State.IDLE,
            events=[
                EmittedEvent(EventType.CANCEL_TIMER, {"name": "all"}),
                EmittedEvent(EventType.STATE_CHANGED, State.IDLE),
                EmittedEvent(
                    EventType.START_TIMER,
                    {"name": TimerName.MAIN, "duration": 600},
                ),
            ],
        )

    # ------------------------------------------------------------------
    # Transition table: (current_state, event) → handler
    # ------------------------------------------------------------------

    _TRANSITION_TABLE = {
        (State.IDLE,      EventType.USB_INSERTED): _idle_usb_inserted,
        (State.IDLE,      EventType.TIMEOUT):      _idle_timeout,
        (State.PLANTING,  EventType.USB_REMOVED):  _planting_usb_removed,
        (State.PLANTING,  EventType.TIMEOUT):      _planting_timeout,
        (State.ACTIVE,    EventType.USB_INSERTED): _active_usb_inserted,
        (State.ACTIVE,    EventType.TIMEOUT):      _active_timeout,
        (State.DEFUSING,  EventType.USB_REMOVED):  _defusing_usb_removed,
        (State.DEFUSING,  EventType.USB_INSERTED): _defusing_usb_inserted,
        (State.DEFUSING,  EventType.TIMEOUT):      _defusing_timeout,
        # RESET is valid from any state
        (State.IDLE,      EventType.RESET):        _any_reset,
        (State.PLANTING,  EventType.RESET):        _any_reset,
        (State.ACTIVE,    EventType.RESET):        _any_reset,
        (State.DEFUSING,  EventType.RESET):        _any_reset,
        (State.ENDED,     EventType.RESET):        _any_reset,
    }
