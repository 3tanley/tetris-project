"""Setup templates: target fields made of piece "slots" that the planner fills in.

A template is a grid aligned with the bottom of the board. Each cell is empty, "G"
(must already be filled on the board) or belongs to a slot (one tetromino of a known
type). Slots marked `spin` are T pieces meant to be spun in (TSS/TSD/TST).
When rows clear on the board the same rows are dropped from the template, so
diagrams drawn "before the clear" (like the wiki's) work as-is.
"""
import re
from collections import Counter

from . import core, fumen
from .setups_wiki import WIKI_SETUPS
from .setups_dpc import DPC_SETUPS
from .setups_fourlol_sdpc import SDPC_PC_FUMENS
from . import setups_jigsaw as JIG
from . import setups_jaws as JAWS
from .setups_fourlol_2pc import PATTERNS as PC2_PATTERNS
from .setups_fourlol_pcs import PATTERNS as PCS

MIRROR_TYPE = {"L": "J", "J": "L", "S": "Z", "Z": "S", "I": "I", "O": "O", "T": "T"}

# All (rot, cells-relative-to-min) shapes per piece, for recognising slot cells.
_NORM = {}
for _p in core.PIECES:
    for _r in range(4):
        cs = core.SHAPES[_p][_r]
        mx, my = min(c[0] for c in cs), min(c[1] for c in cs)
        _NORM.setdefault(_p, set()).add(tuple(sorted((x - mx, y - my) for x, y in cs)))


def _norm(cells):
    mx, my = min(c[0] for c in cells), min(c[1] for c in cells)
    return tuple(sorted((x - mx, y - my) for x, y in cells))


def shape_type(cells, candidates=core.PIECES):
    n = _norm(cells)
    for p in candidates:
        if n in _NORM[p]:
            return p
    return None


def _partition(cells, ptype):
    """Split a set of cells into tetrominoes of `ptype` (backtracking). None if impossible."""
    cells = set(cells)
    if not cells:
        return []
    first = min(cells, key=lambda c: (c[1], c[0]))
    for shape in _NORM[ptype]:
        for ax, ay in shape:  # anchor shape cell onto `first`
            piece = {(first[0] + sx - ax, first[1] + sy - ay) for sx, sy in shape}
            if piece <= cells:
                rest = _partition(cells - piece, ptype)
                if rest is not None:
                    return [frozenset(piece)] + rest
    return None


def _placements_in(cells, ptype):
    """Every placement of `ptype` whose 4 cells are all in `cells`."""
    cells = set(cells)
    out = []
    for shape in _NORM[ptype]:
        for cx, cy in cells:
            for ax, ay in shape:
                piece = frozenset((cx + sx - ax, cy + sy - ay) for sx, sy in shape)
                if piece <= cells and piece not in out:
                    out.append(piece)
    return out


class Slot:
    __slots__ = ("sid", "ptype", "cells", "spin")

    def __init__(self, sid, ptype, cells, spin=False):
        self.sid, self.ptype, self.cells, self.spin = sid, ptype, frozenset(cells), spin

    def __repr__(self):
        return f"Slot({self.sid},{self.ptype}{',spin' if self.spin else ''})"


