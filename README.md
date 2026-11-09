# Arrival Race

Safety of a receiving outlet as a physical race, not a distance heuristic.
Both sides race to the receiver's lead point.

## Quick Start

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Usage

```python
from src.core.geometry import PitchPoint
from src.models.pressing.arrival import arrival_margin
from src.models.pressing.readiness import receiver_readiness
from src.models.pressing.types import PressingActor

receiver = PressingActor(track_id=9, team_id="own", pos_m=PitchPoint(86.0, 25.0))
presser = PressingActor(
    track_id=1, team_id="opp",
    pos_m=PitchPoint(87.5, 26.5), vel_ms=(-4.0, -2.0),
)
res = arrival_margin(receiver, [presser], PitchPoint(100.0, 29.0))
ready = receiver_readiness(receiver, PitchPoint(100.0, 29.0))
print(res.margin_s, res.t_ball_s, res.t_press_s, res.best_presser_id)
print(ready.reception_latency_s, ready.post_cushion_s(res.margin_s))
print(ready.retention_prob(res.margin_s))
```

- `src/models/pressing/arrival.py` — `flight_time_s`, `intercept_target`,
  `presser_engagement_latency_s`, `presser_arrival_s`, `arrival_margin`.
- `src/physics/arrival_constants.py` — 8 arrival-race constants, single source.
- `src/physics/biomechanics.py` — hip-pivot latency + angle wrap.
- `src/core/geometry.py` — `PitchPoint` only.
- `arrival.md` — research note: values, novelty, deleted priors.
- `data/wc2022`, `data/euro2020`, `data/laliga` — open 360 freeze-frames
  for margin-to-retention calibration (untracked, local only).

## Full system

The deleted video engine (detection, tracking, homography, dashboard) is
recoverable from tag `last-full-system`.
