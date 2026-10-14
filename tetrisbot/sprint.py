"""Sprint mode: 6-3 stacking advice (40 lines, tetrises only).

6-3 stacking: the well is column 7 (index 6), with a 6-wide stack on its left and a
3-wide stack on its right. Every I goes down the well for a tetris; everything else
keeps both stacks flat and clean. Rules (Hard Drop wiki "Tetris stacking" + the 6-3
sprint guides):

  * never cover the well, never make holes
  * flat but not perfectly flat: keep a spot for every piece, S and Z especially
  * no other column more than 2 deep (that needs an I, which belongs in the well)
  * keep the 3-wide side level with the 6-wide side
  * I: tetris when 4 rows are ready; otherwise hold it ("keep an I in reserve") or lay
    it flat - never burn it in the well for fewer lines
  * no soft drops, fewest key presses (sprint is about speed)

The advice is a short beam search: the piece in play (with hold, real key paths), then
the next pieces with straight drops, scored by the rules above.

SprintCoach follows the user's game (fed by coach.Watcher) and builds the solve panel:
the board, the well, the piece in play where it should go (outlined), and the next
pieces of the plan, numbered.
"""
from . import core, planner
from .coach import Events

WELL = 6                       # column 7
LEFT = range(0, WELL)          # the 6-wide stack
RIGHT = range(WELL + 1, core.W)  # the 3-wide stack
GOAL = 40
DEPTH = 3                      # pieces planned (current + next 2)
BEAM = 10
_NOT_WELL = core.FULL & ~(1 << WELL)

# bottom profile of every piece / rotation: (width, [lowest cell per column]) - a piece
# fits cleanly (no hole under it) where the column heights follow that profile
_PROFILES = {}
for _p in "IJLOSTZ":
    seen = set()
    for _r in range(4):
        cs = core.SHAPES[_p][_r]
        x0, y0 = min(c[0] for c in cs), min(c[1] for c in cs)
        prof = tuple(min(y for x, y in cs if x == cx) - y0 for cx in range(x0, max(c[0] for c in cs) + 1))
        seen.add(prof)
    _PROFILES[_p] = sorted(seen)
_FIT_WEIGHT = {"S": 1.5, "Z": 1.5, "O": 1.2, "T": 0.8, "J": 0.8, "L": 0.8}


def ready_rows(board):
    """Rows from the bottom that are full except the well (4 = tetris ready)."""
    n = 0
    while n < core.H and board.rows[n] == _NOT_WELL:
        n += 1
    return n


def _fits(hs, piece):
    """Can `piece` go somewhere without a hole and without touching the well?"""
    for prof in _PROFILES[piece]:
        w = len(prof)
        for region in (LEFT, RIGHT):
            lo, hi = region[0], region[-1]
            for x in range(lo, hi - w + 2):
                base = hs[x] - prof[0]
                if all(hs[x + i] - prof[i] == base for i in range(1, w)):
                    return True
    return False


def evaluate(board, hold=None):
    """Board quality for 6-3 stacking (higher = better)."""
    hs = board.col_heights()
    holes = covered = 0
    for x in range(core.W):
        seen = False
        for y in range(hs[x] - 1, -1, -1):
            if board.rows[y] >> x & 1:
                seen = True
            elif seen:
                holes += 1
                covered += hs[x] - y
    in_well = sum(board.rows[y] >> WELL & 1 for y in range(hs[WELL]))
    bump = sum(abs(hs[i] - hs[i + 1]) for i in range(LEFT[0], LEFT[-1]))
    bump += sum(abs(hs[i] - hs[i + 1]) for i in range(RIGHT[0], RIGHT[-1]))
    # columns more than 2 deep need an I; the well's neighbours only count their own side
    deep = 0
    for region in (LEFT, RIGHT):
        lo, hi = region[0], region[-1]
        for x in region:
            left = hs[x - 1] if x > lo else 99
            right = hs[x + 1] if x < hi else 99
            if left == 99 and right == 99:
                continue
            d = min(left, right) - hs[x]
            if d > 2:
                deep += d - 2
    left_avg = sum(hs[x] for x in LEFT) / len(LEFT)
    right_avg = sum(hs[x] for x in RIGHT) / len(RIGHT)
    maxh = max(hs)
    ready = ready_rows(board)
    score = (-6.0 * holes - 1.0 * covered - 5.0 * in_well - 0.45 * bump - 3.0 * deep
             - 0.35 * abs(left_avg - right_avg) + 1.2 * min(ready, 4) + 0.2 * max(0, ready - 4))
    score -= 0.8 * max(0, maxh - 9) + 0.5 * max(0, maxh - 13) ** 2
    score -= sum(w for p, w in _FIT_WEIGHT.items() if not _fits(hs, p))
    if hold == "I":
        score += 1.5                         # an I in reserve
    return score


def reward(lines, keys=None, maxh=0):
    """Score for the placement itself: tetrises good, burnt lines bad (unless high),
    soft drops and extra key presses cost time."""
    s = 0.0
    if lines == 4:
        s += 25.0
    elif lines:
        s += -6.0 if maxh < 12 else 2.0 * lines
    if keys is not None:
        s -= 0.25 * len(keys)
        if core.SOFT in keys:
            s -= 3.0
    return s


class Node:
    __slots__ = ("score", "acc", "board", "i", "hold", "path")

    def __init__(self, acc, board, i, hold, path):
        self.acc, self.board, self.i, self.hold, self.path = acc, board, i, hold, path
        self.score = acc + evaluate(board, hold)


