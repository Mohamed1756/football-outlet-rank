"""Arrival-time pressing core (team-agnostic, no CV)."""

from src.models.pressing.types import PressingActor
from src.models.pressing.arrival import (
    arrival_margin,
    flight_time_s,
    intercept_target,
    presser_arrival_s,
    presser_engagement_latency_s,
    ArrivalResult,
)
from src.models.pressing.readiness import receiver_readiness, ReadinessResult
from src.models.pressing.calibration import (
    decile_risk,
    margin_decile,
    outlet_value,
    rank_outlets,
    rank_risk,
    OutletRank,
)

__all__ = [
    "PressingActor",
    "arrival_margin",
    "flight_time_s",
    "intercept_target",
    "presser_arrival_s",
    "presser_engagement_latency_s",
    "ArrivalResult",
    "receiver_readiness",
    "ReadinessResult",
    "decile_risk",
    "margin_decile",
    "outlet_value",
    "rank_outlets",
    "rank_risk",
    "OutletRank",
]
