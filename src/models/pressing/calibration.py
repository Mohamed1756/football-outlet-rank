"""Rank-space calibration: margin decile -> incompletion rate.

Absolute margins from frozen 360 shape are inflated (standing starts both
sides, no live pace), so the honest unit is rank: which outlets are tighter
than which. Fitted on 41,561 WC2022 completed/incomplete ground passes:

- bottom decile (margin <= ~1.0 s): 20.4% incompletion
- top decile (margin >= ~2.5 s): 0.2% incompletion
- ~100x failure gradient, monotone across all 10 deciles
- gradient holds within short/mid/long pass-length terciles (not a proxy)

Passers choose the safest outlet 44% of the time; incompletion rises
monotonically with chosen rank (0.024 at rank 0 -> ~0.21 at rank 6+).
"""

from __future__ import annotations

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
# Ranks 7+ pooled (n < 300 each).
RANK_INCOMPLETION_RATE: Tuple[float, ...] = (
    0.024,
    0.043,
    0.075,
    0.107,
    0.149,
    0.183,
    0.212,
    0.208,
)


@dataclass(frozen=True)
class OutletRank:
    margin_s: float
    rank: int
    n_outlets: int


def rank_outlets(margins_s: Sequence[float]) -> List[OutletRank]:
    """Rank outlets tightest-last: rank 0 is the safest (largest margin)."""
    order = sorted(range(len(margins_s)), key=lambda i: margins_s[i], reverse=True)
    ranks: List[OutletRank] = [None] * len(margins_s)  # type: ignore[list-item]
    for rank, idx in enumerate(order):
        ranks[idx] = OutletRank(
            margin_s=margins_s[idx], rank=rank, n_outlets=len(margins_s)
        )
    return ranks


def margin_decile(margin_s: float) -> int:
    """Decile bin (1-10) for a margin; 1 is tightest."""
    for i, edge in enumerate(DECILE_EDGES_S):
        if margin_s <= edge:
            return i + 1
    return 10


def decile_risk(decile: int, pace_k: float = 1.0) -> float:
    """Fitted incompletion rate for a margin decile (1-10).

    pace_k scales the WC2022 rate for a slower/faster environment as a
    descriptive level shift, not physics: WWC 2023 fails ~1.5x the WC2022
    rate at equal frozen-shape margin (0.27 vs 0.20 bottom decile). Edges
    stay frozen; only levels move. Capped at 1.0.
    """
    if not 1 <= decile <= 10:
        raise ValueError(f"decile must be 1-10, got {decile}")
    return min(1.0, DECILE_INCOMPLETION_RATE[decile - 1] * pace_k)


def rank_risk(rank: int) -> float:
    """Fitted incompletion rate for a chosen rank (0 = safest, 7+ pooled)."""
    if rank < 0:
        raise ValueError(f"rank must be >= 0, got {rank}")
    return RANK_INCOMPLETION_RATE[min(rank, 7)]


def outlet_value(retention_prob: float, target_x_m: float) -> float:
    """Safety-times-upside for one outlet: retention probability at the
    intercept times forward progress (intercept x over pitch length).
    Inputs outside [0, pitch length] clip silently to [0, 1]: off-pitch
    or behind-goal x is a caller error, scored as boundary, never raised.
    Rank-0-by-margin is safest; rank-0-by-value is the safest
    progressive ball. Descriptive reordering aid, not a fitted
    outcome model.
    """
    progress = min(1.0, max(0.0, target_x_m / PITCH_LENGTH_M))
    return round(retention_prob * progress, 4)
