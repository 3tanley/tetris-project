"""Screen reading for TETR.IO: find the board at any size/aspect ratio and read
the field, the NEXT queue and the HOLD box.

Board detection uses the white frame drawn around the matrix: two vertical white
lines of equal length (exactly 20 rows tall) joined by a white bottom line, 10
columns apart. Hold and next previews use the same cell size as the board.
"""
import numpy as np

from . import core

# Default TETR.IO skin colours (sampled from a screenshot), RGB.
PALETTE = {
    "T": (152, 68, 150),
    "O": (173, 152, 67),
    "Z": (160, 61, 62),
    "L": (178, 112, 68),
    "J": (79, 66, 161),
    "S": (141, 178, 73),
    "I": (93, 179, 136),
}
_PAL_NAMES = list(PALETTE)
_PAL = np.array([PALETTE[k] for k in _PAL_NAMES], dtype=float)

# Spawn-orientation patterns as drawn in the previews: (w, h, rows top->bottom)
_PREVIEW = {
    "I": ["XXXX"],
    "O": ["XX", "XX"],
    "T": [".X.", "XXX"],
    "S": [".XX", "XX."],
    "Z": ["XX.", ".XX"],
    "J": ["X..", "XXX"],
    "L": ["..X", "XXX"],
}


def classify_color(rgb):
    """Nearest palette piece for a mean colour, or None for grey/black/white."""
    rgb = np.asarray(rgb, dtype=float)
    if rgb.max() - rgb.min() < 30:      # unsaturated: empty, garbage, greyed hold
        return None
    d = ((_PAL - rgb) ** 2).sum(axis=1)
    return _PAL_NAMES[int(d.argmin())]


class Geometry:
    """Board location in image pixels: matrix origin (left, top) and cell size."""

    def __init__(self, left, top, cw, ch):
        self.left, self.top, self.cw, self.ch = float(left), float(top), float(cw), float(ch)

    def __repr__(self):
        return f"Geometry(left={self.left:.1f}, top={self.top:.1f}, cell={self.cw:.2f}x{self.ch:.2f})"

    def cell_center(self, x, y):
        """Pixel centre of board cell (x, y), y = 0 bottom row; y >= 20 is above the matrix."""
        return self.left + (x + 0.5) * self.cw, self.top + (19.5 - y) * self.ch

    def scaled(self, s, dx=0, dy=0):
        return Geometry(self.left * s + dx, self.top * s + dy, self.cw * s, self.ch * s)

    def bounds(self):
        """Pixel box covering hold, matrix (+3 rows above) and next queue."""
        return (int(self.left - 6.0 * self.cw), int(self.top - 3.5 * self.ch),
                int(self.left + 16.8 * self.cw), int(self.top + 20.6 * self.ch))

    def hold_box(self):
        return (self.left - 4.9 * self.cw, self.top + 0.85 * self.ch,
                self.left - 0.25 * self.cw, self.top + 3.7 * self.ch)

    def next_box(self):
        return (self.left + 10.95 * self.cw, self.top + 0.85 * self.ch,
                self.left + 15.7 * self.cw, self.top + 15.45 * self.ch)


# ------------------------------------------------------------------ locating
def _longest_runs(mask):
    """For each column: (length, start, end) of its longest run of True."""
    h, w = mask.shape
    pad = np.zeros((1, w), dtype=bool)
    m = np.vstack([pad, mask, pad]).astype(np.int8)
    d = np.diff(m, axis=0)
    out = np.zeros((w, 3), dtype=int)
    starts_y, starts_x = np.nonzero(d == 1)
    ends_y, ends_x = np.nonzero(d == -1)
    # starts and ends come out sorted by row; group per column
    order_s = np.lexsort((starts_y, starts_x))
    order_e = np.lexsort((ends_y, ends_x))
    sx, sy = starts_x[order_s], starts_y[order_s]
    ex, ey = ends_x[order_e], ends_y[order_e]
    lengths = ey - sy
    for i in range(len(sx)):
        x = sx[i]
        if lengths[i] > out[x, 0]:
            out[x] = (lengths[i], sy[i], ey[i])
    return out