class Template:
    def __init__(self, name, family, stage, grid, slots, note="", mirrored=False, leftover=None,
                 criteria=(), label=""):
        self.name, self.family, self.stage, self.note = name, family, stage, note
        self.grid = grid            # rows bottom->top, each a list of 10 tokens (None/"G"/sid)
        self.slots = slots          # sid -> Slot
        self.mirrored = mirrored
        self.leftover = leftover    # DPC: type of the piece carried over from the previous bag
        self.criteria = tuple(criteria)  # DPC: (A, B) pairs, A must come before B
        self.label = label
        self.fallback = False       # only when nothing better can be built (compromise etc.)
        self.spin_last = True       # the T-spin finishes the setup (see dependencies)
        self.pc_rate = None         # published PC chance of what follows, if known
        self.pc_no = None           # four.lol 2nd-7th PC setups: which PC of the loop

    _EXTRA = ("fallback", "spin_last", "pc_rate", "pc_no")

    def __repr__(self):
        return f"<Template {self.name}>"

    def types(self):
        return sorted(s.ptype for s in self.slots.values())

    def g_board(self):
        """Board containing only the template's G cells."""
        b = core.Board()
        for y, row in enumerate(self.grid):
            for x, t in enumerate(row):
                if t == "G":
                    b.rows[y] |= 1 << x
        return b

    def mirror(self):
        grid = [list(reversed(row)) for row in self.grid]
        slots = {}
        for sid, s in self.slots.items():
            slots[sid] = Slot(sid, MIRROR_TYPE[s.ptype], {(9 - x, y) for x, y in s.cells}, s.spin)
        name = self.name[:-3] if self.name.endswith("(m)") else self.name + "(m)"
        m = MIRROR_TYPE
        # piece-order labels (JO, OJ+ZS) mirror letter by letter; names like "SD-PC #1" don't
        label = "".join(m.get(c, c) for c in self.label) if set(self.label) <= set("IJLOSTZ+") else self.label
        t = Template(name, self.family, self.stage, grid, slots, self.note, not self.mirrored,
                     m.get(self.leftover) if self.leftover else None,
                     tuple((m[a], m[b]) for a, b in self.criteria), label)
        for k in self._EXTRA:
            setattr(t, k, getattr(self, k))
        return t

    def render(self):
        out = []
        for row in reversed(self.grid):
            out.append(" ".join("." if t is None else ("G" if t == "G" else self.slots[t].ptype) for t in row))
        return "\n".join(out)


def _build(name, family, stage, token_rows_top, note="", type_of=None, split_ok=False):
    """token_rows_top: list of rows (top->bottom) of tokens. type_of(token)->(type candidates, spin)."""
    rows = list(reversed(token_rows_top))
    groups = {}
    for y, row in enumerate(rows):
        for x, t in enumerate(row):
            if t not in (None, "G"):
                groups.setdefault(t, set()).add((x, y))
    grid = [[None if t is None else ("G" if t == "G" else None) for t in row] for row in rows]
    slots = {}
    for tok, cells in groups.items():
        cands, spin = type_of(tok)
        pieces = None
        for p in cands:
            pieces = _partition(cells, p)
            if pieces is not None:
                break
        if pieces is None and len(cells) == 4 and split_ok:
            # a piece drawn across a row that clears before it is placed
            p, pieces = cands[0], [frozenset(cells)]
        if pieces is None and len(cells) == 8 and split_ok:
            # two pieces of one type, one of them drawn across a row that clears first
            p = cands[0]
            for one in _placements_in(cells, p):
                rest = frozenset(cells) - one
                if _partition(rest, p) is None:
                    pieces = [one, rest]
                    break
        if pieces is None:
            raise ValueError(f"{name}: cells of {tok!r} do not form {cands} pieces")
        for i, pc in enumerate(pieces):
            sid = f"{tok}{i}" if len(pieces) > 1 else tok
            slots[sid] = Slot(sid, p, pc, spin)
            for x, y in pc:
                grid[y][x] = sid
    return Template(name, family, stage, grid, slots, note)


def _wiki_type(tok):
    if tok == "P":
        return ["T"], True
    if len(tok) == 1:
        return [tok], False
    return [tok[-1], tok[0]], False   # "LJ" -> light J, "LL" -> second L


def _wiki_templates():
    out = []
    for name, family, stage, note, rows in WIKI_SETUPS:
        toks = [[None if t == "." else t for t in r.split()] for r in rows]
        out.append(_build(name, family, stage, toks, note, _wiki_type))
    return out


def _find_tsd_slot(board):
    """T placement on `board` that is a full T-spin clearing exactly 2 lines."""
    for pl in core.generate(board, "T").values():
        if pl.spin == "full":
            _, n = core.lock(board, pl)
            if n == 2:
                return pl.cells
    return None


