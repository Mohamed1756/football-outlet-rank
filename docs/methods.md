# Methods: rank outlets, re-scale levels, measure seconds

Three moves, each answering one question. Each move names the function
to call and the evidence behind it.

## 1. Rank every outlet on one freeze

![Frozen vs live: the same pass, 0.96 s later](figs/fig5_frozen_vs_live.svg)
![One frozen shape: the raw material behind fig1](figs/fig6_frozen_shape.svg)

Score each outlet by its arrival cushion — `t_press - t_ball`, the time
between the ball reaching the ball-to-runner intercept and the nearest
presser reaching it — and sort safest-first. Rank 0 is the best outlet
on that play. Absolute seconds are inflated (frozen 360 shape, standing
starts both sides), so rank is the portable unit: which outlets are
tighter than which.

Evidence: bottom decile fails at 20–27%, top at 0.2–0.5%, monotone
across all five calibration datasets and the broadcast replication
(`docs/figs/fig1_decile_curves.png`). Rank 0 fails at 0.02–0.05;
failure rises every rank.

```python
from src.models.pressing.calibration import rank_outlets, rank_risk
ranks = rank_outlets([1.9, 0.4, 1.2])  # margins per outlet, safest first
```

## 2. Re-scale levels per pace environment, never re-bin edges

Rank ordering transfers across pace; absolute levels don't. The women's
game fails ~1.5x the men's rate at equal frozen-shape margin, so the
same decile bin carries a higher risk there. Keep the fixed WC2022 edges
and scale the rate:

```python
from src.models.pressing.calibration import decile_risk
decile_risk(1)          # 0.204 — WC2022 baseline
decile_risk(1, pace_k=1.5)  # 0.306 — approximates the WWC2023 level
```

![Same freeze, two paces](figs/fig7_risk_surface.svg)

## 3. Measure seconds where tracking exists

On 25 fps tracking with a ball track, arrival time is observed
(release-to-reception), not modeled. Pass the measured intercept and
flight time and skip the equation entirely — no stopping-distance
trap, no strike assumption:

```python
arrival_margin(receiver, opponents, passer_pos,
               live_pressers=True,
               measured=(intercept_point, t_ball_s))
```

The frozen flight equation (Coulomb, 22 m/s) stays the default where no
ball track exists — it covers every pass even where it mistimes slow
ones. Measured truth rules where tracking exists.

## Boundaries

What the instrument does not do, stated once so nobody has to
rediscover it:

- It ranks outlets given an attempt. When or whether to pass is
  unobserved — no event+tracking dataset records the ball not played.
- It does not rank passers. Full-pitch choice sets on IDSSE show
  rank-0 choice at 0.00–0.20 with no link to completion: passers
  optimize something the margin doesn't see.
- Seconds from the frozen model are inflated. Trust the ordering, not
  the clock — unless you measured the flight.
- It does split teams. On 20 SkillCorner matches, base incompletion
  (execution) spreads 2x across 13 clubs, median attempted cushion
  (decision) spreads 2x, and tight-quintile failure under pressure
  spreads 2x — Melbourne City leads all three.
