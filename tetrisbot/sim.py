"""Headless 7-bag simulator for testing the brain without TETR.IO.

Every step is replayed key by key from spawn (same kicks as the game), so the
key sequences the bot would send are validated, not just the target cells.
"""
import random
import sys
import time

from . import core
from .brain import Brain


def replay(board, piece, keys, gravity=False):
    """Apply keys to a freshly spawned piece. Returns (rot, x, y, last_rot, kick) at hard drop.
    gravity=True drops the piece after every key (20G)."""
    x, y, r = core.SPAWN_X, core.SPAWN_Y, 0
    if board.collides(piece, r, x, y):
        y += 1
    last_rot, kick = False, -1
    if gravity:
        y = board.drop_y(piece, r, x, y)
    for k in keys:
        if gravity and k != core.HARD:
            pass
        if k in (core.LEFT, core.RIGHT):
            nx = x + (-1 if k == core.LEFT else 1)
            if not board.collides(piece, r, nx, y):
                x, last_rot = nx, False
        elif k in (core.DAS_LEFT, core.DAS_RIGHT):
            nx = core.slide(board, piece, r, x, y, -1 if k == core.DAS_LEFT else 1)
            if nx != x:
                x, last_rot = nx, False
        elif k in (core.CW, core.CCW, core.R180):
            nr = (r + {core.CW: 1, core.CCW: 3, core.R180: 2}[k]) % 4
            for i, (kx, ky) in enumerate(core.kicks(piece, r, nr)):
                if not board.collides(piece, nr, x + kx, y + ky):
                    x, y, r, last_rot, kick = x + kx, y + ky, nr, True, i
                    break
        elif k == core.SOFT:
            ny = board.drop_y(piece, r, x, y)
            if ny != y:
                y, last_rot = ny, False
        elif k == core.HARD:
            ny = board.drop_y(piece, r, x, y)
            if ny != y:
                last_rot = False
            return r, x, ny, last_rot, kick
        if gravity:
            ny = board.drop_y(piece, r, x, y)
            if ny != y:
                y, last_rot = ny, False
    raise ValueError("no hard drop in key sequence")


class Game:
    def __init__(self, seed=None, preview=5):
        self.rng = random.Random(seed)
        self.queue = []
        self.preview = preview
        self.board = core.Board()
        self.hold = None
        self.lines = 0
        self.gravity = False               # True: the piece falls to the floor after every key (20G)
        self._fill()
        self.current = self.queue.pop(0)
        self._fill()

    def _fill(self):
        while len(self.queue) < self.preview + 7:
            bag = list(core.PIECES)
            self.rng.shuffle(bag)
            self.queue += bag

    def visible(self):
        return self.queue[: self.preview]

    def apply(self, step):
        """Perform hold (optional) + key sequence. Returns (cells, cleared rows, spin, hold_was_empty)."""
        hold_was_empty = self.hold is None
        piece = self.current
        if step.hold:
            if self.hold is None:
                self.hold = piece
                piece = self.queue.pop(0)
            else:
                self.hold, piece = piece, self.hold
        assert piece == step.pl.piece, f"expected {step.pl.piece} got {piece}"
        keys = [k for k in step.keys() if k != core.HOLD]
        r, x, y, last_rot, kick = replay(self.board, piece, keys, gravity=self.gravity)
        cells = core.cells_of(piece, r, x, y)
        assert cells == step.pl.cells, f"keys {keys} landed {cells}, planned {step.pl.cells}"
        spin = core.tspin_kind(self.board, r, x, y, last_rot, kick) if piece == "T" else None
        cleared = self.board.place_cells(cells)
        self.lines += len(cleared)
        self.current = self.queue.pop(0)
        self._fill()
        return cells, cleared, spin, hold_was_empty


def run(pieces=200, seed=None, verbose=True):
    log = print if verbose else (lambda *a: None)
    g = Game(seed)
    from .brain import Lookahead
    br = Brain(log=log, lookahead=Lookahead(threaded=False))
    br.bag.reset(aligned=True)
    t0 = time.time()
    worst = 0.0
    for n in range(pieces):
        t = time.time()
        step = br.decide(g.board, g.current, g.hold, g.visible())
        worst = max(worst, time.time() - t)
        if step is None:
            log("[sim] no move, topped out")
            break
        cells, cleared, spin, hold_was_empty = g.apply(step)
        br.on_lock(step, hold_was_empty, cleared, g.board)
        if g.board.height() > 20:
            log("[sim] topped out")
            break
    dt = time.time() - t0
    st = dict(br.stats)
    st.update(lines=g.lines, secs=round(dt, 2), worst_ms=round(worst * 1000), pps_cpu=round(st.get("pieces", 0) / max(dt, 1e-9), 1))
    return st


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    print(run(n, seed))