def _blocks(rows):
    """Split stacked diagrams (top->bottom rows) on fully blank rows."""
    blocks, cur = [], []
    for r in rows:
        if set(r) == {"."}:
            if cur:
                blocks.append(cur)
            cur = []
        else:
            cur.append(r)
    if cur:
        blocks.append(cur)
    return blocks


def _parse_criteria(text):
    return tuple((c[0], c[2]) for c in text.split())


def _dpc_templates():
    """(setups, pc_solutions) from four.lol DPC."""
    setups, sols = [], []
    for name, label, extra, crit, code, sol_codes in DPC_SETUPS:
        blocks = _blocks(fumen.decode(code)[0].rows(with_op=True))
        for bi, blk in enumerate(blocks):
            toks = [[None if c == "." else c for c in r] for r in blk]
            tname = f"DPC-{extra}-{label}" + (f"-{bi + 1}" if len(blocks) > 1 else "")
            t = _build(tname, "DPC", "dpc", toks, f"DPC extra {extra}: {label} ({name})",
                       lambda tok, e=extra: ([e], False) if tok == "X" else ([tok], False))
            b = core.Board()
            for sl in t.slots.values():
                for x, y in sl.cells:
                    b.rows[y] |= 1 << x
            tcells = _find_tsd_slot(b)
            if tcells is None:
                continue
            while len(t.grid) <= max(y for _, y in tcells):
                t.grid.append([None] * 10)
            t.slots["P"] = Slot("P", "T", tcells, True)
            for x, y in tcells:
                t.grid[y][x] = "P"
            t.leftover, t.criteria, t.label = extra, _parse_criteria(crit), label
            setups.append(t)
        n = 0
        for sc in sol_codes:
            for page in fumen.decode(sc):
                rows = page.rows(with_op=True)
                if not rows:
                    continue
                n += 1
                toks = [[None if c == "." else ("G" if c == "X" else c) for c in r] for r in rows]
                try:
                    t = _build(f"PC-{extra}-{label}-{n}", "DPC", "dpc_pc", toks,
                               f"four.lol PC solution {n} for {label} ({page.comment.split(':')[0].strip()})",
                               lambda tok: ([tok], tok == "T"), split_ok=True)
                except ValueError:
                    continue
                t.label = label
                sols.append(t)
    return setups, sols


def _sdpc_pc_templates():
    """four.lol SD-PC 8-line PC solutions (grey = field after the TSD)."""
    out, n = [], 0
    for code in SDPC_PC_FUMENS:
        for page in fumen.decode(code):
            rows = page.rows(with_op=True)
            if not rows or any("." in r for r in rows):
                continue
            n += 1
            toks = [[("G" if c == "X" else c) for c in r] for r in rows]
            try:
                t = _build(f"PC-SDPC-{n}", "SDPC", "sdpc_pc", toks,
                           f"four.lol SD-PC solution {n} ({page.comment.split(':')[-1].strip()})",
                           lambda tok: ([tok], tok == "T"), split_ok=True)
            except ValueError:
                continue
            t.label = f"SD-PC #{n}"
            out.append(t)
    return out


def _jig_rows(rows):
    return [[None if c == "." else c for c in r.split()] for r in rows]