def plan(board, cur, hold, queue, depth=DEPTH, beam=BEAM):
    """Best placements for the piece in play and the next ones. Returns a list of
    (planner.Step, cells, lines_cleared): the first has real key paths, the rest are
    straight drops (where they go if the plan holds)."""
    seq = [cur] + list(queue)
    depth = min(depth, len(seq))
    nodes = [Node(0.0, board, 0, hold, [])]
    for d in range(depth):
        out = []
        for n in nodes:
            maxh = n.board.height()
            for p, used_hold, ni, nh in planner._choices(seq, n.i, n.hold) or []:
                if d == 0:
                    opts = [(pl.cells, pl) for pl in planner.movegen(n.board, p).values()]
                else:
                    opts = [(c, None) for c in core.drop_cells(n.board, p)]
                for cells, pl in opts:
                    if any(y >= 20 for _, y in cells):
                        continue                 # tops out
                    nb = n.board.copy()
                    lines = len(nb.place_cells(cells))
                    r = reward(lines, pl.inputs if pl else None, maxh) * (0.9 ** d)
                    if pl is None:
                        rot, x, y = _locate(p, cells)
                        pl = core.Placement(p, rot, x, y, [], None)
                    out.append(Node(n.acc + r, nb, ni, nh, n.path + [(planner.Step(used_hold, pl), cells, lines)]))
        if not out:
            break
        out.sort(key=lambda n: n.score, reverse=True)
        nodes = out[:beam]
    return nodes[0].path if nodes and nodes[0].path else []


def _locate(piece, cells):
    for x, y, r in core.identify(piece, list(cells)):
        return r, x, y
    return 0, 0, 0


# ------------------------------------------------------------ display
def display(board, steps, lines_done=0):
    """Solve-panel picture: the board in grey, the piece in play in colour (outlined) and
    the next planned pieces dimmed and numbered. Stops after the first line clear (the
    rows move after that)."""
    shown = []
    for k, (st, cells, cleared) in enumerate(steps):
        shown.append((k, st.pl.piece, cells))
        if cleared:
            break
    top = max([board.height()] + [y + 1 for _, _, cs in shown for _, y in cs])
    n = max(8, min(20, top + 2))
    grid = [["G" if board.filled(x, y) else "." for x in range(core.W)] for y in range(n)]
    hint, labels = [], []
    for k, p, cells in shown:
        for x, y in cells:
            if y < n:
                grid[y][x] = p if k == 0 else p.lower()
        if k == 0:
            hint = [(n - 1 - y, x) for x, y in cells if y < n]
        else:
            x, y = max(cells, key=lambda c: (c[1], -c[0]))
            if y < n:
                labels.append((n - 1 - y, x, str(k + 1)))
    rows = ["".join(grid[y]) for y in range(n - 1, -1, -1)]
    ready = ready_rows(board)
    left = max(0, GOAL - lines_done)
    if steps:
        if steps[0][2] == 4:
            note = "TETRIS: I down the well"
        elif ready >= 4:
            note = f"tetris ready ({ready} rows) - waiting for an I"
        else:
            note = f"{ready}/4 rows ready"
    else:
        note = ""
    return {"title": f"Sprint 6-3  ·  {left} lines to go", "sub": f"well: column {WELL + 1}  ·  {note}",
            "rows": rows, "hint": hint, "labels": labels, "well": WELL}


class SprintCoach(Events):
    """Follows the user's sprint game and suggests 6-3 placements. Same events as Coach."""

    def __init__(self, log=print, threaded=False):
        self.log = log
        self.spawn = None
        self.rec = None                # suggested Step for the piece in play
        self.steps = []
        self.display = None
        self.pieces = self.lines = self.tetrises = 0
        self.suggested = self.followed = 0
        self.board = core.Board()
        super().__init__(log, threaded)

    def _begin(self, board, cur, hold, queue, fresh):
        self.pieces = self.lines = self.tetrises = 0
        self.suggested = self.followed = 0
        if not fresh:
            self.log("[sprint] joined mid-game: lines are counted from here")
        self._spawned(board, cur, hold, queue)

    def _spawned(self, board, cur, hold, queue):
        self.spawn = (cur, hold, list(queue))
        self.board = board
        if self.threaded and self._q.qsize() > 0:
            self.rec = None            # the user is already further: don't plan for a past piece
            return
        self.steps = plan(board, cur, hold, queue)
        self.rec = self.steps[0][0] if self.steps else None
        self.display = display(board, self.steps, self.lines)

    def _locked(self, before, piece, rot, x, y, used_hold, after, cleared):
        self.pieces += 1
        self.lines += len(cleared)
        if len(cleared) == 4:
            self.tetrises += 1
        rec = self.rec
        if rec is not None:
            self.suggested += 1
            if rec.pl.piece == piece and rec.pl.cells == core.cells_of(piece, rot, x, y):
                self.followed += 1
        self.rec = None
        if self.lines >= GOAL and self.lines - len(cleared) < GOAL:
            self.log(f"[sprint] {GOAL} lines in {self.pieces} pieces, {self.tetrises} tetrises")

    def advice(self):
        rec = self.rec
        if rec is None:
            return "watching…" if self.spawn else "waiting for a game"
        cur = self.spawn[0]
        what = f"hold {cur}, place {rec.pl.piece}" if rec.hold else f"place {rec.pl.piece}"
        if self.steps and self.steps[0][2] == 4:
            what += " - TETRIS"
        return f"next: {what}"
