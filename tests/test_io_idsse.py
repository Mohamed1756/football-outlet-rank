"""IDSSE loader tests: hand-built DFL XML slices, hand-computed values."""

import pytest

from src.io.idsse import (
    _ball_speed,
    _load_roster,
    _read_passes,
    _read_tracking,
    _velocity,
    assign_sides,
)

MATCH_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<PutDataRequest>
<MatchInformation>
<Teams>
<Team TeamId="H" Role="home">
<Players>
<Player PersonId="P1" Shortname="A" FirstName="A" LastName="A"/>
<Player PersonId="P2" Shortname="B" FirstName="B" LastName="B"/>
</Players>
</Team>
<Team TeamId="A" Role="away">
<Players>
<Player PersonId="P3" Shortname="C" FirstName="C" LastName="C"/>
</Players>
</Team>
</Teams>
</MatchInformation>
</PutDataRequest>
"""

EVENTS_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<PutDataRequest>
<Event EventId="1" EventTime="2022-10-15T11:01:29.320+00:00" X-Position="10.0" Y-Position="34.0" X-Source-Position="10.0" Y-Source-Position="34.0">
<Play Recipient="P2" Height="flat" Evaluation="successfullyCompleted" Player="P1" Team="H"/>
</Event>
<Event EventId="2" EventTime="2022-10-15T11:01:30.320+00:00" X-Position="20.0" Y-Position="34.0" X-Source-Position="20.0" Y-Source-Position="34.0">
<Play Recipient="P2" Height="high" Evaluation="successfullyCompleted" Player="P1" Team="H"/>
</Event>
<Event EventId="3" EventTime="2022-10-15T11:01:31.320+00:00" X-Position="20.0" Y-Position="34.0" X-Source-Position="20.0" Y-Source-Position="34.0">
<Play Recipient="P2" Height="flat" Evaluation="unknown" Player="P1" Team="H"/>
</Event>
</PutDataRequest>
"""


def _track_xml(frames):
    """frames: list of (N, [(pid, x, y)]); ball pid is 'BALL'."""
    parts = ['<?xml version="1.0" encoding="UTF-8" ?><PutDataRequest><Positions>']
    for n, plist in frames:
        for pid, x, y in plist:
            parts.append(
                f'<FrameSet PersonId="{pid}"><Frame N="{n}" '
                f'T="2022-10-15T11:01:29.320+00:00" X="{x}" Y="{y}" '
                f'D="0" S="0" A="0" M="1"/></FrameSet>'
            )
    parts.append("</Positions></PutDataRequest>")
    return "".join(parts)


@pytest.fixture()
def idsse_files(tmp_path):
    match = tmp_path / "match.xml"
    match.write_text(MATCH_XML)
    events = tmp_path / "events.xml"
    events.write_text(EVENTS_XML)
    # center-origin tracking: x=0 -> corner 52.5
    track = tmp_path / "track.xml"
    track.write_text(
        _track_xml(
            [
                (100, [("P1", 0.0, 0.0), ("P2", 5.0, 0.0), ("BALL", 0.0, 0.0)]),
                (101, [("P1", 0.0, 0.0), ("P2", 5.2, 0.0), ("BALL", 0.4, 0.0)]),
                (102, [("P1", 0.0, 0.0), ("P2", 5.4, 0.0), ("BALL", 0.8, 0.0)]),
            ]
        )
    )
    return str(track), str(events), str(match)


def test_roster_maps_sides(idsse_files):
    _, events, match = idsse_files
    length, width, teams, names = _load_roster(match)
    assert (length, width) == (105.0, 68.0)
    assert teams == {"P1": "home", "P2": "home", "P3": "away"}
    assert names["P1"] == "A"


def test_tracking_applies_center_offset(idsse_files):
    track, _, match = idsse_files
    _, _, teams, _ = _load_roster(match)
    frames, ball, stamps = _read_tracking(track, teams, 105.0, 68.0)
    # center x=0 -> corner 52.5; ball x=0.4 -> 52.9
    assert frames[100]["P1"] == pytest.approx((52.5, 34.0))
    assert ball[101] == pytest.approx((52.9, 34.0))


def test_passes_keep_flat_labeled_only(idsse_files):
    _, events, match = idsse_files
    _, _, teams, names = _load_roster(match)
    import datetime

    stamps = {100: datetime.datetime(2022, 10, 15, 11, 1, 29).timestamp()}
    passes = _read_passes(events, stamps, teams, names)
    assert len(passes) == 1  # high ball + unknown evaluation dropped
    p = passes[0]
    assert p.target_id == "P2"
    assert p.complete is True


def test_velocity_central_difference(idsse_files):
    track, _, match = idsse_files
    _, _, teams, _ = _load_roster(match)
    frames, _, _ = _read_tracking(track, teams, 105.0, 68.0)
    vx, vy = _velocity(frames, 101, "P2")
    # (5.4 - 5.0) m over 0.08 s = 5 m/s
    assert vx == pytest.approx(5.0, abs=0.01)
    assert vy == pytest.approx(0.0)


def test_ball_speed_peak_and_cap():
    assert _ball_speed(
        {100: (0.0, 0.0), 101: (0.6, 0.0), 102: (1.2, 0.0)}, 100
    ) == pytest.approx(15.0, abs=0.01)
    assert _ball_speed({100: (0.0, 0.0), 101: (43.0, 0.0)}, 100) == 35.0


def test_assign_sides_picks_nearest():
    from src.core.geometry import PitchPoint
    from src.models.pressing.types import PressingActor

    actors = [
        PressingActor(track_id=0, team_id="home", pos_m=PitchPoint(80, 34)),
        PressingActor(track_id=1, team_id="away", pos_m=PitchPoint(50, 34)),
    ]
    rec, opp = assign_sides(actors, PitchPoint(85, 34))
    assert [a.team_id for a in rec] == ["home"]


def test_assign_sides_rejects_unusable_sides():
    import pytest

    from src.core.geometry import PitchPoint
    from src.models.pressing.types import PressingActor

    with pytest.raises(ValueError):
        assign_sides([], PitchPoint(85, 34))
    with pytest.raises(ValueError):
        assign_sides(
            [PressingActor(track_id=0, team_id="home", pos_m=PitchPoint(80, 34))],
            PitchPoint(85, 34),
        )
