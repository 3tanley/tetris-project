"""Search: fill a setup template, solve a perfect clear, or pick a heuristic move.

All searches walk the piece sequence with hold the same way: at each step you may
  * place the current piece,
  * place the held piece (current goes to hold), or
  * with an empty hold, hold the current piece and place the next one.
"""
import threading
import time
from collections import Counter

from . import core
from .handling import Handling

_GEN_CACHE = {}
_GEN_CACHE_MAX = 60000     # ~8 KB per entry
_GEN_EPOCH = 0
# safe = high-gravity mode (soft drop after every input, see core.generate).
SETTINGS = {"safe": False, "handling": Handling(), "gravity_rps": 0.0, "air_used_ms": 0.0}
_COSTS = {}


def configure(handling=None, safe=None, gravity_rps=None):
    if handling is not None:
        SETTINGS["handling"] = handling
    if safe is not None:
        SETTINGS["safe"] = safe
    if gravity_rps is not None:
        SETTINGS["gravity_rps"] = gravity_rps


def _costs(h):
    sig = h.signature()
    c = _COSTS.get(sig)
    if c is None:
        c = {a: h.action_cost(a) for a in (core.LEFT, core.RIGHT, core.CW, core.CCW, core.R180, core.HOLD,
                                           core.HARD, core.SOFT, core.DAS_LEFT, core.DAS_RIGHT)}
        _COSTS[sig] = c
    return c


# Air-time steps (ms). The measured gravity drifts with every reading; rounding DOWN to
# a few fixed steps keeps the move-generation cache valid (and only ever assumes less
# air time than there is). Past ~1 s every input sequence fits anyway.
_AIR_STEPS = (0, 20, 40, 60, 80, 100, 130, 160, 200, 250, 320, 400, 500, 650, 800, 1000)


def _air_ms(board):
    """High gravity: how long after spawn the piece is still above the stack (ms),
    from the measured gravity with a 2x margin, rounded down to an _AIR_STEPS value."""
    g = SETTINGS.get("gravity_rps", 0.0)
    if not SETTINGS["safe"] or g <= 0:
        return 0.0
    rows = core.SPAWN_Y - board.height() - 2
    ms = max(0.0, rows / (2.0 * g) * 1000.0 - SETTINGS.get("air_used_ms", 0.0))
    return float(max(st for st in _AIR_STEPS if st <= ms))


def generate(board, piece, start=None):
    """core.generate with the current handling settings."""
    h = SETTINGS["handling"]
    return core.generate(board, piece, safe=SETTINGS["safe"], costs=_costs(h),
                         finesse=h.optimize == "FINESSE", use_180=h.use_180, start=start,
                         air_ms=0.0 if start is not None else _air_ms(board), ground_das=h.arr_ms <= 0,
                         gravity_rps=_gravity_step())


# Gravity steps (rows/s) for skipping soft drops gravity does anyway: rounded DOWN, so
# the planner never counts on more gravity than was measured, and results stay cached.
_GRAVITY_STEPS = (0, 100, 200, 400, 800, 1200)


def _gravity_step():
    if not SETTINGS["safe"]:
        return 0.0
    g = SETTINGS.get("gravity_rps", 0.0)
    return float(max(st for st in _GRAVITY_STEPS if st <= g))


# ------------------------------------------------------- foreground / background
# The look-ahead plans on a background thread. Python runs one thread at a time, so while
# the bot thread is deciding a move (a piece is falling) the background pauses at its
# next move generation and gives it the whole CPU.
_TL = threading.local()
_FG_IDLE = threading.Event()
_FG_IDLE.set()


def background():
    """True on the look-ahead (background) thread."""
    return getattr(_TL, "bg", False)


class as_background:
    """Mark the current thread as background while inside the block."""

    def __enter__(self):
        self.prev = background()
        _TL.bg = True

    def __exit__(self, *exc):
        _TL.bg = self.prev


class foreground_busy:
    """The bot thread is deciding: background searches wait meanwhile."""

    def __enter__(self):
        self.on = not background()
        if self.on:
            _FG_IDLE.clear()

    def __exit__(self, *exc):
        if self.on:
            _FG_IDLE.set()