def _jigsaw_templates():
    """(openers, 2nd-bag builds incl. early PCs, 3rd-bag PCs) of the Jigsaw PC loop."""
    upper = lambda tok: ([tok.upper()], False)
    bag1 = [_build(n, "JIGSAW", "bag1", _jig_rows(r), note, upper) for n, note, r in JIG.BAG1]
    for t in bag1:          # the wiki: PCO has the higher chance of an early 1st PC
        t.pc_rate = 0.7452 if "PCO" in t.name else 0.6988

    def bag2_type(tok):
        if tok == "P":
            return ["T"], True          # the Jaws T, spun into the notch
        if tok == "H":
            return ["L"], False         # the PCO L
        return [tok.upper()], False

    bag2 = []
    for n, note, r in JIG.BAG2:
        t = _build(n, "JIGSAW", "bag2", _jig_rows(r), note, bag2_type, split_ok=True)
        # T S J I may go on top before the 3-line solve or onto the empty field after it
        # (an early PC): the T-spin is not the last move here
        t.spin_last = False
        t.fallback = "alt" in n
        bag2.append(t)
    for n, pct, r in JIG.EARLY:
        t = _build(f"Jigsaw-early-{n}", "JIGSAW", "bag2_pc", _jig_rows(r),
                   f"Jigsaw early PC {n} ({pct}% - ends the loop)",
                   lambda tok: (["T"], False) if tok == "u" else ([tok], tok == "T"), split_ok=True)
        t.fallback, t.label = True, n
        bag2.append(t)
    bag3 = []
    for i, (n, r) in enumerate(JIG.BAG3):
        t = _build(f"Jigsaw-3-{i + 1}", "JIGSAW", "pc8_pc", _jig_rows(r),
                   f"Jigsaw 3rd bag PC: {n}", lambda tok: ([tok], False))
        t.label = f"Jigsaw PC: {n}"
        bag3.append(t)
    return bag1, bag2, bag3


ORDINAL = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th", 7: "7th"}
_PAGE_PCT = re.compile(r"([\d.]+)%")


def _pc_templates():
    """four.lol 2nd-7th PC: (setups, solutions). A setup arranges pieces on the empty field
    (the pieces left of the last bag + a few new ones); a solution is the 4-line PC on top
    of it (grey = the setup). Setups carry `pc_no`, the PC they are drawn for."""
    setups, sols = [], []
    for n, patterns in [(2, PC2_PATTERNS)] + sorted(PCS.items()):
        for name, pct, codes in patterns:
            ns = nsol = 0
            drawn = []                                # this pattern's setups, for grey extensions
            for code in codes:
                for page in fumen.decode(code):
                    m = _PAGE_PCT.search(page.comment)
                    rate = float(m.group(1)) if m else pct
                    for blk in _blocks(page.rows(with_op=True)):
                        cells = "".join(blk)
                        if all(c in ".X" for c in cells):
                            continue                  # the grey outline only
                        grey, gaps = "X" in cells, "." in cells
                        if grey and gaps:
                            blk = _ungrey(blk, drawn)  # more pieces on a setup drawn grey
                            if blk is None:
                                continue
                        toks = [[None if c == "." else ("G" if c == "X" else c) for c in r] for r in blk]
                        try:
                            if not grey or gaps:
                                ns += 1
                                t = _build(f"PC{n}-{name}-setup{ns}", "PC2", "pc2", toks,
                                           f"{ORDINAL[n]} PC {name} ({rate}%)",
                                           lambda tok: ([tok.upper()], False))
                                drawn.append(blk)
                            else:
                                nsol += 1
                                t = _build(f"PC{n}-{name}-{nsol}", "PC2", "pc2_pc", toks,
                                           f"{ORDINAL[n]} PC {name}: solution {nsol} ({page.comment.strip()})",
                                           lambda tok: ([tok], tok == "T"), split_ok=True)
                        except ValueError:
                            continue
                        t.label, t.pc_rate, t.pc_no = f"{ORDINAL[n]} PC {name}", (rate or 0.0) / 100.0, n
                        (setups if not grey or gaps else sols).append(t)
    return setups, sols


def _ungrey(blk, drawn):
    """A page that draws an earlier setup of the pattern in grey plus new pieces: put the
    setup's pieces back (lower case, so they stay separate pieces). None if no setup fits."""
    h = len(blk)
    grey = {(x, h - 1 - y) for y, r in enumerate(blk) for x, c in enumerate(r) if c == "X"}
    for s in drawn:
        cells = {(x, len(s) - 1 - y): c for y, r in enumerate(s) for x, c in enumerate(r) if c != "."}
        if set(cells) == grey:
            return ["".join(cells[(x, h - 1 - y)].lower() if c == "X" else c for x, c in enumerate(r))
                    for y, r in enumerate(blk)]
    return None


