"""Synthetic keyboard input on macOS (Quartz CGEvents) for the TETR.IO controls.

Needs Accessibility permission for the app running Python (System Settings >
Privacy & Security > Accessibility).
"""
import time

import Quartz

from . import core

# macOS virtual keycodes (ANSI layout). The first name for a code is the one shown in the
# Handling window's CONTROLS section and saved in settings.json.
KEYCODES = {
    "a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7, "c": 8, "v": 9,
    "b": 11, "q": 12, "w": 13, "e": 14, "r": 15, "y": 16, "t": 17, "o": 31, "u": 32,
    "i": 34, "p": 35, "l": 37, "j": 38, "k": 40, "n": 45, "m": 46,
    "1": 18, "2": 19, "3": 20, "4": 21, "5": 23, "6": 22, "7": 26, "8": 28, "9": 25, "0": 29,
    "-": 27, "=": 24, "[": 33, "]": 30, "\\": 42, ";": 41, "'": 39, ",": 43, ".": 47, "/": 44, "`": 50,
    "space": 49, "tab": 48, "return": 36, "backspace": 51,
    "lshift": 56, "rshift": 60, "lctrl": 59, "rctrl": 62, "loption": 58, "roption": 61,
    "left": 123, "right": 124, "down": 125, "up": 126,
    # older names, still accepted in settings.json
    "shift": 56, "ctrl": 59, "option": 58,
}
KEY_NAMES = {}                 # keycode -> name
for _name, _code in KEYCODES.items():
    KEY_NAMES.setdefault(_code, _name)
MODIFIER_FLAGS = {56: Quartz.kCGEventFlagMaskShift, 60: Quartz.kCGEventFlagMaskShift,
                  59: Quartz.kCGEventFlagMaskControl, 62: Quartz.kCGEventFlagMaskControl,
                  58: Quartz.kCGEventFlagMaskAlternate, 61: Quartz.kCGEventFlagMaskAlternate}


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

    def __init__(self, handling):
        self.codes = {}
        self.src = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
        self.h = handling

    @property
    def h(self):
        return self._h

    @h.setter
    def h(self, handling):
        """New handling settings: also picks up changed controls (keys held under the old
        bindings are released first)."""
        self._h = handling
        codes = {action: KEYCODES[name] for action, name in handling.bindings().items()}
        codes[core.DAS_LEFT] = codes[core.LEFT]
        codes[core.DAS_RIGHT] = codes[core.RIGHT]
        if codes != self.codes:
            if self.codes:
                self.release_all()
            self.codes = codes

    def _post(self, code, down):
        ev = Quartz.CGEventCreateKeyboardEvent(self.src, code, down)
        if code in MODIFIER_FLAGS:
            Quartz.CGEventSetType(ev, Quartz.kCGEventFlagsChanged)
            Quartz.CGEventSetFlags(ev, MODIFIER_FLAGS[code] if down else 0)
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
