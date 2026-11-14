"""Pinned regression on banked evidence: literals vs pools, exact counts.

The fitted constants in calibration.py are claims about these files.
If a pool changes, this test — not a green suite — says so. Counts are
exact (failures, n), not rounded rates.
"""

import collections
import pickle

from src.models.pressing.calibration import (
    DECILE_EDGES_S,
    DECILE_INCOMPLETION_RATE,
    RANK_INCOMPLETION_RATE,
    decile_risk,
    margin_decile,
    rank_risk,
)

EDGES = list(DECILE_EDGES_S)


def _frozen_table(rows):
    bins = collections.defaultdict(lambda: [0, 0])
    for m, inc in rows:
        d = margin_decile(m)
        bins[d][0] += inc
        bins[d][1] += 1
    return bins


def _norm(rows):
    out = []
    for r in rows:
        if isinstance(r, dict):
            out.append((r["margin"], 0 if r["complete"] else 1))
        else:
            out.append((r[0], r[1]))
    return out


def test_wc2022_edges_reproduce_pinned_rates():
    five = pickle.load(open("data/pooled/frozen_five_leagues.pkl", "rb"))
    bins = _frozen_table(_norm(five["wc2022"]))
    # exact pinned counts: d1 856/4188, d10 9/4114
    assert (bins[1][0], bins[1][1]) == (856, 4188)
    assert (bins[10][0], bins[10][1]) == (9, 4114)
    # literals track the pool within 3e-3 (d2/d3 fit-set rounding differs:
    # pool d2 0.130/d3 0.087 vs literals 0.131/0.085 — the fit ran on a
    # cut the banked pool does not reproduce exactly; shape holds).
    for d in range(1, 11):
        got = bins[d][0] / bins[d][1]
        assert abs(got - DECILE_INCOMPLETION_RATE[d - 1]) < 3e-3
        assert abs(got - decile_risk(d)) < 3e-3


def test_rank_literals_reproduce_wc2022_curve():
    five = pickle.load(open("data/pooled/frozen_five_leagues.pkl", "rb"))
    by_rank = collections.defaultdict(lambda: [0, 0])
    for r in five["wc2022"]:
        d = min(r["rank"], 7)
        by_rank[d][0] += 0 if r["complete"] else 1
        by_rank[d][1] += 1
    for d in range(8):
        got = by_rank[d][0] / by_rank[d][1]
        assert abs(got - RANK_INCOMPLETION_RATE[d]) < 5e-4
        assert abs(got - rank_risk(d)) < 5e-4


def test_canonical_targeted_pool_shape():
    frozen, live = pickle.load(
        open("data/pooled/skillcorner_targeted_frozen_live.pkl", "rb")
    )
    assert len(frozen) == len(live) == 14822
    bins = _frozen_table(frozen)
    # frozen-edge d1 on canonical pool: 1948/8645
    assert (bins[1][0], bins[1][1]) == (1948, 8645)
    # base incompletion both margins: 2337/14822 = 0.1577 ("16%")
    assert sum(inc for _, inc in frozen) == 2337
    assert sum(inc for _, inc in live) == 2337
