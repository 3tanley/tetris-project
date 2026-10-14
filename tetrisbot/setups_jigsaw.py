"""Jigsaw PC loop (stickmancomic) from https://harddrop.com/wiki/Jigsaw_PC_Loop

Rows are top -> bottom, one token per cell ('.' empty, 'G' already on the board).
Mirrors are generated in code.

* Bag 1: the Jaws or the PCO build. Each clears one line and keeps one piece in hold
  (Jaws: T, PCO: L).
* Bag 2: the 3-line solve below (held piece + Z O L) and T S J I stacked on top. When
  the 3 lines clear, the same residue is left either way. The wiki draws the left five
  columns as generic "g"; here they are filled in per variant: the Jaws T is spun into
  the notch (token P), the PCO L drops into it (token H). Lowercase = bag-2 pieces.
  Main pattern for almost every order; the alternate one only for IO > Z > L (its Z
  is drawn across the two rows that clear before it goes in).
* Bag 3: 4-line PCs on that residue that leave S, Z (-> S/Z DPC) or O unused.
* Early PC (Jaws only): the wiki's 2nd-bag solves finish a 4-line PC straight away,
  with T + 3 pieces. They end the loop (4 pieces left over), so they're only a fallback.
"""

BAG1 = [
    ("Jigsaw-Jaws", "Jigsaw bag 1, Jaws variant (hold T; bag order Z > T)", [
        "I L L L . . . . . .",
        "I L Z . . . . . . .",
        "I Z Z S S O O J J J",
        "I Z S S . O O . . J",
    ]),
    ("Jigsaw-PCO", "Jigsaw bag 1, PCO variant (hold L; bag order TS > Z)", [
        "I Z Z . . . . . . .",
        "I T Z Z . . . . . .",
        "I T T S S O O J J J",
        "I T S S . O O . . J",
    ]),
]

# residue left by each bag-1 build, as the left five columns of bag 2 (rows top->bottom:
# the three rows of the 3-line solve). P = held T (spun in), H = held L.
_LEFT = {
    "Jaws": ["G G G G P", "G G G P P", "G G G G P"],
    "PCO": ["G G G H H", "G G G G H", "G G G G H"],
}
_TOP = ["t . . . j . . . . .",
        "t t s s j . . . . .",
        "t s s j j . i i i i"]
_TOP_ALT = ["t . . . j . . . . .",
            "t t s s j . . . . .",
            "t s s j j . z z o o"]
_RIGHT = ["l l l o o", "l z z o o", "G G z z G"]
_RIGHT_ALT = ["l l l o o", "l i i i i", "G G z z G"]


def _bag2(variant, top, right):
    return top + [f"{a} {b}" for a, b in zip(_LEFT[variant], right)]


BAG2 = [
    (f"Jigsaw-2-{v}", f"Jigsaw bag 2 ({v}): 3-line solve + T S J I on top", _bag2(v, _TOP, _RIGHT))
    for v in ("Jaws", "PCO")
] + [
    (f"Jigsaw-2-{v}-alt", f"Jigsaw bag 2 ({v}), alternate for IO > Z > L", _bag2(v, _TOP_ALT, _RIGHT_ALT))
    for v in ("Jaws", "PCO")
]

# bag 3: residue rows "G . . . G" / "G G G G G" / "G G G G G . G G G G" plus the PC
BAG3 = [
    ("O>J, S left", ["Z Z T T T I L O O J",
                     "G Z Z T G I L O O J",
                     "G G G G G I L L J J",
                     "G G G G G I G G G G"]),
    ("O>J, Z left", ["T T T S S I L O O J",
                     "G T S S G I L O O J",
                     "G G G G G I L L J J",
                     "G G G G G I G G G G"]),
    ("JL>O, S left", ["Z Z T T T I J J L L",
                      "G Z Z T G I J O O L",
                      "G G G G G I J O O L",
                      "G G G G G I G G G G"]),
    ("JL>O, Z left", ["T T T S S I J J L L",
                      "G T S S G I J O O L",
                      "G G G G G I J O O L",
                      "G G G G G I G G G G"]),
    # optional: the I goes in last for a Tetris PC, O left
    ("Tetris, O left", ["T T T S S I Z Z L L",
                        "G T S S G I J Z Z L",
                        "G G G G G I J J J L",
                        "G G G G G I G G G G"]),
    ("Tetris, O left", ["T T T S S I L J J J",
                        "G T S S G I L Z Z J",
                        "G G G G G I L L Z Z",
                        "G G G G G I G G G G"]),
]

# early 4-line PC after the Jaws build: (name, wiki chance, rows top->bottom).
# T = the held bag-1 T; u = a bag-2 T (in the "no T" solves, where both are used).
EARLY = [
    ("ZOTI", 14.99, ["G G G G I I I I O O", "G G G T T T Z Z O O", "G G G G T G G Z Z G"]),
    ("ZOTL", 14.99, ["G G G G T L L L O O", "G G G T T L Z Z O O", "G G G G T G G Z Z G"]),
    ("STJI", 13.63, ["G G G G T J I I I I", "G G G T T J J J S S", "G G G G T G G S S G"]),
    ("ZTJI", 10.90, ["G G G G T I I I I Z", "G G G T T J J J Z Z", "G G G G T G G J Z G"]),
    ("STOL", 10.90, ["G G G G T O O L L L", "G G G T T O O L S S", "G G G G T G G S S G"]),
    ("ZJTO", 10.90, ["G G G G T O O J J Z", "G G G T T O O J Z Z", "G G G G T G G J Z G"]),
    ("ITLS", 8.18, ["G G G G T L L L S S", "G G G T T L I I I I", "G G G G T G G S S G"]),
    ("JTOS", 8.18, ["G G G G T O O J S S", "G G G T T O O J J J", "G G G G T G G S S G"]),
    ("OTJZ", 8.18, ["G G G G T J Z Z O O", "G G G T T J J J O O", "G G G G T G G Z Z G"]),
    ("TTOL", 8.18, ["G G G G T O O L L L", "G G G T T O O u u u", "G G G G T G G L u G"]),
    ("LTOT", 8.18, ["G G G G T O O u u u", "G G G T T O O L L L", "G G G G T G G L u G"]),
    ("ZTJT", 8.18, ["G G G G T J u u u Z", "G G G T T J J J Z Z", "G G G G T G G u Z G"]),
    ("OLTJ", 12.27, ["G G G G J J J L O O", "G G G T T T J L O O", "G G G G T G G L L G"]),
    ("STLJ", 10.90, ["G G G G J J J L L L", "G G G T T T J L S S", "G G G G T G G S S G"]),
    ("LTJT", 8.18, ["G G G G J J J u u u", "G G G T T T J L L L", "G G G G T G G L u G"]),
    ("TTJL", 8.18, ["G G G G J J J L L L", "G G G T T T J u u u", "G G G G T G G L u G"]),
    ("OIJL", 0.51, ["G G G G L L L J J J", "G G G I I I I O O J", "G G G G L G G O O G"]),
]
