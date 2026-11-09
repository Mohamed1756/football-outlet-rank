# Arrival Race

Safety of a receiving outlet as a physical race, not a distance heuristic.

`margin(j) = t_press(j) - t_ball(j)` — outlet `j` is viable iff margin > 0.
Both sides race to the ball-to-runner intercept.

- `t_ball`: ground-pass flight, dist = 22t − 1.225t² (22 m/s strike, Coulomb
  turf decel 2.45 m/s²). Returns inf past the ~98.8 m stopping distance:
  no-ball reads as trapped (−99), never as a slow ball.
- Intercept: bisection on the gap between receiver run and ball travel.
  Monotone horizon derived from the strike, t_hi = (v0 − 8.5) / a: ball must
  outrun any gated run or the gap can go non-monotone (dead ball, live
  runner returns inf, not a slow ball). Unclamped: the intercept is playable
  space, on or off the pitch. Receiver runs during prep; pressers frozen
  (snapshot convention, ~1 m pro-receiver bias, documented not modeled).
- `t_press`: sprint burst 3.5 m/s² to an 8.5 m/s cap; only the closing
  velocity component counts. Known facing prices the turn on the hip-pivot
  curve (aligned 0.15 s, full flip 0.70 s). Unknown facing pays the 0.25 s
  human reaction floor — no angle, no curve. Standing on the intercept still
  pays engagement latency (most dangerous geometry, never zero).
- Inputs carry distrust: `gate_tracking_velocity` zeroes >8.5 m/s or flagged
  capped vectors and reports the gate. Invalid opponents are skipped, not scored.
- Receipt: 0.45 s first touch plus turn latency (0.25 s floor when unknown).
  `post_cushion_s` subtracts it from margin; `retention_prob` maps the cushion
  through a logistic (steepness 15, 50% at 0.15 s).

## Deleted as unverifiable

- Lead cap + `lead_target`, post-receipt cushion threshold (tested, wired to
  nothing — same class as the multiplier), velocity-as-facing and
  ball-oriented facing fallbacks, `readiness_mult` and the execution penalty
  (scored nothing downstream), shield/exposed/unknown-facing multipliers,
  turn-while-sprinting overlap, defender role/task taxonomy, snapshot wrapper.
- Kept as provenance, not inputs: `facing_source` (pose vs floor) and `note`.
  They tell calibration which margins used measured orientation.

## Open priors (fitted, not proven)

- Constant 22 m/s strike for all distances. Short balls likely overtimed by
  ~0.2 s (needs a distance-dependent strike model; `pass_speed_ms` override exists).
- Unknown-facing at 360 scale means every presser pays the floor.
- 8 constants, every one referenced. Full video engine recoverable from tag
  `last-full-system`.