def _jaws_templates():
    """Jaws 1st PC (four.lol ILSZ): the 4-piece I L S Z build + one solution each, as one
    10-piece template (an O, T or J that comes early can go straight to its spot in the
    solution). Build slots are named b<piece>; the O / J of the ILOSZ / ILJOSZ fields are
    v<piece>: they belong to the solution, so the build stays 4 pieces."""
    build = [r.split() for r in JAWS.BUILD]
    out = []
    for kind, field_code, sol_code in (("", None, JAWS.SOLUTIONS_ILSZ),
                                       ("ILOSZ", JAWS.FIELD_ILOSZ, JAWS.SOLUTIONS_ILOSZ),
                                       ("ILJOSZ", JAWS.FIELD_ILJOSZ, JAWS.SOLUTIONS_ILJOSZ)):
        field = [list(r) for r in fumen.decode(field_code)[0].rows(with_op=True)] if field_code else \
            [[c if c != "." else "." for c in r] for r in build]
        full = [y for y, r in enumerate(field) if "." not in r]          # rows four.lol drew cleared
        for n, page in enumerate(fumen.decode(sol_code)):
            sol = [list(r) for r in page.rows(with_op=True)]
            for y in full:
                sol.insert(y, ["X"] * 10)
            rows = []
            for y, (frow, srow) in enumerate(zip(field, sol)):
                row = []
                for x, (f, c) in enumerate(zip(frow, srow)):
                    if c == "X":
                        row.append(("b" if build[y][x] != "." else "v") + f)
                    else:
                        row.append(None if c == "." else c)
                rows.append(row)

            def type_of(tok):
                if tok[0] in "bv":
                    return [tok[1]], False
                return [tok], tok == "T"

            name = f"Jaws{'-' + kind if kind else ''}-{n + 1}"
            try:
                t = _build(name, "JAWS", "pc1_pc", rows,
                           f"Jaws {kind or 'ILSZ'} 1st PC, four.lol solution {n + 1}", type_of, split_ok=True)
            except ValueError:
                continue        # a piece drawn across a row that clears first (like the DPC loader)
            t.label = f"Jaws {kind + ' ' if kind else ''}#{n + 1}"
            out.append(t)
    return out


def _with_mirrors(ts):
    out = []
    for t in ts:
        out.append(t)
        out.append(t.mirror())
    return out


_LIB = None


def library():
    global _LIB
    if _LIB is None:
        setups, sols = _dpc_templates()
        j1, j2, j3 = _jigsaw_templates()
        p2s, p2p = _pc_templates()
        _LIB = {"wiki": _with_mirrors(_wiki_templates()) + _with_mirrors(j1) + _dedupe(_with_mirrors(j2)),
                "dpc": _with_mirrors(setups),
                "dpc_pc": _dedupe(_with_mirrors(sols)),
                "sdpc_pc": _dedupe(_with_mirrors(_sdpc_pc_templates())),
                "jigsaw_pc": _dedupe(_with_mirrors(j3)),
                "jaws": _dedupe(_with_mirrors(_jaws_templates())),
                "pc2_pc": _dedupe(_with_mirrors(p2p))}
        # a PC setup is only useful if some solution starts from the field it leaves
        # (four.lol's setup fumens also hold a few in-between drawings) - except the 7th
        # PC's 100% setups, drawn without solutions: the 7 pieces after them are all in
        # view (5 previews + the inferred end of the bag), so the solver finishes them
        starts = {tuple(t.g_board().rows) for t in _LIB["pc2_pc"]}
        _LIB["pc2"] = [t for t in _dedupe(_with_mirrors(p2s))
                       if tuple(residue(t).rows) in starts or (t.pc_no == 7 and t.pc_rate == 1.0)]
        # a Jaws solution decides which 4 pieces of bag 2 are left: rate it by the best
        # 2nd PC pattern for those (bag 2 = the 6 solution pieces minus O T J of bag 1)
        best = {}
        for t in pc2_setups(2):
            k = tuple(sorted(t.types()))
            best[k] = max(best.get(k, 0.0), t.pc_rate)
        for t in _LIB["jaws"]:
            sol = Counter(t.types()) - Counter("IJZS" if t.mirrored else "ILSZ")   # the 6 PC pieces
            bag1_rest = Counter("OTL" if t.mirrored else "OTJ")
            bag2_used = sol - bag1_rest
            left = (bag1_rest - sol) + (Counter(core.PIECES) - bag2_used)
            left = tuple(sorted(left.elements())) if sum(left.values()) == 4 else None
            t.leftover2 = left
            t.pc_rate = best.get(left, 0.0) if left else 0.0
        for t in _LIB["wiki"]:
            if t.name in ("SingleYou-B(m)", "SDPC-TSD(m)"):
                t.note += " = four.lol SD-PC (O on the left)"
            if "altO" in t.name or "compromise" in t.note:
                t.fallback = True
    return _LIB


