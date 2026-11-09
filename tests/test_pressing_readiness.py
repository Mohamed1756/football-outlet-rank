"""Tests for receiver readiness body model (hand-verified angles)."""

import math
import pytest

from src.core.geometry import PitchPoint
from src.models.pressing.readiness import (
    receiver_readiness,
    resolve_facing,
)
from src.models.pressing.types import PressingActor


def _actor(tid, x, y, facing=None, source="pose", vx=0.0, vy=0.0, team="own"):
    return PressingActor(
        track_id=tid,
        team_id=team,
        pos_m=PitchPoint(x=x, y=y),
        vel_ms=(vx, vy),
        facing_rad=facing,
        facing_source=source,
    )


def test_open_cb_ready_now():
    rec = _actor(4, 80.0, 30.0, facing=0.0)
    res = receiver_readiness(rec, PitchPoint(x=100.0, y=29.0))
    assert res.turn_latency_s == 0.15
    assert res.readiness_mult == 1.0
    assert res.facing_source == "pose"
    assert res.note == "open"


def test_back_to_passer_prices_turn_not_veto():
    rec = _actor(4, 80.0, 29.0, facing=math.pi)
    res = receiver_readiness(rec, PitchPoint(x=100.0, y=29.0))
    assert res.turn_latency_s == 0.70
    assert res.readiness_mult == 0.35
    assert "needs-turn" in res.note


def test_back_to_presser_shields():
    rec = _actor(9, 86.0, 25.0, facing=-3.0 * math.pi / 4.0)
    presser = _actor(21, 88.0, 27.0, team="opp")
    res = receiver_readiness(rec, PitchPoint(x=100.0, y=29.0), nearest_presser=presser)
    assert "shielded" in res.note
    assert res.readiness_mult > 0.35


def test_chest_open_to_closing_presser_exposed():
    rec = _actor(9, 86.0, 25.0, facing=0.0)
    presser = _actor(21, 90.0, 25.0, team="opp")
    res = receiver_readiness(
        rec,
        PitchPoint(x=100.0, y=29.0),
        nearest_presser=presser,
        presser_closing=True,
    )
    assert "exposed" in res.note
    assert res.readiness_mult == round(1.0 * 0.80, 3)


def test_facing_fallback_chain():
    moving = _actor(7, 80.0, 30.0, facing=None, vx=3.0, vy=0.0)
    assert resolve_facing(moving)[1] == "velocity"
    static = _actor(7, 80.0, 30.0, facing=None)
    angle, source = resolve_facing(static, PitchPoint(x=100.0, y=30.0))
    assert source == "ball"
    assert angle == 0.0
    lost = _actor(7, 80.0, 30.0, facing=None)
    res = receiver_readiness(lost, PitchPoint(x=80.0, y=10.0))
    assert res.facing_source == "unknown"
    assert res.readiness_mult == round(1.0 * 0.85, 3)


def test_reception_latency_and_post_cushion():
    from src.physics.gk_constraints import (
        MIN_POST_RECEIPT_CUSHION_S,
        RECEIVER_FIRST_TOUCH_LATENCY_S,
    )

    rec = _actor(4, 80.0, 30.0, facing=0.0)
    res = receiver_readiness(rec, PitchPoint(x=100.0, y=29.0))
    expected_reception = round(RECEIVER_FIRST_TOUCH_LATENCY_S + res.turn_latency_s, 3)
    assert res.reception_latency_s == expected_reception

    # Margin shorter than reception commitment yields negative or sub-threshold post-cushion
    short_margin_s = expected_reception + 0.10
    assert res.post_cushion_s(short_margin_s) == pytest.approx(0.10, abs=1e-3)
    assert res.post_cushion_s(short_margin_s) < MIN_POST_RECEIPT_CUSHION_S

    # Generous margin leaves ample control cushion
    wide_margin_s = expected_reception + 0.80
    assert res.post_cushion_s(wide_margin_s) >= MIN_POST_RECEIPT_CUSHION_S


def test_hospital_pass_margin_math():
    from src.models.pressing.arrival import arrival_margin

    rec = _actor(10, 25.0, 34.0, facing=0.0)
    presser = PressingActor(
        track_id=21,
        team_id="opp",
        pos_m=PitchPoint(x=29.0, y=34.0),
        vel_ms=(-1.0, 0.0),
    )
    res = arrival_margin(rec, [presser], PitchPoint(x=25.0, y=34.0))
    assert res.margin_s > 0.0

    ready = receiver_readiness(rec, PitchPoint(x=10.0, y=34.0))
    assert ready.post_cushion_s(res.margin_s) < ready.reception_latency_s


def test_retention_probability_calibration():
    from src.physics.gk_constraints import RETENTION_CRITICAL_CUSHION_S

    ready = receiver_readiness(_actor(4, 80.0, 30.0, facing=0.0), PitchPoint(x=100.0, y=29.0))

    # Inflection point at critical cushion gives exactly 50%
    margin_at_inflection = ready.reception_latency_s + RETENTION_CRITICAL_CUSHION_S
    assert ready.retention_prob(margin_at_inflection) == pytest.approx(0.50, abs=1e-3)

    # Monotonicity and C^1 continuity across the physical cushion range
    steps = [round(-0.20 + i * 0.01, 3) for i in range(81)]  # [-0.20, +0.60]
    vals = [
        ready.retention_prob(ready.reception_latency_s + t) for t in steps
    ]

    for i in range(len(vals) - 1):
        assert vals[i] < vals[i + 1], "Retention must be strictly monotonic"
        delta = abs(vals[i + 1] - vals[i])
        assert delta < 0.05, f"Discontinuity detected: step jump of {delta:.4f}"
        assert 0.0 < vals[i] < 1.0, "Retention must stay strictly in (0, 1)"
