"""Rank-space calibration: margin decile -> incompletion rate.

Absolute margins from frozen 360 shape are inflated (standing starts both
sides, no live pace), so the honest unit is rank: which outlets are tighter
than which. Fitted on 41,561 WC2022 completed/incomplete ground passes:

- bottom decile (margin <= ~1.0 s): 20.4% incompletion
- top decile (margin >= ~2.5 s): 0.2% incompletion
- ~93x failure gradient, monotone across all 10 deciles
- gradient holds within short/mid/long pass-length terciles (not a proxy)

Passers choose the safest outlet ~44% of the time on WC2022
(0.41-0.44 across the five 360 leagues); incompletion rises
with chosen rank (0.024 at rank 0 -> ~0.23 at rank 6+, rank 7 pooled).
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from src.core.geometry import PITCH_LENGTH_M

# Decile upper edges (seconds) from the WC2022 fit, fitted values.
# Boundaries are descriptive of the calibration sample, not physics.
DECILE_EDGES_S: Tuple[float, ...] = (
    1.01,
    1.31,
    1.52,
    1.70,
    1.85,
    1.99,
    2.13,
    2.29,
    2.50,
    float("inf"),
)

# Observed incompletion rate per decile (index 0 = tightest).
DECILE_INCOMPLETION_RATE: Tuple[float, ...] = (
    0.204,
    0.131,
    0.085,
    0.049,
    0.033,
    0.023,
    0.016,
    0.009,
    0.006,
    0.002,
)

# Observed incompletion rate by chosen rank (0 = safest outlet).
# Rank 7 pools ranks 7+ (260 plays: 7:200, 8:56, 9:4).
RANK_INCOMPLETION_RATE: Tuple[float, ...] = (
    0.024,
    0.043,
    0.075,
    0.107,
    0.149,
    0.183,
    0.212,
    0.235,
)


@dataclass(frozen=True)
class OutletRank:
    margin_s: float
    rank: int
    n_outlets: int


def rank_outlets(margins_s: Sequence[float]) -> List[OutletRank]:
    """Rank outlets tightest-last: rank 0 is the safest (largest margin).

    Equal margins share no rank: ties break by input order (stable sort,
    first-listed tightest-ranked). No tie rule is inferred — callers that
    need tied ranks must quantize margins before calling.
    """
    order = sorted(range(len(margins_s)), key=lambda i: margins_s[i], reverse=True)
    ranks: List[OutletRank] = [None] * len(margins_s)  # type: ignore[list-item]
    for rank, idx in enumerate(order):
        ranks[idx] = OutletRank(
            margin_s=margins_s[idx], rank=rank, n_outlets=len(margins_s)
        )
    return ranks


def margin_decile(margin_s: float) -> int:
    """Decile bin (1-10) for a margin; 1 is tightest.

    Rejects non-finite input and the -99.0 unscorable sentinel: binning
    unscorable as decile 1 ("tightest, risk 0.204") is the silent-safe
    failure this instrument exists to prevent. Callers score unscorable
    via the margin_s == -99.0 check (see risk_surface), never via decile.
    """

    if not math.isfinite(margin_s) or margin_s <= -99.0:
        raise ValueError(f"margin_decile needs a scored margin, got {margin_s}")
    for i, edge in enumerate(DECILE_EDGES_S):
        if margin_s <= edge:
            return i + 1
    return 10


def decile_risk(decile: int, pace_k: float = 1.0) -> float:
    """Fitted incompletion rate for a margin decile (1-10).

    pace_k scales the WC2022 rate for a slower/faster environment as a
    descriptive level shift, not physics: WWC 2023 fails ~1.5x the WC2022
    rate at equal frozen-shape margin (0.27 vs 0.20 bottom decile). Edges
    stay frozen; only levels move. Capped at 1.0, so ordering holds
    strictly below saturation — at high k the top deciles tie at 1.0
    (weak ordering, distinct margins identical risk).
    """
    if not 1 <= decile <= 10:
        raise ValueError(f"decile must be 1-10, got {decile}")
    return min(1.0, DECILE_INCOMPLETION_RATE[decile - 1] * pace_k)


def rank_risk(rank: int) -> float:
    """Fitted incompletion rate for a chosen rank (0 = safest, 7+ pooled)."""
    if rank < 0:
        raise ValueError(f"rank must be >= 0, got {rank}")
    return RANK_INCOMPLETION_RATE[min(rank, 7)]


def outlet_value(
    retention_prob: float, intercept_x_m: float, attack_sign: float = 1.0
) -> float:
    """Safety-times-upside for one outlet: retention probability at the
    intercept times forward progress (attack-direction x over pitch length).
    intercept_x_m is where the ball is received in corner-origin meters,
    not where the target stands at decision time: on tracking data use
    the reception point, on frozen shape the computed intercept.
    attack_sign=+1 attacks left-to-right (canonical), -1 the reverse:
    callers with unnormalized ends (Metrica keeps raw period orientation)
    pass -1 for second-half attacks instead of silently scoring the wrong
    half. Inputs outside [0, pitch length] are a caller error, scored at
    the boundary with a stderr warning (off-pitch or behind-goal x can
    only come from a bad intercept or flipped ends). attack_sign != +/-1
    raises ValueError.
    Rank-0-by-margin is safest; rank-0-by-value is the safest
    progressive ball. Descriptive reordering aid, not a fitted
    outcome model.
    """
    if attack_sign not in (1.0, -1.0):
        raise ValueError(f"attack_sign must be +1 or -1, got {attack_sign}")
    x = intercept_x_m if attack_sign == 1.0 else PITCH_LENGTH_M - intercept_x_m
    if not 0.0 <= x <= PITCH_LENGTH_M:
        print(
            f"outlet_value: intercept_x_m={intercept_x_m} outside "
            f"[0, {PITCH_LENGTH_M}]: clipped to boundary",
            file=sys.stderr,
        )
    progress = min(1.0, max(0.0, x / PITCH_LENGTH_M))
    return round(retention_prob * progress, 4)
