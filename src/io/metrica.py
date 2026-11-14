"""Metrica Sports sample-data loader: tracking frames to PressingActors.

Metrica CSVs are normalized (x 0..1, y 0..1) at 25 Hz with three header
rows; ball x/y are the final two columns. Velocities are central
differences times the frame rate. Facing is unavailable in this data,
so actors load as unknown-facing (reaction floor); velocity direction
is travel, never facing.

Coordinates map linearly onto the canonical 105 x 68 m pitch. Attack
direction per period is not in the files; passers keep raw orientation
and downstream geometry is direction-agnostic (distances only).
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, replace
from typing import Dict, List, Tuple
from src.core.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, PitchPoint
from src.models.pressing.types import PressingActor

FRAME_HZ: float = 25.0


@dataclass(frozen=True)
class MetricaPass:
    """One pass event with start/end frames and measured ball speed."""

    passer: str
    recipient: str
    start_frame: int
    end_frame: int
    passer_pos_m: PitchPoint
    end_pos_m: PitchPoint
    ball_speed_ms: float


def _read_tracking(path: str) -> Dict[int, Dict[str, Tuple[float, float]]]:
    """Frame -> {player_name: (x_m, y_m)}. Skips the 3 header rows."""
    frames: Dict[int, Dict[str, Tuple[float, float]]] = {}
    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    names = [c.strip() for c in rows[2]]
    for row in rows[3:]:
        try:
            frame = int(float(row[1]))
        except (ValueError, IndexError):
            continue
        players: Dict[str, Tuple[float, float]] = {}
        for col in range(3, len(row) - 2, 2):
            name = names[col] if col < len(names) else ""
            if not name or name.lower() == "nan":
                continue
            try:
                x = float(row[col]) * PITCH_LENGTH_M
                y = float(row[col + 1]) * PITCH_WIDTH_M
            except (ValueError, IndexError):
                continue
            players[name] = (x, y)
        frames[frame] = players
    return frames


def _read_ball(path: str) -> Dict[int, Tuple[float, float]]:
    """Frame -> (x_m, y_m) from the final two columns."""
    ball: Dict[int, Tuple[float, float]] = {}
    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    for row in rows[3:]:
        try:
            frame = int(float(row[1]))
            x = float(row[-2]) * PITCH_LENGTH_M
            y = float(row[-1]) * PITCH_WIDTH_M
        except (ValueError, IndexError):
            continue
        ball[frame] = (x, y)
    return ball


def _read_passes(path: str) -> List[MetricaPass]:
    """Pass rows with a measured ball speed placeholder (filled later)."""
    passes: List[MetricaPass] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("Type") != "PASS":
                continue
            try:
                sf = int(float(row["Start Frame"]))
                ef = int(float(row["End Frame"]))
                sx = float(row["Start X"]) * PITCH_LENGTH_M
                sy = float(row["Start Y"]) * PITCH_WIDTH_M
                ex = float(row["End X"]) * PITCH_LENGTH_M
                ey = float(row["End Y"]) * PITCH_WIDTH_M
            except (ValueError, TypeError):
                continue
            passes.append(
                MetricaPass(
                    passer=row.get("From", ""),
                    recipient=row.get("To", ""),
                    start_frame=sf,
                    end_frame=ef,
                    passer_pos_m=PitchPoint(sx, sy),
                    end_pos_m=PitchPoint(ex, ey),
                    ball_speed_ms=0.0,
                )
            )
    return passes


def _ball_speed(ball: Dict[int, Tuple[float, float]], start: int, end: int) -> float:
    """Peak frame-to-frame ball speed over [start, end]; 0.0 if untracked.

    Capped at 35 m/s: fastest recorded shots sit ~35-37 m/s and passes
    never exceed shots, so above-cap peaks are single-frame tracker
    spikes (observed 43+ m/s against ~15 m/s neighbors).
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
    the receiving side. Works because the recipient runs onto the ball;
    fails on interceptions (nearest man is a defender), so callers
    scoring turnovers should pass sides explicitly instead. Raises
    ValueError when sides are unusable: one side present, any side
    "unknown", or an empty actor list — all would silently empty the
    opponent list and score the pass as safe (arrival unscorable rule).
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


def load_passes(
    home_path: str, away_path: str, events_path: str
) -> List[Tuple[MetricaPass, List[PressingActor]]]:
    """Every pass paired with actors at its start frame.

    Team assignment via assign_sides (nearest-to-end heuristic; see its
    docstring for the interception caveat). Ball speed is the measured
    peak over the pass window.
    """
    home = _read_tracking(home_path)
    away = _read_tracking(away_path)
    ball_home = _read_ball(home_path)
    ball = ball_home or _read_ball(away_path)
    out: List[Tuple[MetricaPass, List[PressingActor]]] = []
    for p in _read_passes(events_path):
        speed = _ball_speed(ball, p.start_frame, p.end_frame)
        actors: List[PressingActor] = []
        tid = 0
        for team_id, frames in (("home", home), ("away", away)):
            for name, pos in frames.get(p.start_frame, {}).items():
                vel = _velocity(frames, p.start_frame, name)
                actors.append(
                    PressingActor(
                        track_id=tid,
                        team_id=team_id,
                        pos_m=PitchPoint(pos[0], pos[1]),
                        vel_ms=vel,
                    )
                )
                tid += 1

        out.append((replace(p, ball_speed_ms=speed), actors))
    return out