# Opener families (the user's toggles) in their old priority order, with the published
# chance of the perfect clear that follows (8-line PC after the 2nd bag):
#   SD-PC 99.44% (four.lol, with the TSS solutions); Mountainous Stacking 1/2/3: the
#   average of their 2nd-bag setups (Hard Drop wiki); Jigsaw: build and 3rd-bag PC are
#   both guaranteed (Hard Drop wiki).
FAMILY_PRIORITY = ["JAWS", "SDPC", "MS2", "MS", "MS3", "JIGSAW"]
FAMILY_NAMES = {"JAWS": "Jaws (ILSZ) 1st PC", "SDPC": "SingleYou / SD-PC", "MS2": "Mountainous Stacking 2",
                "MS": "Mountainous Stacking", "MS3": "Mountainous Stacking 3", "JIGSAW": "Jigsaw PC loop"}
PC_RATE = {"JAWS": 1.0, "SDPC": 0.9944, "MS2": 0.9845, "MS": 0.9755, "MS3": 0.9643, "JIGSAW": 1.0}


def openers(families=None):
    lib = library()["wiki"] + library()["jaws"]
    fams = FAMILY_PRIORITY if families is None else [f for f in FAMILY_PRIORITY if f in families]
    return [t for f in fams for t in lib if t.family == f and t.stage in ("bag1", "pc1_pc")]


def pc2_setups(pc_no=None):
    """four.lol setups for the `pc_no`-th PC of the loop (2-7; None = all of them)."""
    return [t for t in library()["pc2"] if pc_no is None or t.pc_no == pc_no]


def pc2_solutions(board=None):
    """four.lol's 2nd-7th PC solutions; with `board`, only those starting from it."""
    lib = library()
    if board is None:
        return lib["pc2_pc"]
    if "pc2_pc_at" not in lib:
        lib["pc2_pc_at"] = {}
        for t in lib["pc2_pc"]:
            lib["pc2_pc_at"].setdefault(tuple(t.g_board().rows), []).append(t)
    return lib["pc2_pc_at"].get(tuple(board.rows), [])


_FULL = {}


def pc_full(setup):
    """A 2nd-7th PC setup with each four.lol solution on it, as one 10-piece template (like
    Jaws): a piece the setup doesn't use that comes early goes straight to its solution
    spot. Setup slots are named b<sid>."""
    if setup.name not in _FULL:
        out = []
        full = [y for y, row in enumerate(setup.grid) if all(row)]     # rows the setup clears
        for sol in pc2_solutions(residue(setup)):
            grid = [list(row) for row in sol.grid]
            for y in full:
                grid.insert(y, [None] * core.W)
            grid = [[("b" + setup.grid[y][x]) if y < len(setup.grid) and setup.grid[y][x] else t
                     for x, t in enumerate(row)] for y, row in enumerate(grid)]
            slots = dict(sol.slots)
            slots.update({"b" + sid: Slot("b" + sid, s.ptype, s.cells, s.spin) for sid, s in setup.slots.items()})
            t = Template(f"{setup.name}+{sol.name}", "PC2", "pc2_pc", grid, slots,
                         f"{sol.note} (built with the setup)", setup.mirrored, label=sol.label)
            t.pc_rate, t.pc_no, t.setup = setup.pc_rate, setup.pc_no, setup
            out.append(t)
        _FULL[setup.name] = out
    return _FULL[setup.name]


