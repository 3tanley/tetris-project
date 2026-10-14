"""Jaws (ILSZ) 1st PC from https://harddrop.com/wiki/Jaws (four.lol: "A 100% 1st PC pattern").

The build is I L S Z on the left (rows top -> bottom). Every solution is a 4-line PC on
top of it (G = the build) with the other 6 pieces: the rest of bag 1 + 3 of bag 2,
which leaves 4 pieces of bag 2 for the 2nd PC (setups_fourlol_2pc.py).
Extracted by script from the wiki source; tokens: j = a second J, t = a second T
(the wiki draws them in another shade). Mirrors are generated in code.
"""

BUILD = [
    "I L L L . . . . . .",
    "I L Z . . . . . . .",
    "I Z Z S S . . . . .",
    "I Z S S . . . . . .",
]

SOLUTIONS = [
    ["G G G G S S L L O O", "G G G S S J T L O O", "G G G G G J T T O O", "G G G G J J T L O O"],
    ["G G G G S S J J O O", "G G G S S J J T O O", "G G G G G J T T O O", "G G G G J J J T O O"],
    ["G G G G I I I I O O", "G G G T T T Z Z O O", "G G G G G O O J J J", "G G G G T O O Z Z J"],
    ["G G G G T T T J J J", "G G G Z Z T T J J J", "G G G G G T T J O O", "G G G G Z Z T J O O"],
    ["G G G G I I I I J J", "G G G Z Z O O J J T", "G G G G G O O J T T", "G G G G Z Z J J J T"],
    ["G G G G T T T L L L", "G G G Z Z T T L O O", "G G G G G T T J O O", "G G G G Z Z T J J J"],
    ["G G G G T J J J O O", "G G G T T T L J O O", "G G G G G J J J O O", "G G G G L L L J O O"],
    ["G G G G I I I I L L", "G G G Z Z O O J T L", "G G G G G O O J T T", "G G G G Z Z J J T L"],
    ["G G G G S S I I I I", "G G G S S J T L L L", "G G G G G J T T O O", "G G G G J J T L O O"],
    ["G G G G I I I I j j", "G G G T T T O O j T", "G G G G G J O O T T", "G G G G T J J J j T"],
    ["G G G G S S I I I I", "G G G S S T T T O O", "G G G G G T T J O O", "G G G G T T T J J J"],
    ["G G G G I I I I L L", "G G G T T T O O T L", "G G G G G J O O T T", "G G G G T J J J T L"],
    ["G G G G T J I I I I", "G G G T T J J J S S", "G G G G G O O J J J", "G G G G T O O S S J"],
    ["G G G G T T T J J J", "G G G Z Z T L L L J", "G G G G G J J J O O", "G G G G Z Z L J O O"],
    ["G G G G J J J L L L", "G G G T T T J L S S", "G G G G G O O J J J", "G G G G T O O S S J"],
    ["G G G G T L L L j j", "G G G T T L O O j T", "G G G G G J O O T T", "G G G G T J J J j T"],
    ["G G G G S S Z Z O O", "G G G S S T T T O O", "G G G G G T T J J J", "G G G G T T T Z Z J"],
    ["G G G G T S S Z O O", "G G G T T T Z Z O O", "G G G G G J J J O O", "G G G G S S Z J O O"],
    ["G G G G t t t Z O O", "G G G T T T Z Z O O", "G G G G G J J J O O", "G G G G T t Z J O O"],
    ["G G G G T O O J J J", "G G G T T I I I I J", "G G G G G J J J O O", "G G G G T O O J O O"],
    ["G G G G T J J I O O", "G G G T T J T I O O", "G G G G G T T I O O", "G G G G T J T I O O"],
    ["G G G G T S S T T T", "G G G T T T I I I I", "G G G G G Z Z J J J", "G G G G S S Z Z T J"],
]