def movegen(board, piece):
    if not _FG_IDLE.is_set() and background():
        _FG_IDLE.wait(1.0)
    key = (board.key(), piece, SETTINGS["safe"], SETTINGS["handling"].signature(), _air_ms(board),
           _gravity_step())
    r = _GEN_CACHE.get(key)
    if r is None:
        if len(_GEN_CACHE) > _GEN_CACHE_MAX:
            global _GEN_EPOCH
            _GEN_CACHE.clear()
            _GEN_EPOCH += 1                # warmed templates must be warmed again
        r = generate(board, piece)
        _GEN_CACHE[key] = r
    return r


class Step:
    __slots__ = ("hold", "pl", "slot")

    def __init__(self, hold, pl, slot=None):
        self.hold, self.pl, self.slot = hold, pl, slot

    @property
    def piece(self):
        return self.pl.piece

    def keys(self):
        return ([core.HOLD] if self.hold else []) + list(self.pl.inputs)

    def __repr__(self):
        return f"Step({'hold,' if self.hold else ''}{self.pl}{',' + self.slot if self.slot else ''})"


def _choices(seq, i, hold):
    """(piece_to_place, used_hold, next_i, next_hold) options. '?' = unknown piece."""
    cur = seq[i] if i < len(seq) else "?"
    out = []
    if cur != "?":
        out.append((cur, False, i + 1, hold))
    if i == 0 and SETTINGS.get("hold_locked"):
        return out                     # TETR.IO: only one hold per piece
    if hold not in (None, "?") and hold != cur:
        out.append((hold, True, i + 1, cur))
    if hold is None and cur != "?" and i + 1 < len(seq) and seq[i + 1] not in ("?", cur):
        out.append((seq[i + 1], True, i + 2, cur))
    return out


# ------------------------------------------------------- order feasibility
def order_feasible(tmpl, remaining, hard, seq, hold, locked_first=False):
    """Can `seq` (with one hold slot) fill the `remaining` slots of `tmpl` while
    respecting the hard dependencies (pieces that need rows cleared first)?
    Pure bookkeeping - no move generation - so it is fast enough to try every order of
    the pieces that haven't been seen yet."""
    slots = tmpl.slots
    memo = {}

    def rec(i, h, rem):
        if not rem:
            return True
        key = (i, h, rem)
        r = memo.get(key)
        if r is not None:
            return r
        r = False
        for p, used_hold, ni, nh in _choices(seq, i, h):
            if used_hold and i == 0 and locked_first:
                continue
            for sid in rem:
                if slots[sid].ptype == p and not (hard[sid] & rem):
                    if rec(ni, nh, rem - {sid}):
                        r = True
                        break
            if r:
                break
        memo[key] = r
        return r

    return rec(0, hold, frozenset(remaining))


# ------------------------------------------------------------------ warm-up
def warm_signature():
    """Settings that change move generation: when they change, warmed results are stale."""
    return (SETTINGS["safe"], SETTINGS["handling"].signature(), _air_ms(core.Board()), _gravity_step(),
            _GEN_EPOCH)


def warm_template(tmpl, stop=lambda: False):
    """Generate moves for every state a template can be filled through (each set of
    placed slots), so later searches on it are cache hits. Returns False if `stop()`
    interrupted it (calling it again resumes quickly: finished states are cached)."""
    from .templates import TState, dependencies
    hard, _ = dependencies(tmpl)
    seen = set()

    def rec(b, ts):
        if ts.remaining in seen:
            return True
        seen.add(ts.remaining)
        for sid in ts.remaining:
            if hard[sid] & ts.remaining:
                continue
            if stop():
                return False
            pl = movegen(b, tmpl.slots[sid].ptype).get(ts.slot_cells(sid))
            if pl is None:
                continue
            nb = b.copy()
            cleared = nb.place_cells(pl.cells)
            nts = ts.copy()
            nts.apply(sid, cleared)
            if not rec(nb, nts):
                return False
        return True

    return rec(tmpl.g_board(), TState(tmpl))


