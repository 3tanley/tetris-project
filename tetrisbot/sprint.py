"""Sprint mode: 6-3 stacking advice (40 lines, tetrises only).

6-3 stacking: the well is column 7 (index 6), with a 6-wide stack on its left and a
3-wide stack on its right. Every I goes down the well for a tetris; everything else
keeps both stacks flat and clean. Rules (Hard Drop wiki "Tetris stacking" + the 6-3
sprint guides):

  * never cover the well, never make holes
  * flat but not perfectly flat: keep a spot for every piece, S and Z especially
  * no other column more than 2 deep (that needs an I, which belongs in the well)
  * keep the 3-wide side level with the 6-wide side
  * the 3-wide side is built in 4-row blocks, each one of the user's six patterns
    (RIGHT_PATTERNS); a piece only goes there as the next piece of a pattern
  * I: tetris when 4 rows are ready; otherwise hold it ("keep an I in reserve") or lay
    it flat - never burn it in the well for fewer lines
  * no soft drops, fewest key presses (sprint is about speed)

The advice is a short beam search: the piece in play (with hold, real key paths), then
the next pieces with straight drops, scored by the rules above.

SprintCoach follows the user's game (fed by coach.Watcher) and builds the solve panel:
the board, the well, the piece in play where it should go (outlined), and the next
`preview` pieces of the plan, numbered (Handling.sprint_preview, 0-5). SprintBrain is
the same advice played by the bot (BOT PLAYS on): controller.Bot drives it like the
Blitz Brain.
"""
from collections import Counter
from itertools import combinations

from . import core, planner
from .coach import Events

WELL = 6                       # column 7
LEFT = range(0, WELL)          # the 6-wide stack
RIGHT = range(WELL + 1, core.W)  # the 3-wide stack
GOAL = 40
DEPTH = 3                      # pieces planned at least (current + next 2)
BEAM = 10
PREVIEW = 2                    # planned pieces shown after the one in play (0-5)
_NOT_WELL = core.FULL & ~(1 << WELL)


def depth_for(preview):
    """Pieces to plan so the panel can show `preview` pieces after the one in play."""
    return 1 + max(DEPTH - 1, min(5, preview))


# The 3-wide side: every 4 rows of it are one of these
# patterns (rows top -> bottom, the well side on the left), 3 pieces each, placed
# bottom-up without tucks.
RIGHT_PATTERNS = [
    ("JJZ", "JZZ", "JZL", "LLL"),
    ("TLL", "TTL", "TTL", "TTT"),
    ("JJJ", "OOJ", "OOL", "LLL"),
    ("SLL", "SSL", "JSL", "JJJ"),
    ("LLL", "LLL", "OOL", "OOL"),
    ("JJJ", "ZZJ", "JZZ", "JJJ"),
]
_FULL3 = (1 << 12) - 1           # a finished block: 3 columns x 4 rows, bit = 3 * row + column
OFF_PATTERN = 25.0               # score per 4-row block of the 3-wide side that is no pattern
BALANCE = 1.0                    # score per row the two sides' average heights differ


def _pattern_pieces(rows):
    """Split a pattern into its pieces: [(letter, cells)], cells = (column, row) from the
    bottom-left. Two touching pieces of the same letter are separated by shape."""
    by = {}
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            by.setdefault(ch, []).append((i, len(rows) - 1 - j))
    out = []
    for p, cells in by.items():
        if len(cells) == 4:
            out.append((p, tuple(sorted(cells))))
            continue
        for a in combinations(cells, 4):
            b = tuple(c for c in cells if c not in a)
            if core.identify(p, a) and core.identify(p, b):
                out += [(p, tuple(sorted(a))), (p, b)]
                break
        else:
            raise ValueError(f"pattern {rows}: can't split the {p} cells into pieces")
    return out


