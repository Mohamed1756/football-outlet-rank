"""Metrica loader tests: hand-built CSV slices, hand-computed values."""

import csv

import pytest

from src.io.metrica import (
    _ball_speed,
    _read_ball,
    _read_passes,
    _read_tracking,
    _velocity,
    load_passes,
)


def _write(path, rows):
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(rows)


@pytest.fixture()
def tracking_files(tmp_path):
    """3 frames: stander, runner (5.25 m/s in x), ball at 15.75 m/s."""
    header = [
        ["", "", "", "Home", "", "Home", "", "", ""],
        ["", "", "", "11", "", "1", "", "", ""],
        ["Period", "Frame", "Time [s]", "Player11", "", "Player1", "", "Ball", ""],
    ]
    frames = [
        ["1", "1", "0.04", "0.5", "0.5", "0.498", "0.5", "0.300", "0.5"],
        ["1", "2", "0.08", "0.5", "0.5", "0.500", "0.5", "0.306", "0.5"],
        ["1", "3", "0.12", "0.5", "0.5", "0.502", "0.5", "0.312", "0.5"],
    ]
    home = tmp_path / "home.csv"
    _write(str(home), header + frames)
    events = tmp_path / "events.csv"
    _write(
        str(events),
        [
            [
                "Team",
                "Type",
                "Subtype",
                "Period",
                "Start Frame",
                "Start Time [s]",
                "End Frame",
                "End Time [s]",
                "From",
                "To",
                "Start X",
                "Start Y",
                "End X",
                "End Y",
            ],
            [
                "Home",
                "PASS",
                "",
                "1",
                "1",
                "0.04",
                "3",
                "0.12",
                "Player11",
                "Player1",
                "0.5",
                "0.5",
                "0.6",
                "0.5",
            ],
        ],
    )
    return str(home), str(events)


def test_tracking_positions_scale_to_meters(tracking_files):
    home, _ = tracking_files
    frames = _read_tracking(home)
    assert frames[2]["Player11"] == pytest.approx((52.5, 34.0))
    assert frames[2]["Player1"] == pytest.approx((52.5, 34.0))


def test_velocity_is_central_difference(tracking_files):
    home, _ = tracking_files
    frames = _read_tracking(home)
    # (0.502 - 0.498) * 105 / 0.08 s = 5.25 m/s closing run.
    vx, vy = _velocity(frames, 2, "Player1")
    assert vx == pytest.approx(5.25, abs=0.01)
    assert vy == pytest.approx(0.0, abs=1e-9)
    # stander has zero velocity
    assert _velocity(frames, 2, "Player11") == (0.0, 0.0)
    # edges with no neighbor return zero, not an error
    assert _velocity(frames, 1, "Player1") == (0.0, 0.0)


def test_ball_speed_is_peak_over_window(tracking_files):
    home, _ = tracking_files
    ball = _read_ball(home)
    assert _ball_speed(ball, 1, 3) == pytest.approx(15.75, abs=0.01)


def test_ball_spike_capped_at_shot_max():
    assert _ball_speed({1: (0.0, 0.0), 2: (43.0, 0.0)}, 1, 2) == 35.0


def test_pass_parses_with_measured_speed(tracking_files):
    home, events = tracking_files
    passes = _read_passes(events)
    assert len(passes) == 1
    p = passes[0]
    assert p.passer == "Player11"
    assert p.start_frame == 1 and p.end_frame == 3
    assert (p.end_pos_m.x, p.end_pos_m.y) == pytest.approx((63.0, 34.0))


def test_load_passes_pairs_actors(tracking_files):
    home, events = tracking_files
    out = load_passes(home, home, events)
    assert len(out) == 1
    p, actors = out[0]
    assert p.ball_speed_ms == pytest.approx(15.75, abs=0.01)
    names = {a.pos_m.x for a in actors}
    assert len(actors) == 4  # 2 players x 2 team files


def test_assign_sides_picks_nearest_to_end():
    from src.core.geometry import PitchPoint
    from src.io.metrica import assign_sides
    from src.models.pressing.types import PressingActor

    def actor(tid, team, x):
        return PressingActor(track_id=tid, team_id=team, pos_m=PitchPoint(x, 34.0))

    actors = [actor(0, "home", 80.0), actor(1, "away", 50.0)]
    rec, opp = assign_sides(actors, PitchPoint(85.0, 34.0))
    assert [a.team_id for a in rec] == ["home"]
    assert [a.team_id for a in opp] == ["away"]