# --------------------------------------------------------------- template fill
def can_fill(board, ts, seq, hold, fail=None, node_limit=3000):
    """Yes/no version of fill_template: can `seq` (fully known) finish `ts`?

    fill_template looks for the BEST way and so explores every order; this stops at the
    first way that works and tries pieces bottom-up first, which usually finds it straight
    away. For the "every order of the unseen pieces" checks. `fail` (a set) can be shared
    between calls on the same template: states that failed with the same remaining queue
    fail again, so orders with a common ending are only searched once."""
    from .templates import dependencies
    hard, soft = dependencies(ts.tmpl)
    fail = set() if fail is None else fail
    nodes = [0]

    def rec(b, ts_, i, hold_):
        if not ts_.remaining:
            return True
        key = (b.key(), ts_.remaining, tuple(seq[i:]), hold_)
        if key in fail:
            return False
        nodes[0] += 1
        if nodes[0] > node_limit:
            return False
        opts = []
        for p, used_hold, ni, nh in _choices(seq, i, hold_):
            for sid in ts_.remaining:
                if ts_.tmpl.slots[sid].ptype == p and not hard[sid] & ts_.remaining:
                    opts.append((bool(soft[sid] & ts_.remaining), used_hold, sid, p, ni, nh))
        opts.sort(key=lambda o: (o[0], o[1]))
        for _, _, sid, p, ni, nh in opts:
            pl = movegen(b, p).get(ts_.slot_cells(sid))
            if pl is None:
                continue
            nb = b.copy()
            cleared = nb.place_cells(pl.cells)
            nts = ts_.copy()
            nts.apply(sid, cleared)
            if rec(nb, nts, ni, nh):
                return True
        if nodes[0] <= node_limit:
            fail.add(key)
        return False

    return rec(board, ts, 0, hold)


def fill_template(board, ts, seq, hold, future=None, node_limit=6000):
    """Best way to fill template state `ts` using known pieces `seq` (seq[0] = current).

    `future`: Counter of piece types that may still arrive after `seq` (None = any).
    Returns (complete: bool, viable: bool, steps, filled_count).
    """
    from .templates import dependencies
    memo = {}
    nodes = [0]
    spin_slots = {sid for sid, s in ts.tmpl.slots.items() if s.spin}
    hard, _ = dependencies(ts.tmpl)       # "must wait" pieces, incl. the T-spin going last

    def leaf_viable(ts_, hold_):
        need = Counter(ts_.tmpl.slots[s].ptype for s in ts_.remaining)
        if future is None:
            return True
        have = Counter(future)
        if hold_ not in (None, "?"):
            have[hold_] += 1
        return all(have[p] >= n for p, n in need.items())

    def bottom_up_costs(ts_, sid, cells):
        """(covers, inversions) of placing slot `sid` now while ts_.remaining are open:
        covers     = open slots with a cell directly below this piece (they would have to
                     be tucked in underneath later);
        inversions = open slots whose bottom is lower than this piece's bottom.
        Planned T-spin slots are meant to go in last under their overhang, so skip them."""
        cols_low = {}
        for x, y in cells:
            cols_low[x] = min(y, cols_low.get(x, 99))
        bottom = min(y for _, y in cells)
        covers = inv = 0
        for r in ts_.remaining:
            if r == sid or r in spin_slots:
                continue
            rc = ts_.slot_cells(r)
            if not rc:
                continue
            if any(x in cols_low and y < cols_low[x] for x, y in rc):
                covers += 1
            if min(y for _, y in rc) < bottom:
                inv += 1
        return covers, inv

    def rec(b, ts_, i, hold_):
        # score: (complete, viable, filled, spins, -tucks, -covers, -holds, -inversions, -inputs)
        # Bottom-up first: avoiding soft-drop tucks and pieces placed over still-open
        # slots matters more than avoiding a hold (holding costs almost no time).
        if not ts_.remaining:
            return (1, 1, 0, 0, 0, 0, 0, 0, 0), []
        key = (b.key(), ts_.remaining, i, hold_)
        if key in memo:
            return memo[key]
        nodes[0] += 1
        best = ((0, 1 if leaf_viable(ts_, hold_) else 0, 0, 0, 0, 0, 0, 0, 0), [])
        if nodes[0] > node_limit:
            return best
        rem_types = {ts_.tmpl.slots[s].ptype: None for s in ts_.remaining}
        for p, used_hold, ni, nh in _choices(seq, i, hold_):
            if p not in rem_types:
                continue
            gen = movegen(b, p)
            for sid in ts_.remaining:
                slot = ts_.tmpl.slots[sid]
                if slot.ptype != p or hard[sid] & ts_.remaining:
                    continue
                pl = gen.get(ts_.slot_cells(sid))
                if pl is None:
                    continue
                nb = b.copy()
                cleared = nb.place_cells(pl.cells)
                nts = ts_.copy()
                nts.apply(sid, cleared)
                covers, inv = bottom_up_costs(ts_, sid, ts_.slot_cells(sid))
                sc, steps = rec(nb, nts, ni, nh)
                spin = 1 if (sid in spin_slots and pl.spin == "full") else 0
                tuck = 1 if (core.SOFT in pl.inputs and pl.spin != "full") else 0
                sc = (sc[0], sc[1], sc[2] + 1, sc[3] + spin, sc[4] - tuck, sc[5] - covers,
                      sc[6] - used_hold, sc[7] - inv, sc[8] - len(pl.inputs))
                if sc > best[0]:
                    best = (sc, [Step(used_hold, pl, sid)] + steps)
        memo[key] = best
        return best

    sc, steps = rec(board, ts, 0, hold)
    return bool(sc[0]), bool(sc[1]), steps, sc[2]


