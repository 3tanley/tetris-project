"""Game rules for a TETR.IO-style field: pieces, SRS+ rotation (incl. 180 kicks),
board bitboards, line clears and a BFS move generator that returns key sequences.

Coordinates: x = column 0..9 (left->right), y = row 0.. (bottom->top, y-up).
"""
import heapq

W = 10
H = 40                      # rows kept in the model (TETR.IO buffer is 40 tall)
FULL = (1 << W) - 1
PIECES = "IJLOSTZ"

# Cell offsets for rotation 0 (spawn), relative to the piece origin.
# Origin = SRS rotation centre for JLSTZ, box cell (1,1) for I, bottom-left for O.
_SPAWN = {
    "T": [(-1, 0), (0, 0), (1, 0), (0, 1)],
    "J": [(-1, 1), (-1, 0), (0, 0), (1, 0)],
    "L": [(1, 1), (-1, 0), (0, 0), (1, 0)],
    "S": [(-1, 0), (0, 0), (0, 1), (1, 1)],
    "Z": [(-1, 1), (0, 1), (0, 0), (1, 0)],
    "I": [(-1, 0), (0, 0), (1, 0), (2, 0)],
    "O": [(0, 0), (1, 0), (0, 1), (1, 1)],
}


def _rot_cw(cells, piece):
    if piece == "O":
        return list(cells)
    if piece == "I":   # I rotates about (0.5, -0.5)
        return [(y + 1, -x) for x, y in cells]
    return [(y, -x) for x, y in cells]


SHAPES = {}
for _p, _c in _SPAWN.items():
    _r = [_c]
    for _ in range(3):
        _r.append(_rot_cw(_r[-1], _p))
    SHAPES[_p] = [tuple(sorted(s)) for s in _r]

