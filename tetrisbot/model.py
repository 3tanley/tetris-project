"""The advisor's learned prior: how often each setup is the one that actually gets built.

While a setup is only partly built, several templates usually still fit the pieces on the
board (the first I or L of an opener belongs to many of them). The recognizer
(coach.Coach) keeps all of them and ranks them by this prior until the next pieces
narrow it down.

Training data comes from two places:
  * self-play: the simulator runs the bot (which picks setups with the planner, from
    random 7-bag orders) and counts every setup it finishes  -> "sim".
    Each opener family gets the same number of games (only that opener switched on), and
    the counts are stored as a share (percent) of their own kind - same family and stage,
    e.g. "MS2 2nd-bag setup C: 30% of MS2 2nd bags". So the prior learns which variant of
    a family / which DPC gets built, not which family: a family whose loop finishes more
    setups per game doesn't outweigh the others. Which family is the user's choice.
  * the user: every setup the advisor sees the user finish  -> "user". Each one adds
    USER_WEIGHT points, so the display leans toward the setups this player uses.

    python -m tetrisbot --train 42      # 7 self-play games per opener -> model/setup_prior.json
"""
import json
import os
import time
from collections import Counter

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model", "setup_prior.json")
USER_WEIGHT = 20


class SetupPrior:
    def __init__(self, sim=None, user=None, path=PATH):
        self.sim = Counter(sim or {})
        self.user = Counter(user or {})
        self.path = path

    def score(self, name):
        """Relative weight of a template (smoothed: unseen setups still count)."""
        return 1 + self.sim[name] + USER_WEIGHT * self.user[name]

    def learn(self, name, save=True):
        """The user finished `name`."""
        self.user[name] += 1
        if save:
            self.save()

    def save(self):
        if not self.path:
            return
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"sim": dict(self.sim), "user": dict(self.user)}, f, indent=1, sort_keys=True)
        os.replace(tmp, self.path)

    @classmethod
    def load(cls, path=PATH):
        try:
            with open(path) as f:
                d = json.load(f)
            return cls(d.get("sim"), d.get("user"), path)
        except (OSError, ValueError):
            return cls(path=path)


def share_of_kind(counts):
    """Counts -> percent of all finished setups of the same family and stage."""
    from . import templates as T
    kind = {t.name: (t.family, t.stage) for ts in T.library().values() for t in ts}
    total = Counter()
    for name, n in counts.items():
        total[kind.get(name)] += n
    return {name: round(100.0 * n / total[kind.get(name)], 1) for name, n in counts.items()}


def train(games=42, pieces=150, seed=1000, path=PATH, log=print):
    """Self-play in the simulator; count the setups the bot finishes. Keeps the user counts
    already in the file."""
    from . import planner, sim, templates as T
    from .brain import Brain, Lookahead
    from .handling import Handling

    old = planner.SETTINGS["handling"]
    h = Handling.load()
    fams = T.FAMILY_PRIORITY
    counts = Counter()
    t0 = time.time()
    try:
        for k in range(games):
            h.openers = fams[k % len(fams)]          # same number of games for every opener
            planner.configure(h, safe=False)
            g = sim.Game(seed + k)
            br = Brain(log=lambda *a: None, lookahead=Lookahead(threaded=False))
            br.bag.reset(aligned=True)
            for _ in range(pieces):
                step = br.decide(g.board, g.current, g.hold, g.visible())
                if step is None:
                    break
                _, cleared, _, hold_was_empty = g.apply(step)
                br.on_lock(step, hold_was_empty, cleared, g.board)
                if g.board.height() > 20:
                    break
            counts.update(br.built)
            log(f"[train] game {k + 1}/{games} ({h.openers}): {sum(br.built.values())} setups, "
                f"{br.stats.get('pc', 0)} PCs ({time.time() - t0:.0f} s)")
    finally:
        planner.configure(old, safe=False)
    prior = SetupPrior.load(path)
    prior.sim = Counter(share_of_kind(counts))
    prior.save()
    log(f"[train] {sum(counts.values())} finished setups, {len(counts)} different -> {path}")
    return prior
