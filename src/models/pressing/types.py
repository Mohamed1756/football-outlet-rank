"""Arrival-race types: matched on team_id, never on names or colors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import math
from src.core.geometry import PitchPoint
from src.physics.arrival_constants import PRESSER_SPRINT_MAX_SPEED_MS


def gate_tracking_velocity(
    vel_ms: Tuple[float, float],
    speed_capped: bool = False,
) -> Tuple[Tuple[float, float], bool]:
    """Trust gate for tracker velocity. Speeds above a sustained elite sprint
    (teleport jitter, keyframe disagreement) or flagged capped carry no
    directional information, so the body is treated as stationary and the
    caller is told it was gated. Prior: genuine 8.5+ m/s buildup sprints are
    rarer than tracker spikes at these magnitudes (observed 8.8-10.5 m/s
    lateral jumps on standing players).
    """
    if speed_capped or math.hypot(*vel_ms) > PRESSER_SPRINT_MAX_SPEED_MS:
        return (0.0, 0.0), True
    return vel_ms, False


@dataclass(frozen=True)
class PressingActor:
    track_id: int
    team_id: str
    pos_m: PitchPoint
    vel_ms: Tuple[float, float] = (0.0, 0.0)
    facing_rad: Optional[float] = None
    facing_source: str = "unknown"
    speed_capped: bool = False
    pitch_valid: bool = True
    provider_id: str = ""
