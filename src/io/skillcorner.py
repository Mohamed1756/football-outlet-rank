"""SkillCorner open-data loader: broadcast tracking frames to PressingActors.

Tracking JSONL: one object per frame (10 fps), center-origin meters,
player_data entries with x/y/player_id/is_detected, ball_data with x/y.
Dynamic events CSV: player_possession rows carry pass outcomes
(successful/unsuccessful) and start/end positions.

Coordinates map center-origin to canonical corner origin using the
match pitch dimensions (default 105 x 68 m). Velocities are central
differences at 10 fps. Facing is unavailable: unknown-facing (floor).
Frames flagged extrapolated are kept but callers should know 10 fps
broadcast tracking is noisier than 25 Hz optical; the trust gate
catches spikes.
"""

import csv
import json
import math
from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Tuple

from src.core.geometry import PitchPoint
from src.models.pressing.types import PressingActor

FRAME_HZ: float = 10.0


@dataclass(frozen=True)
class SkillCornerPass:
    """One possession pass with outcome and measured ball speed."""

    passer: str
    passer_team: str
    target_id: str
    start_frame: int
    end_frame: int
    passer_pos_m: PitchPoint
    end_pos_m: PitchPoint
    complete: bool
    ball_speed_ms: float


def _load_match_meta(path: str) -> Tuple[float, float, Dict[str, str]]:
    """Pitch dims and player_id -> team ('home'/'away') from match.json."""
    with open(path) as f:
        meta = json.load(f)
    length = float(meta.get("pitch_length") or 105.0)
    width = float(meta.get("pitch_width") or 68.0)
    home_id = str(meta["home_team"]["id"])
    teams: Dict[str, str] = {}
    for p in meta.get("players", []):
        pid = str(p.get("player_id", p.get("id", "")))
        teams[pid] = "home" if str(p.get("team_id", "")) == home_id else "away"
    return length, width, teams


def _read_tracking(
    path: str, length: float, width: float
) -> Dict[int, Dict[str, Tuple[float, float]]]:
    """Frame -> {player_id: (x_m, y_m, corner origin)}."""
    frames: Dict[int, Dict[str, Tuple[float, float]]] = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            fr = json.loads(line)
            players: Dict[str, Tuple[float, float]] = {}
            for p in fr.get("player_data", []):
                if p.get("x") is None or p.get("y") is None:
                    continue
                players[str(p["player_id"])] = (
                    float(p["x"]) + length / 2.0,
                    float(p["y"]) + width / 2.0,
                )
            frames[int(fr["frame"])] = players
    return frames


def _read_ball(
    path: str, length: float, width: float
) -> Dict[int, Tuple[float, float]]:
    """Frame -> ball (x_m, y_m, corner origin)."""
    ball: Dict[int, Tuple[float, float]] = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            fr = json.loads(line)
            b = fr.get("ball_data") or {}
            if b.get("x") is None or b.get("y") is None:
                continue
            ball[int(fr["frame"])] = (
                float(b["x"]) + length / 2.0,
                float(b["y"]) + width / 2.0,
            )
    return ball


def _read_passes(path: str, length: float, width: float) -> List[SkillCornerPass]:
    """Possession rows with a pass outcome; speed filled later."""
    passes: List[SkillCornerPass] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("event_type") != "player_possession":
                continue
            outcome = (row.get("pass_outcome") or "").strip()
            if outcome not in ("successful", "unsuccessful"):
                continue
            try:
                sf = int(float(row["frame_start"]))
                ef = int(float(row["frame_end"] or row["frame_start"]))
                sx = float(row["x_start"]) + length / 2.0
                sy = float(row["y_start"]) + width / 2.0
                ex = float(row["x_end"]) + length / 2.0
                ey = float(row["y_end"]) + width / 2.0
            except (ValueError, TypeError):
                continue
            passes.append(
                SkillCornerPass(
                    passer=row.get("player_name", ""),
                    passer_team=row.get("team_shortname", ""),
                    target_id=str(row.get("player_targeted_id") or "").split(".")[0],
                    start_frame=sf,
                    end_frame=ef,
                    passer_pos_m=PitchPoint(sx, sy),
                    end_pos_m=PitchPoint(ex, ey),
                    complete=outcome == "successful",
                    ball_speed_ms=0.0,
                )
            )
    return passes


def _ball_speed(ball: Dict[int, Tuple[float, float]], start: int, end: int) -> float:
    """Peak frame-to-frame ball speed over [start, end]; 0.0 if untracked.

    Capped at 35 m/s: fastest recorded shots sit ~35-37 m/s and passes
    never exceed shots, so above-cap peaks are tracker spikes.
    """
    peak = 0.0
    prev = ball.get(start)
    for frame in range(start + 1, end + 1):
        cur = ball.get(frame)
        if prev is None or cur is None:
            prev = cur
            continue
        dx = cur[0] - prev[0]
        dy = cur[1] - prev[1]
        speed = (dx * dx + dy * dy) ** 0.5 * FRAME_HZ
        peak = max(peak, speed)
        prev = cur
    return round(min(peak, 35.0), 2)


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

    Heuristic: the side with a player nearest the pass end position is
    the receiving side. Fails on interceptions (nearest man is a
    defender); callers scoring turnovers should pass sides explicitly.
    """

    def nearest(side: str) -> float:
        return min(
            (
                math.dist((a.pos_m.x, a.pos_m.y), (end_pos_m.x, end_pos_m.y))
                for a in actors
                if a.team_id == side
            ),
            default=math.inf,
        )

    sides = {a.team_id for a in actors}
    rec_side = min(sides, key=nearest, default="")
    return (
        [a for a in actors if a.team_id == rec_side],
        [a for a in actors if a.team_id != rec_side],
    )


def load_passes(
    tracking_path: str, events_path: str, match_path: Optional[str] = None
) -> List[Tuple[SkillCornerPass, List[PressingActor]]]:
    """Every possession pass paired with actors at its start frame.

    Team ids come from match.json when given, else 'home'/'away' by
    roster order is unavailable and all load as 'unknown' — pass
    match_path. Ball speed is the measured peak over the pass window.
    """
    if match_path is not None:
        length, width, team_of = _load_match_meta(match_path)
    else:
        length, width, team_of = 105.0, 68.0, {}
    frames = _read_tracking(tracking_path, length, width)
    ball = _read_ball(tracking_path, length, width)
    out: List[Tuple[SkillCornerPass, List[PressingActor]]] = []
    for p in _read_passes(events_path, length, width):
        speed = _ball_speed(ball, p.start_frame, p.end_frame)
        actors: List[PressingActor] = []
        tid = 0
        for pid, pos in frames.get(p.start_frame, {}).items():
            vel = _velocity(frames, p.start_frame, pid)
            actors.append(
                PressingActor(
                    track_id=tid,
                    team_id=team_of.get(pid, "unknown"),
                    pos_m=PitchPoint(pos[0], pos[1]),
                    vel_ms=vel,
                    provider_id=pid,
                )
            )
        out.append((replace(p, ball_speed_ms=speed), actors))
    return out