def _pattern_states():
    """Every partly built block reachable by placing pattern pieces bottom-up (each piece
    resting on the block floor or on blocks below, nothing hanging): mask -> pieces that
    may go on it next."""
    nxt = {}
    for rows in RIGHT_PATTERNS:
        pieces = [(p, sum(1 << (3 * y + x) for x, y in cs), cs) for p, cs in _pattern_pieces(rows)]
        todo, seen = [0], {0}
        while todo:
            m = todo.pop()
            nxt.setdefault(m, set())
            hs = [next((y for y in range(4) if not m >> (3 * y + x) & 1), 4) for x in range(3)]
            for p, pm, cs in pieces:
                if m & pm:
                    continue
                if all(min(y for cx, y in cs if cx == x) == hs[x] for x in {cx for cx, _ in cs}):
                    nxt[m].add(p)
                    if (m | pm) not in seen:
                        seen.add(m | pm)
                        todo.append(m | pm)
    return {m: frozenset(v) for m, v in nxt.items()}


_NEXT = _pattern_states()          # mask -> pieces that continue a pattern

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
# the same profiles as height steps between neighbouring columns: a piece fits at x when
# hs[x+1]-hs[x], hs[x+2]-hs[x+1], ... equal its profile's steps
_STEPS = {_p: frozenset(tuple(pr[i + 1] - pr[i] for i in range(len(pr) - 1)) for pr in profs)
          for _p, profs in _PROFILES.items()}
_FIT_WEIGHT = {"S": 1.5, "Z": 1.5, "O": 1.2, "T": 0.8, "J": 0.8, "L": 0.8}


def ready_rows(board):
    """Rows from the bottom that are full except the well (4 = tetris ready)."""
    n = 0
    while n < core.H and board.rows[n] == _NOT_WELL:
        n += 1
    return n


def _windows(hs, regions):
    """Every run of 0-3 height steps inside the regions (pieces are 1-4 columns wide)."""
    out = set()
    for region in regions:
        steps = [hs[x + 1] - hs[x] for x in range(region[0], region[-1])]
        for w in range(4):
            for i in range(len(steps) - w + 1):
                out.add(tuple(steps[i:i + w]))
    return out


def _fits(hs, piece, regions=(LEFT, RIGHT), windows=None):
    """Can `piece` go somewhere without a hole and without touching the well?"""
    if windows is None:
        windows = _windows(hs, regions)
    return not _STEPS[piece].isdisjoint(windows)


def right_blocks(board, base=0, hs=None):
    """The 3-wide side in 4-row blocks from row `base` up: (blocks that are not a
    pattern, pieces that can go there next by the patterns)."""
    hs = hs or board.col_heights()
    top = max(hs[x] for x in RIGHT)
    bad, nxt = 0, None
    for y in range(base, top, 4):
        m = 0
        for dy in range(4):
            if y + dy < core.H:
                m |= (board.rows[y + dy] >> RIGHT[0] & 7) << (3 * dy)
        if m not in _NEXT and m != _FULL3:
            bad += 1
        elif nxt is None and m != _FULL3:
            nxt = _NEXT[m]
    return bad, (_NEXT[0] if nxt is None else nxt)


def align(board):
    """Row where the 3-wide side's blocks start (0-3): the one that fits the patterns
    best (only line clears other than tetrises shift it)."""
    hs = board.col_heights()
    return min(range(4), key=lambda b: (right_blocks(board, b, hs)[0], b))


def evaluate(board, hold=None, base=0):
    """Board quality for 6-3 stacking (higher = better). `base`: see align()."""
    hs = board.col_heights()
    holes, covered = planner.holes_covered(board, hs)
    in_well = sum(board.rows[y] >> WELL & 1 for y in range(hs[WELL]))
    bump = sum(abs(hs[i] - hs[i + 1]) for i in range(LEFT[0], LEFT[-1]))
    # the 3-wide side follows the patterns; only once it is off them (the user stacked
    # something else) does it fall back to the flat-stack rules
    off, right_next = right_blocks(board, base, hs)
    regions = (LEFT,) if not off else (LEFT, RIGHT)
    if off:
        bump += sum(abs(hs[i] - hs[i + 1]) for i in range(RIGHT[0], RIGHT[-1]))
    # columns more than 2 deep need an I; the well's neighbours only count their own side
    deep = 0
    for region in regions:
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
             - BALANCE * abs(left_avg - right_avg) + 1.2 * min(ready, 4) + 0.2 * max(0, ready - 4))
    score -= 0.8 * max(0, maxh - 9) + 0.5 * max(0, maxh - 13) ** 2
    score -= OFF_PATTERN * off
    windows = _windows(hs, regions)
    score -= sum(w for p, w in _FIT_WEIGHT.items()
                 if not (_fits(hs, p, windows=windows) or (not off and p in right_next)))
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
    __slots__ = ("score", "acc", "board", "i", "hold", "path", "base")

    def __init__(self, acc, board, i, hold, path, base):
        self.acc, self.board, self.i, self.hold, self.path, self.base = acc, board, i, hold, path, base
        self.score = acc + evaluate(board, hold, base)


