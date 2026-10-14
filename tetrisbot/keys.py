"""Synthetic keyboard input on macOS (Quartz CGEvents) for the TETR.IO controls.

Needs Accessibility permission for the app running Python (System Settings >
Privacy & Security > Accessibility).
"""
import time

import Quartz

from . import core

# macOS virtual keycodes (ANSI layout)
KEYCODES = {
    "a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7, "c": 8, "v": 9,
    "b": 11, "q": 12, "w": 13, "e": 14, "r": 15, "y": 16, "t": 17, "o": 31, "u": 32,
    "i": 34, "p": 35, "l": 37, "j": 38, "k": 40, "n": 45, "m": 46,
    "space": 49, "shift": 56, "lshift": 56, "rshift": 60, "ctrl": 59, "option": 58,
    "left": 123, "right": 124, "down": 125, "up": 126,
}
_MODIFIER_FLAGS = {56: Quartz.kCGEventFlagMaskShift, 60: Quartz.kCGEventFlagMaskShift,
                   59: Quartz.kCGEventFlagMaskControl, 58: Quartz.kCGEventFlagMaskAlternate}

# The user's TETR.IO "CUSTOM" bindings.
DEFAULT_BINDINGS = {
    core.LEFT: "j",
    core.RIGHT: "l",
    core.SOFT: "k",
    core.HARD: "space",
    core.CCW: "z",
    core.CW: "c",
    core.R180: "x",
    core.HOLD: "lshift",
}


def accessibility_ok(prompt=False):
    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt
        return bool(AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: bool(prompt)}))
    except Exception:
        return True


class Keyboard:
    """Presses keys with timings taken from the handling settings:
    taps are held shorter than DAS, DAS moves are held past DAS (+DCD, +ARR repeats),
    an instant soft drop is held one game frame."""

    def __init__(self, handling, bindings=None):
        b = dict(DEFAULT_BINDINGS)
        b.update(bindings or {})
        self.codes = {action: KEYCODES[name] for action, name in b.items()}
        self.codes[core.DAS_LEFT] = self.codes[core.LEFT]
        self.codes[core.DAS_RIGHT] = self.codes[core.RIGHT]
        self.h = handling
        self.src = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)

    def _post(self, code, down):
        ev = Quartz.CGEventCreateKeyboardEvent(self.src, code, down)
        if code in _MODIFIER_FLAGS:
            Quartz.CGEventSetType(ev, Quartz.kCGEventFlagsChanged)
            Quartz.CGEventSetFlags(ev, _MODIFIER_FLAGS[code] if down else 0)
        else:
            Quartz.CGEventSetFlags(ev, 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)

    def hold_ms(self, action):
        if action in (core.DAS_LEFT, core.DAS_RIGHT):
            return self.h.das_hold_ms()
        if action == core.SOFT:
            return self.h.softdrop_ms()
        return self.h.tap_ms()

    def down(self, action):
        self._post(self.codes[action], True)

    def up(self, action):
        self._post(self.codes[action], False)

    def press(self, action):
        self.down(action)
        _sleep(self.hold_ms(action))
        self.up(action)
        _sleep(self.h.key_gap_ms)

    def release_all(self):
        for code in set(self.codes.values()):
            self._post(code, False)


def _sleep(ms):
    """time.sleep for long waits, busy-wait for sub-millisecond precision."""
    end = time.perf_counter() + ms / 1000.0
    if ms > 3:
        time.sleep((ms - 2) / 1000.0)
    while time.perf_counter() < end:
        pass