# ------------------------------------------------------------ perfect clears
# normalised cell shape (as a bitmask over a 4x4 box) -> piece type, for 4-cell pockets
_POCKET = {}
for _p in core.PIECES:
    for _r in range(4):
        _cs = core.SHAPES[_p][_r]
        _mx, _my = min(c[0] for c in _cs), min(c[1] for c in _cs)
        _POCKET[sum(1 << ((y - _my) * 4 + (x - _mx)) for x, y in _cs)] = _p


def _pocket_type(region, W):
    """Piece type whose shape is exactly this 4-cell region (bitmask), or None."""
    cells = []
    while region:
        low = region & -region
        i = low.bit_length() - 1
        cells.append((i % W, i // W))
        region ^= low
    mx, my = min(c[0] for c in cells), min(c[1] for c in cells)
    if max(c[0] for c in cells) - mx > 3 or max(c[1] for c in cells) - my > 3:
        return None
    return _POCKET.get(sum(1 << ((y - my) * 4 + (x - mx)) for x, y in cells))


def _regions_ok(board, h, types=None):
    """Every connected empty region below row h has a multiple of 4 cells.
    With `types` (the piece types still available): a sealed 4-cell pocket can only take
    the one piece of exactly its shape, so that piece must be available."""
    seen = 0
    full_mask = (1 << (core.W * h)) - 1
    filled = 0
    for y in range(h):
        filled |= board.rows[y] << (core.W * y)
    empty = full_mask & ~filled
    W = core.W
    left_edge = 0
    for y in range(h):
        left_edge |= 1 << (W * y)
    right_edge = left_edge << (W - 1)
    while empty & ~seen:
        rest = empty & ~seen
        frontier = rest & -rest
        region = frontier
        while frontier:
            nb = ((frontier & ~left_edge) >> 1) | ((frontier & ~right_edge) << 1) | (frontier >> W) | (frontier << W)
            nb &= empty & ~region
            region |= nb
            frontier = nb
        seen |= region
        n = bin(region).count("1")
        if n % 4:
            return False
        if n == 4 and types is not None and _pocket_type(region, W) not in types:
            return False
    return True


def _groups_ok(board, h):
    """Like _regions_ok, but valid when lines clear mid-PC.

    Two empty regions can only ever become adjacent if every row between two of
    their cells in one column clears, i.e. through a vertical run of filled cells.
    Regions linked that way form a group; each group must hold a multiple of 4 cells.
    """
    W = core.W
    region_of = {}
    sizes = []
    for y in range(h):
        row = board.rows[y]
        for x in range(W):
            if not (row >> x & 1) and (x, y) not in region_of:
                rid = len(sizes)
                stack = [(x, y)]
                region_of[(x, y)] = rid
                n = 0
                while stack:
                    cx, cy = stack.pop()
                    n += 1
                    for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                        if 0 <= nx < W and 0 <= ny < h and (nx, ny) not in region_of \
                                and not (board.rows[ny] >> nx & 1):
                            region_of[(nx, ny)] = rid
                            stack.append((nx, ny))
                sizes.append(n)
    if all(s % 4 == 0 for s in sizes):
        return True
    parent = list(range(len(sizes)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for x in range(W):
        last = None  # region id of the last empty cell seen below a filled run
        gap = False
        for y in range(h):
            if board.rows[y] >> x & 1:
                gap = last is not None
            else:
                r = region_of[(x, y)]
                if gap and last is not None:
                    parent[find(r)] = find(last)
                last, gap = r, False
    tot = {}
    for i, s in enumerate(sizes):
        root = find(i)
        tot[root] = tot.get(root, 0) + s
    return all(v % 4 == 0 for v in tot.values())


def pc_heights(board, max_h=8):
    """Candidate PC heights (lines) for this board, smallest first."""
    cnt = board.count()
    hs = []
    for h in range(max(board.height(), 1), max_h + 1):
        if (h * core.W - cnt) % 4 == 0 and h * core.W > cnt:
            hs.append(h)
    return hs


def _types(seq, i, hold_):
    """Piece types still available at seq[i:] plus hold (None if any is unknown)."""
    rest = seq[i:]
    if "?" in rest or hold_ == "?":
        return None
    t = set(rest)
    if hold_ is not None:
        t.add(hold_)
    return t


class _Timeout(Exception):
    pass


def pc_solve(board, seq, hold, h, time_limit=1.0, strict=True):
    """Perfect clear within h lines using seq/hold. Returns list of Steps or None.
    Pass 1 only tries straight hard drops (plus every T placement, for T-spins) - most
    PCs need nothing else and it is many times faster. Pass 2 adds tucks and slides."""
    t0 = time.time()
    if _air_ok(board):
        r = _pc_solve(board, seq, hold, h, t0 + time_limit / 2, strict, True)
        if r:
            return r
    r = _pc_solve(board, seq, hold, h, t0 + time_limit, strict, False)
    return r or None


def _pc_solve(board, seq, hold, h, deadline, strict, drops_only):
    """[] on timeout / no PC (falsy), else the steps."""
    fail = set()
    counter = [0]

    def rec(b, i, hold_, hh):
        if b.rows[0] == 0:
            return []
        avail = (len(seq) - i) + (1 if hold_ not in (None, "?") else 0)
        need = (hh * core.W - b.count()) // 4
        if need > avail:
            return None
        key = (b.key(), i, hold_, hh)
        if key in fail:
            return None
        counter[0] += 1
        if counter[0] & 7 == 0 and time.time() > deadline:
            raise _Timeout
        if not (_regions_ok(b, hh, _types(seq, i, hold_)) if strict else _groups_ok(b, hh)):
            fail.add(key)
            return None
        for pl, used_hold, ni, nh in _bottom_up(b, seq, i, hold_, hh, drops_only):
            nb = b.copy()
            cl = nb.place_cells(pl.cells)
            nhh = hh - len(cl)
            if nb.height() > nhh:
                continue
            r = rec(nb, ni, nh, nhh)
            if r is not None:
                return [Step(used_hold, pl)] + r
        fail.add(key)
        return None

    try:
        return rec(board, 0, hold, h) or []
    except _Timeout:
        return []


def _pc_order(pl):
    """Search order for PC placements: T-spins first, then plain hard drops before
    tucks/spins that need a soft drop (those depend on exact timing in the real game),
    then lower placements, then fewer keys."""
    return ({"full": 0, "mini": 1}.get(pl.spin, 2), core.SOFT in pl.inputs,
            max(y for _, y in pl.cells), len(pl.inputs))


def _bottom_up(b, seq, i, hold_, hh, drops_only=False):
    """All placements possible now (current piece, or via hold), lowest and safest first:
    T-spins, then plain hard drops before soft-drop tucks, then by height - so the PC is
    built from the bottom up even if that means holding the current piece.
    drops_only: straight hard drops only (T keeps every placement, for its spins)."""
    cands = []
    for p, used_hold, ni, nh in _choices(seq, i, hold_):
        pls = air_drops(b, p) if drops_only and p != "T" else movegen(b, p)
        for pl in pls.values():
            if max(y for _, y in pl.cells) >= hh:
                continue
            cands.append((_pc_order(pl), used_hold, pl, ni, nh))
    cands.sort(key=lambda c: (c[0][0], c[0][1], c[0][2], c[1], c[0][3]))
    return [(pl, used_hold, ni, nh) for _, used_hold, pl, ni, nh in cands]


# ------------------------------------------------------- straight hard drops
# The part of move generation that happens up in the air (rotate, shift, DAS) is the
# same on every board whose stack is well below the spawn: compute it once per piece on
# an empty board, then a hard drop is just a drop_y per rotation and column.
_AIR_TABLE = {}
_AIR_TOP = 12          # stacks up to this height never reach the pieces' air path


def _air_ok(board):
    """Can straight hard drops be planned from the air table on this board?"""
    return board.height() <= _AIR_TOP and (not SETTINGS["safe"] or _air_ms(board) > 0)


def _air_table(piece, air):
    h = SETTINGS["handling"]
    key = (piece, h.signature(), SETTINGS["safe"], air)
    t = _AIR_TABLE.get(key)
    if t is None:
        g = core.generate(core.Board(), piece, safe=SETTINGS["safe"], costs=_costs(h),
                          finesse=h.optimize == "FINESSE", use_180=h.use_180, air_ms=air,
                          ground_das=h.arr_ms <= 0)
        # on an empty floor, a placement whose cheapest keys need no soft drop was
        # reached entirely in the air: the same keys hard drop it on any low stack
        t = [(pl.rot, pl.x, pl.inputs, pl.cost) for pl in g.values() if core.SOFT not in pl.inputs]
        _AIR_TABLE[key] = t
    return t


def air_drops(board, piece):
    """{cells: Placement} of every straight hard drop on `board` (needs _air_ok)."""
    top = board.height()
    out = {}
    for rot, x, inputs, cost in _air_table(piece, _air_ms(board)):
        y = board.drop_y(piece, rot, x, top - core._ROWS[(piece, rot)][2])
        pl = core.Placement(piece, rot, x, y, inputs, None, cost)
        if pl.cells not in out:
            out[pl.cells] = pl
    return out


def tucks(steps):
    """Number of non-spin placements in `steps` that need a soft drop (riskier)."""
    return sum(1 for st in steps if core.SOFT in st.pl.inputs and st.pl.spin != "full")


def pc_solutions(board, seq, hold, h, time_limit=0.6, want=6, strict=False):
    """Several perfect clears within h lines that END DIFFERENTLY (different pieces
    left unused / in hold), so the caller can choose by what comes next.
    Straight hard drops first (fast); tucks only if that finds nothing (the caller
    prefers endings without tucks anyway)."""
    t0 = time.time()
    found, ends = [], set()
    if _air_ok(board):
        _pc_solutions(board, seq, hold, h, t0 + time_limit / 2, want, strict, True, found, ends)
    if not found:
        _pc_solutions(board, seq, hold, h, t0 + time_limit, want, strict, False, found, ends)
    return found


def _pc_solutions(board, seq, hold, h, deadline, want, strict, drops_only, found, ends):
    fail = set()
    counter = [0]

    def rec(b, i, hold_, hh, path):
        """True if at least one new solution was recorded below this state."""
        if b.rows[0] == 0:
            end = (i, hold_)
            if end in ends:
                return False
            ends.add(end)
            found.append(list(path))
            return True
        avail = (len(seq) - i) + (1 if hold_ not in (None, "?") else 0)
        if (hh * core.W - b.count()) // 4 > avail:
            return False
        key = (b.key(), i, hold_, hh)
        if key in fail:
            return False
        counter[0] += 1
        if counter[0] & 7 == 0 and time.time() > deadline:
            raise _Timeout
        if not (_regions_ok(b, hh, _types(seq, i, hold_)) if strict else _groups_ok(b, hh)):
            fail.add(key)
            return False
        any_new = False
        for pl, used_hold, ni, nh in _bottom_up(b, seq, i, hold_, hh, drops_only):
            nb = b.copy()
            cl = nb.place_cells(pl.cells)
            nhh = hh - len(cl)
            if nb.height() > nhh:
                continue
            path.append(Step(used_hold, pl))
            if rec(nb, ni, nh, nhh, path):
                any_new = True
            path.pop()
            if len(found) >= want:
                return True
        if not any_new:
            fail.add(key)
        return any_new

    try:
        rec(board, 0, hold, h, [])
    except _Timeout:
        pass


def find_pc(board, seq, hold, max_h=6, time_limit=1.5):
    """Try PC heights in order; strict region pruning first, then relaxed."""
    t0 = time.time()
    for h in pc_heights(board, max_h):
        for strict in (True, False):
            left = time_limit - (time.time() - t0)
            if left <= 0:
                return None
            r = pc_solve(board, seq, hold, h, min(left, time_limit / 3) if strict else left, strict)
            if r:
                return r
    return None


# ------------------------------------------------------------ heuristic play
def holes_covered(board, hs):
    """(holes, covered): empty cells under a column's top, and how many blocks sit on
    top of each one. Row by row from the top, with a mask of the columns already roofed."""
    rows = board.rows
    holes = covered = 0
    roofed = 0
    for y in range(max(hs) - 1, -1, -1):
        gaps = roofed & ~rows[y]
        while gaps:
            low = gaps & -gaps
            holes += 1
            covered += hs[low.bit_length() - 1] - y
            gaps ^= low
        roofed |= rows[y]
    return holes, covered


def evaluate(board, lines, spin):
    hs = board.col_heights()
    holes, covered = holes_covered(board, hs)
    maxh = max(hs)
    agg = sum(hs)
    # deepest well is fine (one column for I / T-spins), others penalised
    bump = well_pen = deepest = 0
    for x in range(core.W):
        right = hs[x + 1] if x < 9 else 99
        if x < 9:
            bump += abs(hs[x] - right)
        w = min(hs[x - 1] if x > 0 else 99, right) - hs[x]
        if w > 0:
            well_pen += w
            deepest = max(deepest, w)
    well_pen -= deepest
    score = -4.0 * holes - 0.6 * covered - 0.35 * bump - 0.25 * agg - 0.8 * well_pen
    score -= 2.0 * max(0, maxh - 10) ** 1.5
    if board.rows[0] == 0 and lines:
        score += 60  # perfect clear
    if spin == "full":
        score += {1: 8, 2: 22, 3: 35}.get(lines, 0)
    elif lines == 4:
        score += 18
    elif lines:
        score += [0, -3, -2, 1][lines] if maxh < 10 else 3 * lines
    return score


def heuristic_move(board, seq, hold, lookahead=True, pc_h=None):
    """Best placement by the stacking heuristic. pc_h: only placements that keep a pc_h-line
    PC possible (field within pc_h rows, no holes, empty regions a multiple of 4 cells) -
    if there are any - so the solver can finish one when enough pieces are in view."""
    best = None
    for p, used_hold, ni, nh in _choices(seq, 0, hold) or [(seq[0], False, 1, hold)]:
        for pl in movegen(board, p).values():
            nb = board.copy()
            lines = len(nb.place_cells(pl.cells))
            if pc_h is not None and (nb.height() > pc_h - lines or holes_covered(nb, nb.col_heights())[0]
                                     or not _groups_ok(nb, pc_h - lines)):
                continue
            s = evaluate(nb, lines, pl.spin)
            if lookahead and ni < len(seq):
                # add the best board quality reachable with the next piece (straight drops
                # only: scoring a board needs no key paths, and this is 50x cheaper)
                s += max((evaluate(_after_cells(nb, c), 0, None) for c in core.drop_cells(nb, seq[ni])),
                         default=0)
            if best is None or s > best[0]:
                best = (s, Step(used_hold, pl))
    if best is None and pc_h is not None:
        return heuristic_move(board, seq, hold, lookahead)
    return best[1] if best else None


def _after_cells(b, cells):
    nb = b.copy()
    nb.place_cells(cells)
    return nb
