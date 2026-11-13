"""Risk surface: expected incompletion per pitch cell for a frozen frame.

Pure composition: arrival_margin per cell (static hypothetical receiver)
mapped through decile_risk with the environment's pace_k. Answers "where
is it safe to receive" in absolute risk, comparable across environments.
Not rank: cells have no choice set, only margins.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.core.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, PitchPoint
from src.models.pressing.arrival import arrival_margin
from src.models.pressing.calibration import decile_risk, margin_decile
from src.models.pressing.types import PressingActor


@dataclass(frozen=True)
class RiskCell:
    x_m: float
    y_m: float
    margin_s: float
    risk: float


def risk_surface(
    passer: PitchPoint,
    opponents: List[PressingActor],
    nx: int = 21,
    ny: int = 14,
    pace_k: float = 1.0,
) -> List[RiskCell]:
    """Per-cell (margin, risk) over a coarse pitch grid.

    Hypothetical receiver stands static at each cell center; pressers run
    the frozen snapshot. pace_k re-scales levels per environment
    (1.0 = WC2022 calibration pace, ~1.5 = A-League broadcast pace).
    Same freeze, different k: colors shift, ordering does not.
    """
    cells: List[RiskCell] = []
    tid = 0
    for ix in range(nx):
        for iy in range(ny):
            x = (ix + 0.5) / nx * PITCH_LENGTH_M
            y = (iy + 0.5) / ny * PITCH_WIDTH_M
            probe = PressingActor(track_id=tid, team_id="own", pos_m=PitchPoint(x, y))
            tid += 1
            res = arrival_margin(probe, opponents, passer)
            if not res.margin_s > -99.0:
                continue
            dec = margin_decile(res.margin_s)
            cells.append(
                RiskCell(
                    x_m=x, y_m=y, margin_s=res.margin_s, risk=decile_risk(dec, pace_k)
                )
            )
    return cells
