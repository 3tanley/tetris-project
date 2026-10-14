"""Minimal fumen (v115) decoder: returns each page's field as rows of piece letters.

Only what the setup library needs: field diffs, the page's piece operation, lock /
line clear / mirror / rise flags, and comments.
"""
from urllib.parse import unquote

_B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
_CTAB = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
_TYPES = "_ILOZTJSX"          # 0 empty .. 8 garbage
_ROT = [2, 1, 0, 3]           # fumen rotation code -> our rot (0 spawn,1 R,2 180,3 L)
FIELD_TOP, WIDTH = 23, 10
NBLOCKS = (FIELD_TOP + 1) * WIDTH

# tetris-fumen piece offsets (y-up) for the spawn orientation, rotated per state.
_FP = {
    "I": [(0, 0), (-1, 0), (1, 0), (2, 0)],
    "T": [(0, 0), (-1, 0), (1, 0), (0, 1)],
    "O": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "L": [(0, 0), (-1, 0), (1, 0), (1, 1)],
    "J": [(0, 0), (-1, 0), (1, 0), (-1, 1)],
    "S": [(0, 0), (-1, 0), (0, 1), (1, 1)],
    "Z": [(0, 0), (1, 0), (0, 1), (-1, 1)],
}


def _blocks(piece, rot):
    b = _FP[piece]
    if rot == 0:
        return b
    if rot == 1:   # right
        return [(y, -x) for x, y in b]
    if rot == 2:
        return [(-x, -y) for x, y in b]
    return [(-y, x) for x, y in b]


def _coord(n, piece, rot):
    x = n % WIDTH
    y = FIELD_TOP - n // WIDTH - 1
    if piece == "O" and rot == 3:
        x += 1; y -= 1
    elif piece == "O" and rot == 2:
        x += 1
    elif piece == "O" and rot == 0:
        y -= 1
    elif piece == "I" and rot == 2:
        x += 1
    elif piece == "I" and rot == 3:
        y -= 1
    elif piece == "S" and rot == 0:
        y -= 1
    elif piece == "S" and rot == 1:
        x -= 1
    elif piece == "Z" and rot == 0:
        y -= 1
    elif piece == "Z" and rot == 3:
        x += 1
    return x, y


class _Reader:
    def __init__(self, s):
        self.v = [_B64.index(c) for c in s]
        self.i = 0

    def poll(self, n):
        val = 0
        for k in range(n):
            val += self.v[self.i] * 64 ** k
            self.i += 1
        return val

    def done(self):
        return self.i >= len(self.v)


class Page:
    def __init__(self, field, op, comment, lock):
        self.field = field          # dict (x,y)->letter, y in -1..22 (-1 = garbage row)
        self.op = op                # (piece, rot, x, y) or None
        self.comment = comment
        self.lock = lock

    def cells(self, with_op=True):
        f = {k: v for k, v in self.field.items() if k[1] >= 0}
        if with_op and self.op:
            for c in op_cells(self.op):
                f[c] = self.op[0]
        return f

    def rows(self, with_op=True):
        """Rows top->bottom as strings of letters ('.' empty, 'X' garbage)."""
        f = self.cells(with_op)
        h = max([y for _, y in f] + [-1]) + 1
        return ["".join(f.get((x, y), ".") for x in range(WIDTH)) for y in range(h - 1, -1, -1)]


def op_cells(op):
    p, r, x, y = op
    return [(x + dx, y + dy) for dx, dy in _blocks(p, r)]


def decode(code):
    code = code.strip()
    for pre in ("v115@", "d115@", "m115@"):
        if pre in code:
            code = code[code.index(pre) + len(pre):]
            break
    data = code.replace("?", "")
    rd = _Reader(data)
    field = {}
    pages = []
    repeat = 0
    comment = ""
    while not rd.done():
        # ---- field
        if repeat > 0:
            repeat -= 1
        else:
            idx = 0
            changed = False
            newf = dict(field)
            while idx < NBLOCKS:
                v = rd.poll(2)
                diff, run = divmod(v, NBLOCKS)
                if diff == 8 and run == NBLOCKS - 1:
                    pass
                else:
                    changed = True
                for _ in range(run + 1):
                    x = idx % WIDTH
                    y = FIELD_TOP - idx // WIDTH - 1
                    cur = _TYPES.index(newf.get((x, y), "_"))
                    nv = cur + diff - 8
                    if nv:
                        newf[(x, y)] = _TYPES[nv]
                    else:
                        newf.pop((x, y), None)
                    idx += 1
            field = newf
            if not changed:
                repeat = rd.poll(1)
        # ---- action
        v = rd.poll(3)
        t = v % 8; v //= 8
        r = _ROT[v % 4]; v //= 4
        loc = v % NBLOCKS; v //= NBLOCKS
        rise = v % 2; v //= 2
        mirror = v % 2; v //= 2
        v //= 2  # colour flag
        has_comment = v % 2; v //= 2
        lock = not (v % 2)
        if has_comment:
            n = rd.poll(2)
            chars = []
            for _ in range((n + 3) // 4):
                cv = rd.poll(5)
                for _ in range(4):
                    chars.append(_CTAB[cv % 96]); cv //= 96
            comment = unquote("".join(chars[:n]))
        op = None
        if t and t != 8:
            p = _TYPES[t]
            op = (p,) + (r,) + _coord(loc, p, r)
        pages.append(Page(dict(field), op, comment, lock))
        # ---- apply lock to produce next page's base field
        if lock:
            if op:
                for c in op_cells(op):
                    field[c] = op[0]
            # line clear (rows y>=0 only; garbage row untouched)
            ys = sorted({y for _, y in field if y >= 0})
            full = [y for y in ys if all((x, y) in field for x in range(WIDTH))]
            if full:
                nf = {}
                for (x, y), c in field.items():
                    if y in full:
                        continue
                    shift = sum(1 for fy in full if fy < y) if y >= 0 else 0
                    nf[(x, y - shift)] = c
                field = nf
            if rise:
                garbage = {k: c for k, c in field.items() if k[1] < 0}
                field = {(x, y + 1): c for (x, y), c in field.items()} | garbage
            if mirror:
                field = {(WIDTH - 1 - x, y): c for (x, y), c in field.items() if y >= 0} | {
                    k: c for k, c in field.items() if k[1] < 0}
    return pages
