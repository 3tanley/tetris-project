"""Handling settings (mirrors TETR.IO's HANDLING panel) and the input timings
derived from them. Saved to settings.json next to the project."""
import json
import os
from dataclasses import asdict, dataclass, fields

from . import core

FRAME_MS = 1000.0 / 60.0
SDF_INF = 41                  # TETR.IO shows SDF 41 as "∞"
PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json")


@dataclass
class Handling:
    # --- TETR.IO handling (CONFIG → HANDLING)
    arr_ms: float = 0.0
    das_ms: float = 110.0
    dcd_ms: float = 0.0
    sdf: float = SDF_INF
    prevent_accidental_hard_drops: bool = True
    cancel_das_on_direction_change: bool = False
    prefer_soft_drop_over_movement: bool = True
    irs: str = "TAP"          # OFF | HOLD | TAP
    ihs: str = "TAP"
    # --- bot behaviour
    optimize: str = "FINESSE"  # FINESSE (fewest key presses, ~3.3/piece like top Blitz players) | SPEED (shortest time, taps a lot)
    key_gap_ms: float = 8.0    # pause after each key release
    max_tap_ms: float = 12.0   # longest a tap is ever held
    check_piece: bool = True   # confirm piece/ghost position before every hard drop
    gravity: str = "AUTO"      # AUTO | LOW | HIGH
    use_180: bool = True
    # openers the bot may build (templates.FAMILY_PRIORITY names, comma separated), in
    # priority order (dragged in the Openers window): the first that can be built wins
    openers: str = "JAWS,SDPC,MS2,MS,MS3"
    # game mode (overlay MODES row): BLITZ | SPRINT (VOD is a placeholder)
    mode: str = "BLITZ"
    # Sprint panel: planned pieces shown after the one in play (0-5, settings SPRINT slider)
    sprint_preview: int = 2
    # --- controls: the keys bound in TETR.IO (CONFIG → CONTROLS), names from keys.KEYCODES.
    # Defaults are TETR.IO's own defaults.
    bind_left: str = "left"
    bind_right: str = "right"
    bind_soft_drop: str = "down"
    bind_hard_drop: str = "space"
    bind_ccw: str = "z"
    bind_cw: str = "up"
    bind_180: str = "a"
    bind_hold: str = "c"

    def bindings(self):
        """Planner action -> key name."""
        return {action: getattr(self, f) for action, f in BINDINGS}

    def opener_order(self):
        """Switched-on openers, highest priority first."""
        return [f.strip() for f in self.openers.split(",") if f.strip()]

    def opener_on(self, fam):
        return fam in self.opener_order()

    def set_opener(self, fam, on):
        """Switch an opener on (it goes to the bottom of the priority list) or off."""
        cur = [f for f in self.opener_order() if f != fam]
        self.openers = ",".join(cur + ([fam] if on else []))

    def move_opener(self, fam, index):
        """Move a switched-on opener to position `index` of the priority list."""
        cur = [f for f in self.opener_order() if f != fam]
        cur.insert(max(0, min(index, len(cur))), fam)
        self.openers = ",".join(cur)

    # ------------------------------------------------------------ timings
    @property
    def sdf_infinite(self):
        return self.sdf >= SDF_INF

    def tap_ms(self):
        """How long a single press is held. Always shorter than DAS, otherwise the
        game would start auto-shifting (with ARR 0 the piece flies to the wall)."""
        return max(0.3, min(self.max_tap_ms, 0.75 * self.das_ms))

    def das_hold_ms(self, cells=9):
        """Hold time that guarantees DAS fires and auto-repeat reaches the wall.
        Two frames of margin: TETR.IO reads keys once per frame, and during effects
        (ALL CLEAR etc.) a late frame can see the press and the release together - the
        2026-10-09 23:20 recording shows a DAS slide that only moved one cell."""
        repeat = self.arr_ms * cells if self.arr_ms > 0 else 0.0
        return self.das_ms + self.dcd_ms + repeat + 2 * FRAME_MS + 3.0

    def softdrop_ms(self):
        """Hold for one full game frame so an instant (∞) soft drop registers."""
        return FRAME_MS + 5.0

    def action_cost(self, action):
        """(key presses, milliseconds) for one planner action."""
        g = self.key_gap_ms
        if action in ("DL", "DR"):
            return 1, self.das_hold_ms() + g
        if action == "SD":
            return 1, (self.softdrop_ms() if self.sdf_infinite else 250.0) + g
        return 1, self.tap_ms() + g

    def signature(self):
        """Everything that changes which key sequences the planner picks."""
        return (self.optimize, round(self.das_hold_ms(), 2), round(self.tap_ms(), 2),
                self.sdf_infinite, self.key_gap_ms, self.use_180)

    # ------------------------------------------------------------ persistence
    def save(self, path=PATH):
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path=PATH):
        h = cls()
        try:
            with open(path) as f:
                data = json.load(f)
            names = {fl.name for fl in fields(cls)}
            for k, v in data.items():
                if k in names:
                    setattr(h, k, v)
        except (OSError, ValueError):
            pass
        from .keys import KEYCODES          # needs Quartz, so only imported here
        for _, f in BINDINGS:
            if getattr(h, f) not in KEYCODES:
                print(f"settings.json: unknown key {getattr(h, f)!r} for {f}, using the default")
                setattr(h, f, getattr(cls, f))
        return h


# Planner action -> the Handling field with its key, in the order the CONTROLS section shows them.
BINDINGS = [
    (core.LEFT, "bind_left"),
    (core.RIGHT, "bind_right"),
    (core.SOFT, "bind_soft_drop"),
    (core.HARD, "bind_hard_drop"),
    (core.CCW, "bind_ccw"),
    (core.CW, "bind_cw"),
    (core.R180, "bind_180"),
    (core.HOLD, "bind_hold"),
]


def ms_to_frames(ms):
    return ms / FRAME_MS
