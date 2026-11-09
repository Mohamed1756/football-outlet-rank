"""Arrival-race tests: hand-computed kinematics, no plausibility asserts."""

import math

import pytest

from src.core.geometry import PitchPoint
from src.models.pressing.arrival import (
    arrival_margin,
    flight_time_s,
    lead_target,
    presser_arrival_s,
)
from src.models.pressing.types import PressingActor


def _actor(tid, x, y, vx=0.0, vy=0.0, team="opp", valid=True):
    return PressingActor(
        track_id=tid,
        team_id=team,
        pos_m=PitchPoint(x=x, y=y),
        vel_ms=(vx, vy),
        pitch_valid=valid,
    )


def test_flight_time_scales_with_turf_friction():
    # dist = 22t - 1.225t^2: t10 = (22 - sqrt(484 - 24.5)) / 2.45 ~ 0.467
    t10 = flight_time_s(10.0)
    assert t10 == pytest.approx(0.467, abs=1e-3)
    # t20 = (22 - sqrt(484 - 49)) / 2.45 ~ 0.960; t40 ~ 2.053
    t20 = flight_time_s(20.0)
    assert t20 == pytest.approx(0.960, abs=1e-3)
    t40 = flight_time_s(40.0)
    assert t40 == pytest.approx(2.053, abs=1e-3)
    assert t10 < t20 < t40


def test_flight_time_beyond_stopping_distance_is_no_ball():
    # Stopping distance = 22^2 / (2 * 2.45) ~ 98.8 m: ball never arrives
    assert flight_time_s(105.0) == math.inf
    assert flight_time_s(98.8) == math.inf


def test_lead_target_projects_velocity():
    tgt = lead_target(PitchPoint(x=80.0, y=30.0), (4.0, 0.0), 1.0)
    assert tgt.x == 84.0 and tgt.y == 30.0


def test_lead_target_caps_runaway_displacement():
    from src.physics.gk_constraints import MAX_LEAD_DISPLACEMENT_M

    tgt = lead_target(PitchPoint(x=80.0, y=30.0), (10.42, 0.0), 3.0)
    assert tgt.x - 80.0 == pytest.approx(MAX_LEAD_DISPLACEMENT_M, abs=1e-2)


def test_converging_3v1_is_trapped():
    rec = _actor(9, 86.0, 25.0, team="own")
    passer = PitchPoint(x=100.0, y=29.0)
    pressers = [
        _actor(1, 87.5, 26.5, vx=-4.0, vy=-2.0),
        _actor(2, 84.5, 23.5, vx=3.0, vy=2.0),
        _actor(3, 87.5, 23.0, vx=-3.0, vy=3.0),
    ]
    res = arrival_margin(rec, pressers, passer)
    assert res.margin_s < 0.0
    assert res.best_presser_id in (1, 2, 3)


def test_static_pressers_leave_positive_margin():
    rec = _actor(9, 86.0, 25.0, team="own")
    passer = PitchPoint(x=100.0, y=29.0)
    pressers = [_actor(1, 80.0, 40.0), _actor(2, 95.0, 50.0)]
    res = arrival_margin(rec, pressers, passer)
    assert res.margin_s > 0.5


def test_invalid_opponents_ignored():
    rec = _actor(9, 86.0, 25.0, team="own")
    passer = PitchPoint(x=100.0, y=29.0)
    pressers = [_actor(1, 86.5, 25.5, valid=False)]
    res = arrival_margin(rec, pressers, passer)
    assert res.best_presser_id is None
    assert res.t_press_s == 99.0


def test_margin_falls_as_presser_accelerates():
    rec = _actor(9, 86.0, 25.0, team="own")
    passer = PitchPoint(x=100.0, y=29.0)
    slow = arrival_margin(rec, [_actor(1, 90.0, 29.0, vx=-1.0)], passer)
    fast = arrival_margin(rec, [_actor(1, 90.0, 29.0, vx=-6.0)], passer)
    assert fast.margin_s < slow.margin_s


def test_endpoints_converge_ball_and_pressers_share_target():
    # Fixed-point invariant: the lead recomputed from the returned t_ball
    # must reproduce t_ball through the flight model. Old one-pass code left
    # up to 1.74 m endpoint gaps (15 m pass, 7 m/s receiver).
    rec = _actor(9, 80.0, 30.0, vx=7.0, vy=0.0, team="own")
    passer = PitchPoint(x=65.0, y=30.0)
    res = arrival_margin(rec, [], passer)
    recheck = lead_target(rec.pos_m, rec.vel_ms, res.t_ball_s)
    t_recheck = flight_time_s(math.hypot(recheck.x - passer.x, recheck.y - passer.y))
    assert t_recheck == pytest.approx(res.t_ball_s, abs=0.035)


def test_presser_running_away_does_not_count():
    away = presser_arrival_s(
        _actor(1, 88.0, 27.0, vx=6.0, vy=6.0), PitchPoint(x=86.0, y=25.0)
    )
    toward = presser_arrival_s(
        _actor(1, 88.0, 27.0, vx=-6.0, vy=-6.0), PitchPoint(x=86.0, y=25.0)
    )
    assert away[0] > toward[0]