def plan(board, cur, hold, queue, depth=DEPTH, beam=BEAM):
    """Best placements for the piece in play and the next ones. Returns a list of
    (planner.Step, cells, lines_cleared): the first has real key paths, the rest are
    straight drops (where they go if the plan holds)."""
    seq = [cur] + list(queue)
    depth = min(depth, len(seq))
    nodes = [Node(0.0, board, 0, hold, [], align(board))]
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
                    out.append(Node(n.acc + r, nb, ni, nh, n.path + [(planner.Step(used_hold, pl), cells, lines)],
                                    (n.base - lines) % 4))
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
def display(board, steps, lines_done=0, preview=PREVIEW):
    """Solve-panel picture: the board in grey, the piece in play in colour (outlined) and
    the next `preview` planned pieces dimmed and numbered. Pieces after a line clear are
    drawn where they will sit on the stack (the cleared rows stay in the picture)."""
    b = board.copy()
    ymap = list(range(core.H))         # row after the clears so far -> row in the picture
    shown = []
    for k, (st, cells, _) in enumerate(steps[:1 + max(0, preview)]):
        shown.append((k, st.pl.piece, [(x, ymap[y]) for x, y in cells]))
        cleared = set(b.place_cells(cells))
        if cleared:
            keep = [ymap[y] for y in range(core.H) if y not in cleared]
            ymap = keep + list(range(ymap[-1] + 1, ymap[-1] + 1 + len(cleared)))
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
        tetris = next((k for k, (_, _, cl) in enumerate(steps[:1 + max(0, preview)]) if cl == 4), None)
        if tetris == 0:
            note = "TETRIS: I down the well"
        elif tetris is not None:
            note = f"tetris with piece {tetris + 1}"
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

    def __init__(self, log=print, threaded=False, preview=PREVIEW):
        self.log = log
        self.preview = preview         # planned pieces shown after the one in play
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
        self.steps = plan(board, cur, hold, queue, depth_for(self.preview))
        self.rec = self.steps[0][0] if self.steps else None
        self.display = display(board, self.steps, self.lines, self.preview)

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


class SprintBrain:
    """BOT PLAYS in Sprint: plays the 6-3 advice. Has the parts of brain.Brain's interface
    that controller.Bot uses (decide / on_lock / clone / adopt / stage / ts / plan)."""

    def __init__(self, log=print, preview=PREVIEW):
        self.log = log
        self.preview = preview
        self.stage = "6-3"
        self.ts = None                 # (Blitz setup state: never used here)
        self.plan = []
        self.stats = Counter()
        self.display = None
        self.bag_view = None
        self.lines = self.tetrises = 0

    def clone(self):
        b = SprintBrain.__new__(SprintBrain)
        b.__dict__.update(self.__dict__)
        b._real_log = getattr(self, "_real_log", self.log)
        b._buffer = []
        b.log = b._buffer.append       # held back until this copy is adopted
        b.stats = Counter(self.stats)
        return b

    def adopt(self):
        real = getattr(self, "_real_log", None)
        if real is not None:
            for m in getattr(self, "_buffer", []):
                real(m)
            self.log, self._buffer = real, []
        return self

    def done(self):
        return self.lines >= GOAL

    def decide(self, board, cur, hold, queue):
        steps = plan(board, cur, hold, queue, depth_for(self.preview))
        self.display = display(board, steps, self.lines, self.preview)
        return steps[0][0] if steps else None

    def on_lock(self, step, hold_was_empty, cleared, board):
        n = len(cleared)
        self.lines += n
        if n == 4:
            self.tetrises += 1
            self.stats["tetris"] += 1
        elif n:
            self.stats["burn"] += n
        if self.lines >= GOAL and self.lines - n < GOAL:
            self.log(f"[sprint] {GOAL} lines: {self.tetrises} tetrises")
