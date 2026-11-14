"""Reproduce headline tables from banked evidence (no tracking needed).

Frozen-edge table: the same absolute margin everywhere (WC2022 edges),
portable seconds. Headline gradients in arrival.md/fig1 use pooled
deciles instead (each pool's own tenths, portable shape) — see
data/pooled/README.md "Binning rule". Values here and headline d1
0.244 (SkillCorner) / d1 0.40 (IDSSE) are the two binnings of the
same pools, not competing claims.
"""

import collections
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
        print(f"  d{d}: fail={f / max(n, 1):.3f} n={n}")


def main():
    frozen, live = pickle.load(
        open("data/pooled/skillcorner_targeted_frozen_live.pkl", "rb")
    )
    print(f"SkillCorner targeted canonical (n={len(frozen)}):")
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
        print(f"  {name}: medAE={np.median(err):.2f}s strand={inf / len(R):.3f}")


if __name__ == "__main__":
    main()