def test_prep_latency_delays_ball_arrival_and_reduces_margin():
    rec = _actor(9, 80.0, 30.0, vx=2.0, vy=0.0, team="own")
    passer = PitchPoint(x=60.0, y=30.0)
    presser = _actor(1, 85.0, 30.0, vx=-3.0, vy=0.0)

    res_no_latency = arrival_margin(rec, [presser], passer, prep_latency_s=0.0)
    res_with_latency = arrival_margin(rec, [presser], passer, prep_latency_s=0.35)

    # Prep latency delays total ball arrival; the lead re-times (two-pass),
    # so the shift exceeds the raw 0.35 s by the extra lead distance
    assert res_with_latency.t_ball_s > res_no_latency.t_ball_s + 0.35
    assert res_with_latency.margin_s < res_no_latency.margin_s


def test_margin_times_ball_to_lead_not_stale_position():
    # Receiver sprinting at 5 m/s on a 30 m pass: stale timing underprices
    # the ball by ~0.42 s (1.49 vs 1.90), multiple retention thresholds
    rec = _actor(9, 80.0, 30.0, vx=5.0, vy=0.0, team="own")
    passer = PitchPoint(x=50.0, y=30.0)
    res = arrival_margin(rec, [], passer)
    stale = flight_time_s(30.0)
    assert res.t_ball_s > stale + 0.30


def test_ball_beyond_stopping_distance_is_trapped():
    rec = _actor(9, 5.0, 34.0, team="own")
    passer = PitchPoint(x=110.0, y=34.0)
    res = arrival_margin(rec, [_actor(1, 20.0, 34.0)], passer)
    assert res.margin_s == -99.0
    assert res.best_presser_id is None


def test_static_presser_burst_acceleration_kinematics():
    # Static defender at 3.0m away accelerates at 3.5 m/s^2
    # t = sqrt(2 * 3.0 / 3.5) = 1.309s (previously walked at 1.0 m/s taking 3.0s!)
    presser = _actor(1, 83.0, 30.0, vx=0.0, vy=0.0)
    t_arr, _ = presser_arrival_s(presser, PitchPoint(x=80.0, y=30.0))
    assert t_arr == pytest.approx(1.309, abs=1e-3)
    assert t_arr < 2.0  # Far faster than the 3.0s walking artifact


def _posed_actor(tid, x, y, facing_rad):
    return PressingActor(
        track_id=tid,
        team_id="opp",
        pos_m=PitchPoint(x=x, y=y),
        vel_ms=(0.0, 0.0),
        facing_rad=facing_rad,
        facing_source="pose",
    )


def test_engaged_presser_pays_only_plant():
    from src.models.pressing.arrival import presser_engagement_latency_s

    # Sprinting straight at the target: open body shape, foot plant only
    presser = _posed_actor(1, 80.0, 30.0, math.pi)
    lat, source = presser_engagement_latency_s(
        presser, PitchPoint(x=70.0, y=30.0)
    )
    assert source == "pose"
    assert lat <= 0.15


def test_back_turned_presser_pays_full_flip():
    from src.models.pressing.arrival import presser_engagement_latency_s

    # Facing +x, target at -x: 180-degree flip through the shared pivot curve
    presser = _posed_actor(1, 80.0, 30.0, 0.0)
    lat, _ = presser_engagement_latency_s(
        presser, PitchPoint(x=70.0, y=30.0)
    )
    assert lat == pytest.approx(0.70, abs=1e-3)


def test_unknown_orientation_pays_reaction_floor():
    from src.models.pressing.arrival import presser_engagement_latency_s
    from src.physics.gk_constraints import GK_REACTION_TIME_DEFAULT_S

    presser = _actor(1, 80.0, 30.0)
    lat, source = presser_engagement_latency_s(
        presser, PitchPoint(x=70.0, y=30.0)
    )
    assert source == "unknown"
    assert lat == GK_REACTION_TIME_DEFAULT_S


def test_engagement_latency_delays_arrival():
    presser = _actor(1, 83.0, 30.0, vx=0.0, vy=0.0)
    target = PitchPoint(x=80.0, y=30.0)
    base, _ = presser_arrival_s(presser, target)
    delayed, _ = presser_arrival_s(presser, target, engagement_latency_s=0.3)
    assert delayed == pytest.approx(base + 0.3, abs=1e-3)


def test_at_target_presser_keeps_engagement_latency():
    # Standing on the lead is the most dangerous geometry: arrival must still
    # price turn/reaction, not return 0. Zero displacement has no turn axis,
    # so the measured minimum (plant 0.15) applies.
    presser = _posed_actor(1, 80.0, 30.0, 0.0)
    t, d = presser_arrival_s(
        presser, PitchPoint(x=80.0, y=30.0), engagement_latency_s=0.3
    )
    assert d == 0.0
    assert t == pytest.approx(0.3, abs=1e-3)


def test_back_turned_pose_presser_arrives_later():
    rec = _actor(9, 86.0, 25.0, team="own")
    passer = PitchPoint(x=100.0, y=29.0)
    facing_away = _posed_actor(1, 88.0, 27.0, 0.0)
    facing_toward = _posed_actor(1, 88.0, 27.0, math.atan2(25.0 - 27.0, 86.0 - 88.0))
    away = arrival_margin(rec, [facing_away], passer)
    toward = arrival_margin(rec, [facing_toward], passer)
    assert away.t_press_s > toward.t_press_s


def test_gated_velocity_treated_as_stationary():
    from src.models.pressing.types import gate_tracking_velocity

    assert gate_tracking_velocity((10.42, 0.25), False) == ((0.0, 0.0), True)
    assert gate_tracking_velocity((2.0, 0.0), True) == ((0.0, 0.0), True)
    assert gate_tracking_velocity((2.0, 0.0), False) == ((2.0, 0.0), False)