def locate(img):
    """Find the TETR.IO matrix in an RGB image. Returns Geometry or None."""
    h, w, _ = img.shape
    white = img.min(axis=2) >= 200
    runs = _longest_runs(white)
    min_len = max(40, int(h * 0.15))
    cols = [x for x in range(w) if runs[x, 0] >= min_len]
    # group adjacent columns into lines
    lines = []
    for x in cols:
        if lines and x - lines[-1][-1] <= 2 and abs(runs[x, 1] - runs[lines[-1][-1], 1]) <= 4:
            lines[-1].append(x)
        else:
            lines.append([x])
    segs = []
    for g in lines:
        best = max(g, key=lambda c: runs[c, 0])
        segs.append((min(g), max(g), runs[best, 1], runs[best, 2]))
    best = None
    for a in segs:
        for b in segs:
            if b[0] <= a[1]:
                continue
            la, lb = a[3] - a[2], b[3] - b[2]
            if abs(a[2] - b[2]) > max(4, 0.01 * la) or abs(la - lb) > max(6, 0.02 * la):
                continue
            inner_w = b[0] - a[1] - 1
            ratio = inner_w / la
            if not 0.45 < ratio < 0.56:
                continue
            # bottom white line joining them
            y = min(a[3], b[3]) - 1
            band = white[max(0, y - 3): y + 2, a[1]: b[0]]
            if band.any(axis=0).mean() < 0.9:
                continue
            err = abs(ratio - 0.5)
            if best is None or err < best[0]:
                best = (err, a, b)
    if best is None:
        return _locate_left_only(white, segs)
    _, a, b = best
    left, right = a[1] + 1, b[0]
    top, bottom = max(a[2], b[2]), min(a[3], b[3])
    # the bottom frame line occupies the last few pixels of the vertical run
    bl = bottom - 1
    while bl > top and white[bl, (left + right) // 2]:
        bl -= 1
    bottom = bl + 1
    return Geometry(left, top, (right - left) / 10.0, (bottom - top) / 20.0)


def _locate_left_only(white, segs):
    """Fallback when the right border is not white (it glows during some effects):
    a vertical line 20 rows tall whose bottom joins a white line ~10 cells long."""
    best = None
    for a in segs:
        la = a[3] - a[2]
        y = a[3] - 1
        row = white[max(0, y - 3): y + 2, a[1] + 1:]
        if row.size == 0:
            continue
        run = 0
        for v in row.any(axis=0):
            if not v:
                break
            run += 1
        ratio = run / la
        if 0.45 < ratio < 0.56 and (best is None or abs(ratio - 0.5) < best[0]):
            best = (abs(ratio - 0.5), a, run)
    if best is None:
        return None
    _, a, run = best
    left = a[1] + 1
    top, bottom = a[2], a[3]
    bl = bottom - 1
    while bl > top and white[bl, left + run // 2]:
        bl -= 1
    bottom = bl + 1
    ch = (bottom - top) / 20.0
    return Geometry(left, top, ch, ch)   # TETR.IO cells are square


# ------------------------------------------------------------------- reading
def _patch(img, cx, cy, r):
    h, w, _ = img.shape
    x0, x1 = int(max(0, cx - r)), int(min(w, cx + r + 1))
    y0, y1 = int(max(0, cy - r)), int(min(h, cy + r + 1))
    if x1 <= x0 or y1 <= y0:
        return np.zeros(3)
    return img[y0:y1, x0:x1].reshape(-1, 3).mean(axis=0)


def cell_color(img, geo, x, y):
    r = max(1, int(min(geo.cw, geo.ch) * 0.18))
    cx, cy = geo.cell_center(x, y)
    return _patch(img, cx, cy, r)


def piece_pixels(pix):
    """Mask of pixels that belong to a drawn piece: saturated colour, or the neutral
    grey of a locked hold piece. Excludes black, white and the bluish background."""
    mx, mn = pix.max(axis=-1), pix.min(axis=-1)
    saturated = (mx >= 50) & (mx - mn >= 30)
    grey = (mx >= 25) & (mx - mn < 12) & (mx < 90)
    return saturated | grey


def is_filled(rgb):
    return rgb.max() >= 45


_GRID9 = [(fx, fy) for fy in (0.2, 0.5, 0.8) for fx in (0.2, 0.5, 0.8)]


def cell_state(img, geo, x, y):
    """'block', 'empty' or 'unknown' for board cell (x, y), plus its mean colour.

    A real block is coloured across the whole cell with one colour (TETR.IO's bevel
    varies little). Text drawn over the board ("ALL CLEAR", combo numbers) covers
    cells only partly or with gradients, so it reads as 'unknown', never as a block.
    """
    centre = cell_color(img, geo, x, y)
    if not is_filled(centre):
        return "empty", centre
    px0 = geo.left + x * geo.cw
    py0 = geo.top + (19 - y) * geo.ch
    r = max(1, int(min(geo.cw, geo.ch) * 0.05))
    pts = [_patch(img, px0 + fx * geo.cw, py0 + fy * geo.ch, r) for fx, fy in _GRID9]
    lit = [c for c in pts if c.max() >= 45]
    if len(lit) >= 8 and np.ptp(np.array(lit), axis=0).max() <= 60:
        return "block", centre
    return "unknown", centre


def read_board_ex(img, geo, rows=20):
    """(board, letters, unknown_cells). Unknown cells are left empty in `board`."""
    b = core.Board()
    letters, unknown = {}, set()
    for y in range(rows):
        m = 0
        for x in range(core.W):
            st, c = cell_state(img, geo, x, y)
            if st == "block":
                m |= 1 << x
                letters[(x, y)] = classify_color(c) or "G"
            elif st == "unknown":
                unknown.add((x, y))
        b.rows[y] = m
    return b, letters, unknown


def read_board(img, geo, rows=20):
    """Board of solid blocks for rows 0..rows-1, plus colour letters per block."""
    b, letters, _ = read_board_ex(img, geo, rows)
    return b, letters


def _pieces_in_box(img, geo, box):
    """Segment a preview box into piece blobs and classify each (top to bottom)."""
    x0, y0, x1, y1 = (int(round(v)) for v in box)
    h, w, _ = img.shape
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(w, x1), min(h, y1)
    if x1 <= x0 or y1 <= y0:
        return []
    sub = img[y0:y1, x0:x1].astype(int)
    occ = piece_pixels(sub)
    rows_occ = occ.mean(axis=1) > 0.02
    # vertical segmentation into blobs
    runs, start = [], None
    for i, v in enumerate(list(rows_occ) + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if runs and start - runs[-1][1] < geo.ch * 0.5:   # gap between cells of one piece
                runs[-1] = (runs[-1][0], i)
            else:
                runs.append((start, i))
            start = None
    blobs = [r for r in runs if r[1] - r[0] >= geo.ch * 0.6]
    out = []
    for by0, by1 in blobs:
        cols_occ = occ[by0:by1].mean(axis=0) > 0.05
        # keep column runs at least a third of a cell wide (drops border anti-aliasing)
        runs_x, st = [], None
        for i, v in enumerate(list(cols_occ) + [False]):
            if v and st is None:
                st = i
            elif not v and st is not None:
                if i - st >= geo.cw / 3:
                    runs_x.append((st, i))
                st = None
        if not runs_x:
            continue
        bx0, bx1 = runs_x[0][0], runs_x[-1][1]
        p = _classify_blob(sub[by0:by1, bx0:bx1], occ[by0:by1, bx0:bx1], geo)
        if p:
            out.append(p)
    return out


# Preview colours learned while playing (piece -> mean RGB), from previews where shape
# and colour agree. Starts from the default skin; adapts to the user's skin/brightness.
CALIBRATED = {}


def preview_colour_class(rgb):
    """(piece, confidence) by colour. confidence = distance to the 2nd-best colour divided
    by distance to the best (>= 2 means clearly that colour)."""
    rgb = np.asarray(rgb, dtype=float)
    if rgb.max() - rgb.min() < 30:
        return None, 0.0
    names = _PAL_NAMES
    pal = np.array([CALIBRATED.get(p, PALETTE[p]) for p in names], dtype=float)
    d = np.sqrt(((pal - rgb) ** 2).sum(axis=1))
    order = d.argsort()
    best, second = d[order[0]], d[order[1]]
    return names[int(order[0])], float(second / max(best, 1.0))


def _classify_blob(pix, occ, geo):
    """Identify a preview piece by its colour and its shape.

    Colour is primary (every piece type has its own colour); the shape confirms it.
    When both agree the colour is learned. When they disagree a clearly identified
    colour wins (shapes break more easily: anti-aliasing, pieces touching); otherwise
    the shape decides."""
    hh, ww = occ.shape
    nw = max(1, int(round(ww / geo.cw)))
    nh = max(1, int(round(hh / geo.ch)))
    pattern = []
    for j in range(nh):
        row = ""
        for i in range(nw):
            cy0, cy1 = int(hh * (j + 0.3) / nh), int(hh * (j + 0.7) / nh) + 1
            cx0, cx1 = int(ww * (i + 0.3) / nw), int(ww * (i + 0.7) / nw) + 1
            row += "X" if occ[cy0:cy1, cx0:cx1].mean() > 0.5 else "."
        pattern.append(row)
    by_shape = [p for p, pat in _PREVIEW.items() if pat == pattern]
    mean = pix[occ].mean(axis=0) if occ.any() else None
    colour, conf = preview_colour_class(mean) if mean is not None else (None, 0.0)
    if colour is not None and colour in by_shape:
        old = CALIBRATED.get(colour)
        CALIBRATED[colour] = mean if old is None else 0.9 * np.asarray(old) + 0.1 * mean
        return colour
    if colour is not None and conf >= 2.0:
        return colour
    if by_shape:
        return by_shape[0]
    return colour


def read_queue(img, geo):
    return _pieces_in_box(img, geo, geo.next_box())


def hold_locked(img, geo):
    """True when the hold piece is drawn grey: TETR.IO's sign that hold was already
    used for the piece in play (only one hold per piece)."""
    x0, y0, x1, y1 = (int(round(v)) for v in geo.hold_box())
    h, w, _ = img.shape
    sub = img[max(0, y0):min(h, y1), max(0, x0):min(w, x1)].astype(int)
    if sub.size == 0:
        return False
    mask = piece_pixels(sub)
    if mask.sum() < 20:
        return False
    px = sub[mask]
    saturated = (px.max(axis=1) - px.min(axis=1)) >= 30
    return saturated.mean() < 0.3


def read_hold(img, geo):
    ps = _pieces_in_box(img, geo, geo.hold_box())
    return ps[0] if ps else None


def read_ghost(img, geo, exclude=(), rows=22, color=None):
    """Cells of the ghost (drop shadow). TETR.IO draws it as a coloured outline
    around the whole piece, so a ghost cell has a dark centre and at least one
    coloured edge band."""
    out = set()
    r = max(1, int(min(geo.cw, geo.ch) * 0.05))
    for y in range(rows):
        for x in range(core.W):
            if (x, y) in exclude:
                continue
            if is_filled(cell_color(img, geo, x, y)):
                continue
            px0 = geo.left + x * geo.cw
            py0 = geo.top + (19 - y) * geo.ch
            for fx, fy in ((0.13, 0.5), (0.87, 0.5), (0.5, 0.13), (0.5, 0.87)):
                c = _patch(img, px0 + fx * geo.cw, py0 + fy * geo.ch, r)
                if c.max() >= 50 and c.max() - c.min() >= 30 and (color is None or _same_hue(c, color)):
                    out.add((x, y))
                    break
    return out


def _same_hue(a, b, tol=0.12):
    """Colours with the same hue/saturation pattern (ignores brightness)."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    na, nb = a / max(a.sum(), 1), b / max(b.sum(), 1)
    return float(np.abs(na - nb).max()) <= tol


def read_active(img, geo, sim_board=None, expect=None):
    """Find the falling piece: 4 same-coloured blocks forming a tetromino, not in
    `sim_board`. Looks at rows 0..22 (rows 20+ are drawn above the matrix).
    Prefers the `expect`ed piece type. Returns (piece, cells) or (None, None)."""
    cells = {}
    for y in range(23):
        for x in range(core.W):
            if sim_board is not None and y < 20 and sim_board.filled(x, y):
                continue
            st, c = cell_state(img, geo, x, y)
            if st == "block":
                p = classify_color(c)
                if p:
                    cells[(x, y)] = p
    found = []
    seen = set()
    for start in sorted(cells, key=lambda c: -c[1]):
        if start in seen:
            continue
        p = cells[start]
        grp, stack = [], [start]
        seen.add(start)
        while stack:
            cx, cy = stack.pop()
            grp.append((cx, cy))
            for n in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if n in cells and n not in seen and cells[n] == p:
                    seen.add(n)
                    stack.append(n)
        if len(grp) == 4 and core.identify(p, grp):
            found.append((p, tuple(sorted(grp))))
    if not found:
        return None, None
    for p, grp in found:
        if p == expect:
            return p, grp
    return found[0]
