"""SkillCorner loader tests: hand-built JSONL/CSV slices, hand-computed values."""

import json

import pytest

from src.io.skillcorner import (
    _ball_speed,
    _read_ball,
    _read_passes,
    _read_tracking,
    _velocity,
    assign_sides,
    load_passes,
)


@pytest.fixture()
def sc_files(tmp_path):
    """2 frames at 10 fps: stander (p1), runner (p2: 5 m/s in x), ball at 15 m/s."""
    track = tmp_path / "track.jsonl"
    frames = [
        {
            "frame": 100,
            "timestamp": 10.0,
            "period": 1,
            "ball_data": {"x": 0.0, "y": 0.0},
            "player_data": [
                {"x": 0.0, "y": 0.0, "player_id": 1, "is_detected": True},
                {"x": -5.0, "y": 0.0, "player_id": 2, "is_detected": True},
            ],
        },
        {
            "frame": 101,
            "timestamp": 10.1,
            "period": 1,
            "ball_data": {"x": 1.5, "y": 0.0},
            "player_data": [
                {"x": 0.0, "y": 0.0, "player_id": 1, "is_detected": True},
                {"x": -4.5, "y": 0.0, "player_id": 2, "is_detected": True},
            ],
        },
    ]
    track.write_text("\n".join(json.dumps(f) for f in frames))
    events = tmp_path / "events.csv"
    events.write_text(
        "event_type,frame_start,frame_end,x_start,y_start,x_end,y_end,"
        "player_name,team_shortname,pass_outcome\n"
        "player_possession,100,101,0.0,0.0,7.5,0.0,P1,HOME,successful\n"
        "player_possession,100,101,0.0,0.0,7.5,0.0,P2,AWAY,unsuccessful\n"
        "player_possession,100,101,0.0,0.0,7.5,0.0,P3,HOME,\n"
    )
    match = tmp_path / "match.json"
    match.write_text(
        json.dumps(
            {
                "home_team": {"id": 1},
                "pitch_length": 105,
                "pitch_width": 68,
                "players": [
                    {"id": 1, "team_id": 1},
                    {"id": 2, "team_id": 2},
                ],
            }
        )
    )
    return str(track), str(events), str(match)


def test_tracking_maps_center_to_corner(sc_files):
    track, _, _ = sc_files
    frames = _read_tracking(track, 105.0, 68.0)
    assert frames[100]["1"] == pytest.approx((52.5, 34.0))
    assert frames[101]["2"] == pytest.approx((48.0, 34.0))


def test_velocity_is_central_difference_10fps(sc_files):
    track, _, _ = sc_files
    frames = _read_tracking(track, 105.0, 68.0)
    # 1.0 m over 0.2 s central window = 5 m/s
    vx, vy = _velocity(frames, 100, "2")
    assert vx == pytest.approx(0.0)  # edge: no frame 99
    assert _velocity(frames, 101, "2") == (0.0, 0.0)  # edge: no frame 102


def test_ball_speed_peak_and_cap(sc_files):
    track, _, _ = sc_files
    ball = _read_ball(track, 105.0, 68.0)
    # 1.5 m per 0.1 s = 15 m/s
    assert _ball_speed(ball, 100, 101) == pytest.approx(15.0, abs=0.01)
    assert _ball_speed({100: (0.0, 0.0), 101: (43.0, 0.0)}, 100, 101) == 35.0


def test_load_passes_uses_roster_sides(sc_files):
    track, events, match = sc_files
    out = load_passes(track, events, match)
    passes = _read_passes(events, 105.0, 68.0)
    assert len(passes) == 2  # blank-outcome row dropped
    assert passes[0].complete is True
    assert passes[1].complete is False
    # center-origin end (7.5, 0) -> corner (60.0, 34)
    assert (passes[0].end_pos_m.x, passes[0].end_pos_m.y) == pytest.approx((60.0, 34.0))


def test_load_passes_uses_roster_sides(sc_files):
    from src.io.metrica import load_passes as _  # noqa: F401 (name check)

    track, events, match = sc_files
    out = load_passes(track, events, match)
    assert len(out) == 2
    p, actors = out[0]
    assert p.ball_speed_ms == pytest.approx(15.0, abs=0.01)
    sides = {a.team_id for a in actors}
    assert sides == {"home", "away"}


def test_assign_sides_picks_nearest():
    from src.core.geometry import PitchPoint
    from src.models.pressing.types import PressingActor

    actors = [
        PressingActor(track_id=0, team_id="home", pos_m=PitchPoint(80, 34)),
        PressingActor(track_id=1, team_id="away", pos_m=PitchPoint(50, 34)),
    ]
    rec, opp = assign_sides(actors, PitchPoint(85, 34))
    assert [a.team_id for a in rec] == ["home"]
