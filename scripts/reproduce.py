"""Reproduce headline tables from banked evidence (no tracking needed).

Bins use frozen WC2022 edges throughout, so IDSSE rates differ from the
note's pooled-decile figures (same shape, different binning).
"""
import pickle
import sys

sys.path.insert(0, ".")

EDGES = [1.01, 1.31, 1.52, 1.70, 1.85, 1.99, 2.13, 2.29, 2.50]


def decile(m):
    for i, e in enumerate(EDGES):
        if m <= e:
            return i + 1
    return 10


def table(rows, title):
    from collections import defaultdict

    bins = defaultdict(lambda: [0, 0])
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
    both = pickle.load(open("data/pooled/idsse_measured_live.pkl", "rb"))
    print(f"IDSSE measured (n={len(both)}):")
    table(both, "")


if __name__ == "__main__":
    main()