def second_bag(family):
    return [t for t in library()["wiki"] if t.family == family and t.stage in ("bag2", "bag2_pc")]


def pc8_solutions(family):
    """Known 8-line PC solutions for what a family's 2nd bag leaves (None: use the solver)."""
    return {"SDPC": library()["sdpc_pc"], "JIGSAW": library()["jigsaw_pc"],
            "PC2": library()["pc2_pc"]}.get(family)


def dpc(leftover=None):
    return [t for t in library()["dpc"] if leftover is None or t.leftover == leftover]


def dpc_solutions():
    return library()["dpc_pc"]


def residue(t):
    """The field a setup leaves when every slot (incl. the T-spin) is in."""
    b = t.g_board()
    for y, row in enumerate(t.grid):
        for x, tok in enumerate(row):
            if tok not in (None, "G"):
                b.rows[y] |= 1 << x
    b.clear_lines()
    return b


def solutions_after(t):
    """PC solutions whose starting field is what setup `t` leaves (four.lol: some setups
    make the same shape as others, e.g. OS = JO, so their solutions apply too)."""
    r = residue(t)
    return [s for s in dpc_solutions() if s.g_board() == r]


def sdpc_solutions():
    return library()["sdpc_pc"]


def _dedupe(ts):
    seen, out = set(), []
    for t in ts:
        k = tuple(tuple(t.slots[c].ptype if c not in (None, "G") else c for c in row) for row in t.grid)
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out


def criteria_status(tmpl, order):
    """Check a DPC setup's "A before B" criteria against the upcoming piece order.
    `order` = next bag's pieces as far as known (hold first). Returns (ok, unknown, text)."""
    pos = {}
    for i, p in enumerate(order):
        pos.setdefault(p, i)
    ok, unknown, parts = True, False, []
    for a, b in tmpl.criteria:
        pa, pb = pos.get(a), pos.get(b)
        if pa is not None and (pb is None or pa < pb):
            parts.append(f"{a}<{b} ✓")
        elif pb is not None:
            parts.append(f"{a}<{b} ✗")
            ok = False
        else:
            parts.append(f"{a}<{b} ?")
            unknown = True
    return ok, unknown, " ".join(parts) or "no order needed"


# ------------------------------------------------------------ piece dependencies
def dependencies(t):
    """Which slots must be placed before which (the "priority list" of a setup/solve).

    Returns (hard, soft): dicts slot -> set of slots that must come first.
      hard: a piece drawn across rows that clear before it is placed (four.lol draws
            those "split") can only go in after every piece in those rows is down.
            In a setup (not a PC solution) the T-spin also goes in after every other
            piece: it is the move that finishes the setup.
      soft: building bottom-up - a slot directly below another goes first, so nothing
            has to be tucked under it later. Planned T-spin slots are exempt (they go
            in last, under their overhang)."""
    if getattr(t, "_deps", None) is not None:
        return t._deps
    owner = {c: sid for sid, s in t.slots.items() for c in s.cells}
    hard = {sid: set() for sid in t.slots}
    soft = {sid: set() for sid in t.slots}
    for sid, s in t.slots.items():
        ys = sorted({y for _, y in s.cells})
        for y in range(ys[0], ys[-1] + 1):
            if y in ys:
                continue
            for x in range(core.W):
                o = owner.get((x, y))
                if o is not None and o != sid:
                    hard[sid].add(o)
    if t.spin_last and not t.stage.endswith("_pc"):
        for sid, s in t.slots.items():
            if s.spin:
                for o, so in t.slots.items():
                    if o != sid and not so.spin and sid not in _ancestors(o, hard, {}):
                        hard[sid].add(o)
    for sid, s in t.slots.items():
        for x, y in s.cells:
            o = owner.get((x, y - 1))
            if o is not None and o != sid and (not t.slots[o].spin or not t.spin_last) \
                    and o not in hard[sid]:
                soft[sid].add(o)
        if s.spin and t.spin_last:         # a T-spin goes in after its overhang
            for x, y in s.cells:
                o = owner.get((x, y + 1))
                if o is not None and o != sid and o not in hard[sid]:
                    soft[sid].add(o)
    # drop soft edges that would create a cycle with the hard ones
    for sid in list(soft):
        for o in list(soft[sid]):
            if sid in _ancestors(o, hard, soft):
                soft[sid].discard(o)
    t._deps = (hard, soft)
    return t._deps


