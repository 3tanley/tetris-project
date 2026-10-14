"""Handling settings (mirrors TETR.IO's HANDLING panel) and the input timings
derived from them. Saved to settings.json next to the project."""
import json
import os
from dataclasses import asdict, dataclass, fields

FRAME_MS = 1000.0 / 60.0
SDF_INF = 41                  # TETR.IO shows SDF 41 as "∞"
PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json")


@dataclass
class Handling:
    # --- TETR.IO handling (defaults = the user's screenshot)
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
    # openers the bot may build (templates.FAMILY_PRIORITY names, comma separated)
    openers: str = "JAWS,SDPC,MS2,MS,MS3"
    # game mode (overlay MODES row). Only BLITZ is implemented; SPRINT / VOD are placeholders
    mode: str = "BLITZ"

    def opener_on(self, fam):
        return fam in {f.strip() for f in self.openers.split(",")}

    def set_opener(self, fam, on):
        cur = [f.strip() for f in self.openers.split(",") if f.strip() and f.strip() != fam]
        self.openers = ",".join(cur + ([fam] if on else []))

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
        return h


def ms_to_frames(ms):
    return ms / FRAME_MS
