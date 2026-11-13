"""Reproduce headline tables from banked evidence (no tracking needed).

Bins use frozen WC2022 edges throughout, so IDSSE rates differ from the
note's pooled-decile figures (same shape, different binning).
"""
import collections
import glob
import json
import math
import pickle

import numpy as np

import sys

sys.path.insert(0, ".")

EDGES = [1.01, 1.31, 1.52, 1.70, 1.85, 1.99, 2.13, 2.29, 2.50]


def decile(m):
    for i, e in enumerate(EDGES):
        if m <= e:
            return i + 1
    return 10


def table(rows, title):
    bins = collections.defaultdict(lambda: [0, 0])
    for m, inc in rows:
        bins[decile(m)][0] += inc
        bins[decile(m)][1] += 1
    print(title)
    for d in range(1, 11):
        f, n = bins[d]
        print(f"  d{d}: fail={f/max(n,1):.3f} n={n}")


def main():
    frozen, live = pickle.load(open("data/pooled/skillcorner_frozen_live.pkl", "rb"))
    print(f"SkillCorner frozen (n={len(frozen)}):")
    table(frozen, "")
    print("same margins, live pressers:")
    table(live, "")
    both = pickle.load(open("data/pooled/idsse_measured_all_1160.pkl", "rb"))
    print(f"IDSSE measured (n={len(both)}):")
    table(both, "")
    print("Team fingerprints (base rate | median margin | n):")
    meta = json.load(open("data/pooled/match_teams.json"))
    teams = collections.defaultdict(list)
    fp = pickle.load(open("data/pooled/skillcorner_team_margins.pkl", "rb"))
    for (mid, side), rows in fp.items():
        if mid not in meta:
            continue
        teams[meta[mid][side]].extend(rows)
    for t, rows in sorted(teams.items()):
        n = len(rows)
        base = sum(x[1] for x in rows) / n
        med = sorted(x[0] for x in rows)[n // 2]
        print(f"  {t}: fail={base:.3f} med={med:.2f} n={n}")
    print("Drag rematch (median |AE| vs measured flight, strand rate):")
    from src.models.pressing.arrival import flight_time_s

    R = pickle.load(open("data/pooled/idsse_reception_speeds.pkl", "rb"))
    for name, fn in [
        ("coulomb22", lambda d, v: flight_time_s(d, 22.0)),
        ("coulomb_meas", lambda d, v: flight_time_s(d, v)),
    ]:
        err, inf = [], 0
        for d, v, t in R:
            p = fn(d, v)
            if math.isfinite(p):
                err.append(abs(p - t))
            else:
                inf += 1
        print(f"  {name}: medAE={np.median(err):.2f}s strand={inf/len(R):.3f}")


if __name__ == "__main__":
    main()