def _ancestors(sid, hard, soft):
    seen, stack = set(), [sid]
    while stack:
        cur = stack.pop()
        for o in hard.get(cur, set()) | soft.get(cur, set()):
            if o not in seen:
                seen.add(o)
                stack.append(o)
    return seen


def order_conflicts(t, remaining, order):
    """How many "A goes before B" dependencies the arrival order breaks (B shows up
    before A, so B has to wait in hold). `order` = hold first, then current + queue;
    a type not visible yet counts as arriving last. T-spins are always last, so they
    don't count."""
    pos = {}
    for i, p in enumerate(order):
        pos.setdefault(p, i)
    late = len(order)
    hard, soft = dependencies(t)
    rem = set(remaining)
    n = 0
    for b in rem:
        sb = t.slots[b]
        if sb.spin:
            continue
        for a in (hard[b] | soft[b]) & rem:
            sa = t.slots[a]
            if not sa.spin and sa.ptype != sb.ptype and pos.get(sb.ptype, late) < pos.get(sa.ptype, late):
                n += 1
    return n


def priority_groups(t, remaining=None):
    """Remaining slots grouped by priority (placement wave): [[slot, ...], ...]."""
    hard, soft = dependencies(t)
    rem = set(t.slots) if remaining is None else set(remaining)
    groups = []
    while rem:
        wave = [s for s in rem if not ((hard[s] | soft[s]) & rem)]
        if not wave:                      # should not happen (cycles removed)
            wave = list(rem)
        groups.append(sorted(wave, key=lambda s: min(y for _, y in t.slots[s].cells)))
        rem -= set(wave)
    return groups


def priority_text(t, remaining=None):
    groups = priority_groups(t, remaining)
    return " › ".join(" ".join(t.slots[s].ptype for s in g) for g in groups)


# ------------------------------------------------------------------ live state
class TState:
    """A template being filled on a real board: rows aligned with board rows."""

    __slots__ = ("tmpl", "grid", "remaining")

    def __init__(self, tmpl, grid=None, remaining=None):
        self.tmpl = tmpl
        self.grid = [list(r) for r in (grid if grid is not None else tmpl.grid)]
        self.remaining = frozenset(tmpl.slots) if remaining is None else remaining

    def copy(self):
        return TState(self.tmpl, self.grid, self.remaining)

    def slot_cells(self, sid):
        """Current board coordinates of a slot (rows may have shifted after clears)."""
        out = []
        for y, row in enumerate(self.grid):
            for x, t in enumerate(row):
                if t == sid:
                    out.append((x, y))
        return tuple(sorted(out))

    def apply(self, sid, cleared):
        self.remaining = self.remaining - {sid}
        for y in sorted(cleared, reverse=True):
            if y < len(self.grid):
                del self.grid[y]

    def matches(self, board):
        """Board filled exactly where the template says (G + placed slots), empty elsewhere."""
        for y in range(core.H):
            row = self.grid[y] if y < len(self.grid) else None
            want = 0
            if row:
                for x, t in enumerate(row):
                    if t == "G" or (t is not None and t not in self.remaining):
                        want |= 1 << x
            if board.rows[y] != want:
                return False
        return True

    @classmethod
    def fresh_on(cls, tmpl, board):
        """Start `tmpl` on `board` if the board equals its G cells; else None."""
        ts = cls(tmpl)
        return ts if ts.matches(board) else None