# TETR.IO SRS+ kick tables, converted to y-up. (0,0) is always tested first.
# CW/CCW kicks are mirror images (r0->r1 vs the mirrored rotation, x negated), so a
# mirrored setup has the mirrored spin (tests check this). 180 kicks: TETR.IO's own table
# (tetrio.wiki.gg "180 kicks"); I-piece 180s only use their first kick.
_K = {
    (0, 1): [(-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (1, 0): [(1, 0), (1, -1), (0, 2), (1, 2)],
    (1, 2): [(1, 0), (1, -1), (0, 2), (1, 2)],
    (2, 1): [(-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (2, 3): [(1, 0), (1, 1), (0, -2), (1, -2)],
    (3, 2): [(-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (3, 0): [(-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (0, 3): [(1, 0), (1, 1), (0, -2), (1, -2)],
    (0, 2): [(0, 1), (1, 1), (-1, 1), (1, 0), (-1, 0)],
    (1, 3): [(1, 0), (1, 2), (1, 1), (0, 2), (0, 1)],
    (2, 0): [(0, -1), (-1, -1), (1, -1), (-1, 0), (1, 0)],
    (3, 1): [(-1, 0), (-1, 2), (-1, 1), (0, 2), (0, 1)],
}
_IK = {
    (0, 1): [(1, 0), (-2, 0), (-2, -1), (1, 2)],
    (1, 0): [(-1, 0), (2, 0), (-1, -2), (2, 1)],
    (1, 2): [(-1, 0), (2, 0), (-1, 2), (2, -1)],
    (2, 1): [(-2, 0), (1, 0), (-2, 1), (1, -2)],
    (2, 3): [(2, 0), (-1, 0), (2, 1), (-1, -2)],
    (3, 2): [(1, 0), (-2, 0), (1, 2), (-2, -1)],
    (3, 0): [(1, 0), (-2, 0), (1, -2), (-2, 1)],
    (0, 3): [(-1, 0), (2, 0), (2, -1), (-1, 2)],
    (0, 2): [(0, 1)],
    (1, 3): [(1, 0)],
    (2, 0): [(0, -1)],
    (3, 1): [(-1, 0)],
}


def kicks(piece, r0, r1):
    if piece == "O":
        return [(0, 0)]
    return [(0, 0)] + (_IK if piece == "I" else _K)[(r0, r1)]


SPAWN_X, SPAWN_Y = 4, 21

# Per (piece, rot): list of (dy, rowmask-at-x=0), plus min/max dx for bounds.
_ROWS = {}
for _p in PIECES:
    for _r in range(4):
        cells = SHAPES[_p][_r]
        xs = [c[0] for c in cells]
        rows = {}
        for x, y in cells:
            rows[y] = rows.get(y, 0) | (1 << (x - min(xs)))
        _ROWS[(_p, _r)] = (min(xs), max(xs), min(c[1] for c in cells), sorted(rows.items()))


_CELLS = {}


def cells_of(piece, rot, x, y):
    k = (piece, rot, x, y)
    c = _CELLS.get(k)
    if c is None:
        c = _CELLS[k] = tuple(sorted((x + cx, y + cy) for cx, cy in SHAPES[piece][rot]))
    return c


class Board:
    """Rows are ints; bit x set = column x filled. rows[0] is the bottom."""

    __slots__ = ("rows",)

    def __init__(self, rows=None):
        r = list(rows) if rows else []
        self.rows = (r + [0] * H)[:H]

    @classmethod
    def from_strings(cls, lines):
        """lines top->bottom, '.' or ' ' = empty, anything else filled."""
        rows = []
        for line in reversed(lines):
            m = 0
            for x, ch in enumerate(line[:W]):
                if ch not in ". _":
                    m |= 1 << x
            rows.append(m)
        return cls(rows)

    def copy(self):
        b = Board.__new__(Board)
        b.rows = self.rows[:]
        return b

    def key(self):
        return tuple(self.rows[: self.height()])

    def filled(self, x, y):
        if x < 0 or x >= W or y < 0:
            return True
        if y >= H:
            return False
        return bool(self.rows[y] >> x & 1)

    def height(self):
        for y in range(H - 1, -1, -1):
            if self.rows[y]:
                return y + 1
        return 0

    def col_heights(self):
        hs = [0] * W
        rows = self.rows
        left = FULL                    # columns whose top block hasn't been seen yet
        for y in range(self.height() - 1, -1, -1):
            r = rows[y] & left
            if r:
                left ^= r
                while r:
                    low = r & -r
                    hs[low.bit_length() - 1] = y + 1
                    r ^= low
                if not left:
                    break
        return hs

    def count(self):
        return sum(bin(r).count("1") for r in self.rows)

    def collides(self, piece, rot, x, y):
        lo, hi, miny, rows = _ROWS[(piece, rot)]
        if x + lo < 0 or x + hi >= W or y + miny < 0:
            return True
        sx = x + lo
        for dy, m in rows:
            yy = y + dy
            if yy < H and self.rows[yy] & (m << sx):
                return True
        return False

    def place(self, piece, rot, x, y):
        """Lock the piece and clear lines. Returns list of cleared row indices."""
        lo, hi, miny, rows = _ROWS[(piece, rot)]
        sx = x + lo
        for dy, m in rows:
            self.rows[y + dy] |= m << sx
        return self.clear_lines()

    def place_cells(self, cells):
        for x, y in cells:
            self.rows[y] |= 1 << x
        return self.clear_lines()

    def clear_lines(self):
        cleared = [y for y in range(H) if self.rows[y] == FULL]
        if cleared:
            self.rows = [r for r in self.rows if r != FULL]
            self.rows += [0] * (H - len(self.rows))
        return cleared

    def drop_y(self, piece, rot, x, y):
        while not self.collides(piece, rot, x, y - 1):
            y -= 1
        return y

    def __eq__(self, other):
        return isinstance(other, Board) and self.rows == other.rows

    def __hash__(self):
        return hash(self.key())

    def __str__(self):
        h = max(self.height(), 1)
        return "\n".join(
            "".join("#" if self.rows[y] >> x & 1 else "." for x in range(W)) for y in range(h - 1, -1, -1)
        )


# ----------------------------------------------------------------- T-spin rules
def tspin_kind(board, rot, x, y, last_was_rot, kick_idx):
    """Return 'full', 'mini' or None for a T locked at (rot,x,y) on `board` (before lock)."""
    if not last_was_rot:
        return None
    corners = [(x - 1, y + 1), (x + 1, y + 1), (x + 1, y - 1), (x - 1, y - 1)]  # TL TR BR BL
    filled = [board.filled(cx, cy) for cx, cy in corners]
    if sum(filled) < 3:
        return None
    front = {0: (0, 1), 1: (1, 2), 2: (2, 3), 3: (3, 0)}[rot]
    if (filled[front[0]] and filled[front[1]]) or kick_idx == 4:
        return "full"
    return "mini"


# ------------------------------------------------------------------- move gen
# Inputs understood by the controller. DL/DR = hold the direction past DAS
# (the piece slides until it hits the wall or a block).
LEFT, RIGHT, CW, CCW, R180, SOFT, HARD, HOLD = "L", "R", "CW", "CCW", "180", "SD", "HD", "HOLD"
DAS_LEFT, DAS_RIGHT = "DL", "DR"
MIRROR_CCW = ("Z", "J")        # prefer CCW on ties (mirrors of S and L)
GROUND_SLIDE_MS = 0.01
SPAWN_FALL_RPS = 1000.0        # from ~17 rows per frame a new piece is on the stack before any key

# (key presses, milliseconds) per action; replaced by Handling.action_cost.
DEFAULT_COSTS = {a: (1, 20.0) for a in (LEFT, RIGHT, CW, CCW, R180, HOLD, HARD)}
DEFAULT_COSTS.update({SOFT: (1, 30.0), DAS_LEFT: (1, 130.0), DAS_RIGHT: (1, 130.0)})


class Placement:
    __slots__ = ("piece", "rot", "x", "y", "cells", "inputs", "spin", "cost")

    def __init__(self, piece, rot, x, y, inputs, spin, cost=(0, 0.0)):
        self.piece, self.rot, self.x, self.y = piece, rot, x, y
        self.cells = cells_of(piece, rot, x, y)
        self.inputs = inputs
        self.spin = spin
        self.cost = cost

    def __repr__(self):
        return f"<{self.piece} r{self.rot} ({self.x},{self.y}) {self.spin or ''} {' '.join(self.inputs)}>"


def slide(board, piece, r, x, y, dx):
    while not board.collides(piece, r, x + dx, y):
        x += dx
    return x


def generate(board, piece, spawn=(SPAWN_X, SPAWN_Y), use_180=True, safe=False,
             costs=None, finesse=True, start=None, air_ms=0.0, ground_das=True, gravity_rps=0.0):
    """All lockable placements reachable by key presses. Returns {cells: Placement}.

    Cheapest key sequence per placement (Dijkstra). finesse=True ranks by number of
    presses then time (DAS-to-wall counts as one press, as in finesse guides);
    finesse=False ranks by time. For each cell set a T-spin beats a non-spin.
    safe=True: high-gravity mode, a soft drop follows every input so the result is
    the same at any gravity. start=(x, y, rot) plans from a piece already in play.
    air_ms (with safe=True): for this long after spawn the piece is still well above
    the stack, so ordinary moves/rotations are allowed up there before it is dropped
    (a lower-than-expected piece is still above every block, so the result is the same).
    gravity_rps (with safe=True): the measured gravity. After an input the piece only gets
    an explicit soft drop if gravity can't pull it down that far (with a 2x margin) in the
    time that input takes - at 20G the extra soft-drop presses are pointless key presses.
    """
    costs = costs or DEFAULT_COSTS
    # Local collision/drop with an early out above the stack: rows >= top are empty, so
    # a piece up there only has to stay inside the walls and falls straight to `top`.
    top = board.height()
    brows = board.rows
    tab = [_ROWS[(piece, r)] for r in range(4)]

    def coll(r, x, y):
        lo, hi, miny, prs = tab[r]
        if x + lo < 0 or x + hi >= W or y + miny < 0:
            return True
        if y + miny >= top:
            return False
        sx = x + lo
        for dy, m in prs:
            yy = y + dy
            if yy < H and brows[yy] & (m << sx):
                return True
        return False

    def drop(r, x, y):
        low = top - tab[r][2]
        if y > low:
            y = low
        while not coll(r, x, y - 1):
            y -= 1
        return y

    def sld(r, x, y, dx):
        while not coll(r, x + dx, y):
            x += dx
        return x

    rank = (lambda c: c) if finesse else (lambda c: (c[1], c[0]))
    sd_cost = costs[SOFT]

    if start is None:
        sx, sy = spawn
        if coll(0, sx, sy):
            sy += 1
            if coll(0, sx, sy):
                return {}
        start = (sx, sy, 0)
    x0, y0, r0 = start
    first_keys, first_cost = [], (0, 0.0)
    use_air = safe and air_ms > 0 and y0 + min(c[1] for c in SHAPES[piece][r0]) > top
    if safe and not use_air:
        dy = drop(r0, x0, y0)
        if dy != y0 and gravity_rps < SPAWN_FALL_RPS:
            first_keys, first_cost = [SOFT], sd_cost
        start = (x0, dy, r0)
    air = {start} if use_air else set()        # states still up in the air (no auto-drop)

    # When two rotations are equally cheap, mirrored pieces use mirrored rotations
    # (tetrio.wiki.gg/wiki/Spins: "all setups can be mirrored, but so must the piece"):
    # S, L (and T, I) try CW first, their mirrors Z and J try CCW first.
    rot_moves = ([(CCW, 3), (CW, 1)] if piece in MIRROR_CCW else [(CW, 1), (CCW, 3)]) \
        + ([(R180, 2)] if use_180 else [])
    # info[state] = (cost, parent, keys, last_was_rotation, kick_idx)
    info = {start: (first_cost, None, first_keys, False, -1)}
    heap = [(rank(first_cost), 0, start)]
    done = set()
    n = 0

    def push(ns, c, parent, keys, isrot, ki):
        nonlocal n
        old = info.get(ns)
        if old is None or rank(c) < rank(old[0]):
            info[ns] = (c, parent, keys, isrot, ki)
            n += 1
            heapq.heappush(heap, (rank(c), n, ns))

    while heap:
        _, _, s = heapq.heappop(heap)
        if s in done:
            continue
        done.add(s)
        cost = info[s][0]
        x, y, r = s
        moves = []
        for mv, dx in ((LEFT, -1), (RIGHT, 1)):
            if not coll(r, x + dx, y):
                moves.append((mv, x + dx, y, r, False, -1))
        for mv, dx in ((DAS_LEFT, -1), (DAS_RIGHT, 1)):
            if safe and s not in air:
                # on the ground: the key moves one cell at once, then auto-shift slides
                # after the DAS wait. Gravity can act in between, so only use DAS when
                # that first step keeps the piece supported (same result at any gravity;
                # with ARR > 0 the slide itself is gradual, so no ground DAS at all)
                if ground_das is False or coll(r, x + dx, y) \
                        or not coll(r, x + dx, y - 1):
                    continue
                nx = sld(r, x + dx, y, dx)
                if abs(nx - x) >= 2:
                    moves.append((mv, nx, y, r, False, -1))
                continue
            nx = sld(r, x, y, dx)
            if abs(nx - x) >= 2:
                moves.append((mv, nx, y, r, False, -1))
        if piece != "O":
            for mv, d in rot_moves:
                nr = (r + d) % 4
                for i, (kx, ky) in enumerate(kicks(piece, r, nr)):
                    if not coll(nr, x + kx, y + ky):
                        moves.append((mv, x + kx, y + ky, nr, True, i))
                        break
        in_air = s in air
        if not safe or in_air:
            dy = drop(r, x, y)
            if dy != y:
                moves.append((SOFT, x, dy, r, False, -1))
        grounded = coll(r, x, y - 1)
        for mv, nx, ny, nr, isrot, ki in moves:
            c = (cost[0] + costs[mv][0], cost[1] + costs[mv][1])
            if grounded and mv in (LEFT, RIGHT, DAS_LEFT, DAS_RIGHT):
                # sideways moves belong in the air: move first, then soft drop and kick in
                # (a hair of cost so an equally cheap air path always wins)
                c = (c[0], c[1] + GROUND_SLIDE_MS)
            keys = [mv]
            if in_air and mv != SOFT:
                # still in the air: allowed while the time budget lasts and the piece
                # stays above every block
                if c[1] > air_ms or ny + min(cc[1] for cc in SHAPES[piece][nr]) <= top:
                    continue
                if (nx, ny, nr) not in info or rank(c) < rank(info[(nx, ny, nr)][0]):
                    air.add((nx, ny, nr))
                push((nx, ny, nr), c, s, keys, isrot, ki)
                continue
            if safe and mv != SOFT:
                dy = drop(nr, nx, ny)
                if dy != ny:
                    if ny - dy > gravity_rps * costs[mv][1] / 2000.0:
                        keys = [mv, SOFT]
                        c = (c[0] + sd_cost[0], c[1] + sd_cost[1])
                    ny, isrot = dy, False
            push((nx, ny, nr), c, s, keys, isrot, ki)

    def path_to(st):
        out = []
        while st is not None:
            _, p, k, _, _ = info[st]
            out = k + out
            st = p
        return out

    # Best placement per cell set: a T-spin beats a mini beats none, then the cheaper
    # keys (first found wins ties). Placements are only built for the winners.
    best = {}
    spin_rank = {"full": 0, "mini": 1, None: 2}

    def offer(r, x, y, spin, fc, s, extra):
        cells = cells_of(piece, r, x, y)
        key = (spin_rank[spin], rank(fc))
        old = best.get(cells)
        if old is None or key < old[0]:
            best[cells] = (key, r, x, y, spin, fc, s, extra)

    hd = costs[HARD]
    for s, (c, _, _, isrot, ki) in info.items():
        x, y, r = s
        fc = (c[0] + hd[0], c[1] + hd[1])
        if coll(r, x, y - 1):
            spin = tspin_kind(board, r, x, y, isrot, ki) if piece == "T" else None
            offer(r, x, y, spin, fc, s, [HARD])
        else:
            offer(r, x, drop(r, x, y), None, fc, s, [HARD])
    if piece == "T":  # rotations into resting states first reached another way
        for s, (c, _, _, _, _) in list(info.items()):
            x, y, r = s
            for mv, d in rot_moves:
                nr = (r + d) % 4
                for i, (kx, ky) in enumerate(kicks(piece, r, nr)):
                    nx, ny = x + kx, y + ky
                    if not coll(nr, nx, ny):
                        if coll(nr, nx, ny - 1):
                            spin = tspin_kind(board, nr, nx, ny, True, i)
                            if spin:
                                fc = (c[0] + costs[mv][0] + hd[0], c[1] + costs[mv][1] + hd[1])
                                offer(nr, nx, ny, spin, fc, s, [mv, HARD])
                        break
    result = {}
    for cells, (_, r, x, y, spin, fc, s, extra) in best.items():
        result[cells] = Placement(piece, r, x, y, path_to(s) + extra, spin, fc)
    return result


def drop_cells(board, piece):
    """Cell sets of every straight hard drop (any rotation, any column) - no key paths,
    no tucks or spins. Cheap enough for scoring the next piece in a heuristic lookahead."""
    top = board.height()
    out = {}
    for r in range(4):
        lo, hi, miny, _ = _ROWS[(piece, r)]
        for x in range(-lo, W - hi):
            y = board.drop_y(piece, r, x, top - miny)
            cells = cells_of(piece, r, x, y)
            if cells not in out and all(cy < H for _, cy in cells):
                out[cells] = True
    return list(out)


def _better(a, b, rank=lambda c: c):
    ra = {"full": 0, "mini": 1, None: 2}[a.spin]
    rb = {"full": 0, "mini": 1, None: 2}[b.spin]
    if ra != rb:
        return ra < rb
    return rank(a.cost) < rank(b.cost)


def walk(board, piece, keys, start=None, gravity=False):
    """States (x, y, rot) the piece passes through when `keys` are applied
    (gravity=True: the piece is on the ground after every key, as at 20G).
    First entry is the start (spawn by default); HARD/HOLD are ignored."""
    if start is None:
        x, y, r = SPAWN_X, SPAWN_Y, 0
        if board.collides(piece, r, x, y):
            y += 1
    else:
        x, y, r = start
    out = [(x, y, r)]
    for k in keys:
        if k in (LEFT, RIGHT):
            nx = x + (-1 if k == LEFT else 1)
            if not board.collides(piece, r, nx, y):
                x = nx
        elif k in (DAS_LEFT, DAS_RIGHT):
            d = -1 if k == DAS_LEFT else 1
            if gravity and not board.collides(piece, r, x + d, y):
                x += d
                y = board.drop_y(piece, r, x, y)
            x = slide(board, piece, r, x, y, d)
        elif k in (CW, CCW, R180):
            nr = (r + {CW: 1, CCW: 3, R180: 2}[k]) % 4
            for kx, ky in kicks(piece, r, nr):
                if not board.collides(piece, nr, x + kx, y + ky):
                    x, y, r = x + kx, y + ky, nr
                    break
        elif k == SOFT:
            y = board.drop_y(piece, r, x, y)
        else:
            continue
        if gravity:
            y = board.drop_y(piece, r, x, y)
        out.append((x, y, r))
    return out


def identify(piece, cells, prefer_rot=None):
    """(x, y, rot) states whose cells equal `cells`, preferred rotation first."""
    cells = tuple(sorted(cells))
    out = []
    for r in range(4):
        sh = SHAPES[piece][r]
        x = cells[0][0] - sh[0][0]
        y = cells[0][1] - sh[0][1]
        if cells_of(piece, r, x, y) == cells:
            out.append((x, y, r))
    out.sort(key=lambda s: s[2] != prefer_rot)
    return out


def lock(board, pl):
    """Return (new_board, lines_cleared) after locking placement `pl`."""
    b = board.copy()
    n = len(b.place_cells(pl.cells))
    return b, n
