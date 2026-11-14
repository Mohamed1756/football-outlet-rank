"""IDSSE live-data loader: DFL TRACAB tracking + synchronized events.

Bassek et al. 2025, Scientific Data 12:195 (doi:10.1038/s41597-025-04505-y):
7 Bundesliga 22/23 matches, 25 fps optical tracking with ball, CC-BY 4.0,
via Hugging Face pysport/idsse-data. DFL XML: match info (roster +
TeamId), raw events (Play with Recipient/Height/Evaluation), raw observed
positions (FrameSet per PersonId, X/Y meters, S = speed m/s).

Events join tracking by wall clock (EventTime to nearest Frame T).
FrameSets whose PersonId is on neither roster are the ball.

Sprint/turn/first-touch physics stay ours (arrival_constants.py);
everything about who/where/when comes from the dataset. Facing is not in
DFL tracking: unknown-facing (reaction floor).
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from bisect import bisect_left
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from src.core.geometry import PitchPoint
from src.models.pressing.types import PressingActor

FRAME_HZ: float = 25.0
BALL_SPEED_CAP_MS: float = 35.0


@dataclass(frozen=True)
class IDSSEPass:
    """One ground pass with outcome, targeted receiver, measured speed."""

    passer: str
    passer_team: str
    target_id: str
    start_frame: int
    end_frame: int
    passer_pos_m: PitchPoint
    end_pos_m: PitchPoint
    complete: bool
    ball_speed_ms: float


def _load_roster(path: str) -> Tuple[float, float, Dict[str, str], Dict[str, str]]:
    """Pitch dims, PersonId -> team ('home'/'away'), PersonId -> name."""
    root = ET.parse(path).getroot()
    length, width = 105.0, 68.0
    for ps in root.iter("PitchSize"):
        length = float(ps.attrib.get("X", length))
        width = float(ps.attrib.get("Y", width))
    teams, names = {}, {}
    for team in root.iter("Team"):
        side = "home" if team.attrib.get("Role") == "home" else "away"
        for ps in team.iter("Players"):
            for p in ps.iter("Player"):
                pid = p.attrib["PersonId"]
                teams[pid] = side
                names[pid] = (
                    p.attrib.get("Shortname")
                    or (
                        p.attrib.get("FirstName", "")
                        + " "
                        + p.attrib.get("LastName", "")
                    ).strip()
                )
    return length, width, teams, names


def _read_tracking(
    path: str, roster: Dict[str, str], length: float, width: float
) -> Tuple[
    Dict[int, Dict[str, Tuple[float, float]]],
    Dict[int, Tuple[float, float]],
    Dict[int, float],
]:
    """Frame -> players, frame -> ball, frame -> epoch seconds. Streamed.

    DFL tracking is center-origin; events are corner-origin. Both map to
    canonical corner meters here (+half pitch on read).
    """
    frames: Dict[int, Dict[str, Tuple[float, float]]] = {}
    ball: Dict[int, Tuple[float, float]] = {}
    stamps: Dict[int, float] = {}
    cur_id: Optional[str] = None
    cur_ball = False
    for ev, el in ET.iterparse(path, events=("start", "end")):
        if ev == "start" and el.tag == "FrameSet":
            cur_id = el.attrib.get("PersonId")
            cur_ball = cur_id is not None and cur_id not in roster
        elif ev == "end" and el.tag == "Frame":
            try:
                n = int(el.attrib["N"])
                x = float(el.attrib["X"]) + length / 2.0
                y = float(el.attrib["Y"]) + width / 2.0
                stamps.setdefault(n, datetime.fromisoformat(el.attrib["T"]).timestamp())
            except (KeyError, ValueError):
                pass
            else:
                if cur_id is not None:
                    if cur_ball:
                        ball[n] = (x, y)
                    else:
                        frames.setdefault(n, {})[cur_id] = (x, y)
            el.clear()
        elif ev == "end" and el.tag == "FrameSet":
            cur_id = None
            el.clear()
    return frames, ball, stamps


def _read_passes(
    path: str,
    stamps: Dict[int, float],
    teams: Dict[str, str],
    names: Dict[str, str],
) -> List[IDSSEPass]:
    """Ground (Height=flat) plays with an Evaluation outcome.

    Each pass takes the nearest tracked frame at/after its EventTime.
    X-Position is the action location; X-Source-Position the ball origin
    (they coincide on clean receipts, differ on first-time balls).
    """
    ordered = sorted(stamps)
    epochs = [stamps[f] for f in ordered]
    passes: List[IDSSEPass] = []
    tree = ET.parse(path)
    for event in tree.getroot().iter("Event"):
        try:
            t = datetime.fromisoformat(event.attrib["EventTime"]).timestamp()
        except (KeyError, ValueError):
            continue
        f0 = ordered[min(bisect_left(epochs, t), len(ordered) - 1)] if ordered else 0
        for play in event:
            if play.tag != "Play":
                continue
            if play.attrib.get("Height") != "flat":
                continue
            ev = play.attrib.get("Evaluation", "")
            if ev not in ("successfullyCompleted", "unsuccessful"):
                continue
            try:
                sx = float(event.attrib["X-Position"])
                sy = float(event.attrib["Y-Position"])
                ex = float(event.attrib.get("X-Source-Position", sx))
                ey = float(event.attrib.get("Y-Source-Position", sy))
            except (KeyError, ValueError):
                continue
            pid = play.attrib.get("Player", "")
            passes.append(
                IDSSEPass(
                    passer=names.get(pid, pid),
                    passer_team=teams.get(pid, "unknown"),
                    target_id=play.attrib.get("Recipient", ""),
                    start_frame=f0,
                    end_frame=f0,
                    passer_pos_m=PitchPoint(sx, sy),
                    end_pos_m=PitchPoint(ex, ey),
                    complete=ev == "successfullyCompleted",
                    ball_speed_ms=0.0,
                )
            )
    return passes


def _ball_speed(
    ball: Dict[int, Tuple[float, float]], start: int, window: int = 25
) -> float:
    """Peak frame-to-frame ball speed over [start, start+window].

    Capped at 35 m/s: fastest recorded shots sit ~35-37 m/s and passes
    never exceed shots, so above-cap peaks are tracker spikes.
    """
    peak = 0.0
    prev = ball.get(start)
    for frame in range(start + 1, start + window + 1):
        cur = ball.get(frame)
        if prev is None or cur is None:
            prev = cur
            continue
        dx, dy = cur[0] - prev[0], cur[1] - prev[1]
        peak = max(peak, math.hypot(dx, dy) * FRAME_HZ)
        prev = cur
    return round(min(peak, BALL_SPEED_CAP_MS), 2)


def _velocity(
    frames: Dict[int, Dict[str, Tuple[float, float]]], frame: int, name: str
) -> Tuple[float, float]:
    """Central-difference velocity at frame; (0,0) at data edges."""
    before = frames.get(frame - 1, {}).get(name)
    after = frames.get(frame + 1, {}).get(name)
    if before is None or after is None:
        return (0.0, 0.0)
    dt = 2.0 / FRAME_HZ
    return (
        round((after[0] - before[0]) / dt, 2),
        round((after[1] - before[1]) / dt, 2),
    )


def assign_sides(
    actors: List[PressingActor], end_pos_m: PitchPoint
) -> Tuple[List[PressingActor], List[PressingActor]]:
    """Split actors into (receiving side, opposing side).

    Heuristic fallback when the targeted receiver is untracked. Fails on
    interceptions (nearest man is a defender). Raises ValueError when
    sides are unusable: one side present, any side "unknown", or an
    empty actor list — all would silently empty the opponent list and
    score the pass as safe (arrival unscorable rule).
    """
    sides = {a.team_id for a in actors}
    if not sides or "unknown" in sides or len(sides) < 2:
        raise ValueError(
            f"assign_sides needs two known sides, got {sorted(sides)}: "
            "nearest-to-end cannot run. Pass sides explicitly."
        )

    def nearest(side: str) -> float:
        return min(
            (
                math.dist((a.pos_m.x, a.pos_m.y), (end_pos_m.x, end_pos_m.y))
                for a in actors
                if a.team_id == side
            ),
            default=math.inf,
        )

    rec_side = min(sides, key=nearest)
    return (
        [a for a in actors if a.team_id == rec_side],
        [a for a in actors if a.team_id != rec_side],
    )


def _reception_point(
    ball: Dict[int, Tuple[float, float]],
    frames: Dict[int, Dict[str, Tuple[float, float]]],
    start: int,
    target_id: str,
    window: int = 25,
) -> Optional[Tuple[PitchPoint, int]]:
    """First ball position within 2 m of the target after start.

    Reception = ball meets runner inside one second of flight. Search
    starts one frame after the event: at frame zero the ball is still
    at the passer's feet, which would false-match a nearby target.
    Later meetings are next-phase coincidence (target lingering near a
    settled ball), not this pass arriving. Returns point and frame.
    """
    for f in range(start + 1, start + window + 1):
        b = ball.get(f)
        r = frames.get(f, {}).get(target_id)
        if b is None or r is None:
            continue
        if math.dist(b, r) <= 2.0:
            return PitchPoint(b[0], b[1]), f
    return None


def load_passes(
    tracking_path: str, events_path: str, match_path: str
) -> List[Tuple[IDSSEPass, List[PressingActor]]]:
    """Every ground pass paired with actors at its event frame.

    The end position is the measured reception point (ball meets targeted
    runner within 1 s), not the event coordinates: DFL X-Source is the ball
    origin. Passes with no observed reception are dropped — this
    conditions the pool on the ball arriving (against long balls and the
    very failures the gradient fits), so fitted rates are conditional on
    reception, not unconditional pass risk.
    """
    length, width, teams, names = _load_roster(match_path)
    frames, ball, stamps = _read_tracking(tracking_path, teams, length, width)
    out: List[Tuple[IDSSEPass, List[PressingActor]]] = []
    for p in _read_passes(events_path, stamps, teams, names):
        speed = _ball_speed(ball, p.start_frame)
        found = _reception_point(ball, frames, p.start_frame, p.target_id)
        if found is None:
            continue
        end_pos, end_frame = found
        actors: List[PressingActor] = []
        for tid, (pid, pos) in enumerate(frames.get(p.start_frame, {}).items()):
            vel = _velocity(frames, p.start_frame, pid)
            actors.append(
                PressingActor(
                    track_id=tid,
                    team_id=teams.get(pid, "unknown"),
                    pos_m=PitchPoint(pos[0], pos[1]),
                    vel_ms=vel,
                    provider_id=pid,
                )
            )
        out.append(
            (
                replace(
                    p,
                    ball_speed_ms=speed,
                    end_pos_m=end_pos,
                    end_frame=end_frame,
                ),
                actors,
            )
        )
    return out
