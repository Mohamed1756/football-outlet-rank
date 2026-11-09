# Arrival Race

Safety of a receiving outlet as a physical race, not a distance heuristic.

`margin(j) = t_press(j) - t_ball(j)` — outlet `j` is viable iff margin > 0.
Both sides race to the same point: the receiver's lead.

- `t_ball`: ground-pass flight, dist = 22t − 1.225t² (22 m/s strike, Coulomb
  turf decel 2.45 m/s²). Returns inf past the ~98.8 m stopping distance:
  no-ball reads as trapped (−99), never as a slow ball.
- Lead: receiver pos + velocity × flight time, capped at 8.0 m. Two-pass
  iteration (lead from t0, re-time to lead, re-lead) converges within ~30 ms.
- `t_press`: sprint burst 3.5 m/s² to an 8.5 m/s cap; only the closing
  velocity component counts. Known facing prices the turn on the hip-pivot
  curve (aligned 0.15 s, full flip 0.70 s). Unknown facing pays the 0.25 s
  human reaction floor.
- Inputs carry distrust: `gate_tracking_velocity` zeroes >8.5 m/s or flagged
  capped vectors and reports the gate. Invalid opponents are skipped, not scored.
- Receipt: 0.45 s first touch plus hip-turn latency. `post_cushion_s`
  subtracts it from margin; `retention_prob` maps the cushion through a
  logistic (steepness 15, 50% at 0.15 s).

## Deleted as unverifiable

- Velocity-as-facing and ball-oriented facing fallbacks (travel is not
  facing; ball-watching was assumed, never measured). Pose or unknown.
- Shield/exposed/unknown-facing multipliers (1.10/0.80/0.85), the
  turn-while-sprinting overlap formula, and the sprint-speed lead cap.
- Defender role/task taxonomy and the snapshot wrapper: nothing assigned or
  read them.

## Open priors (fitted, not proven)

- Constant 22 m/s strike for all distances. Short balls likely overtimed by
  ~0.2 s. Caller override exists (`pass_speed_ms`); default needs a
  distance-dependent strike model.
- Facing unknown at 360 scale: pose data absent, so every presser pays the
  floor. Calibrate the floor, don't decorate it.

## Status

Margin correct within stated priors. Next: feed 360 freeze-frames, fit
margin → retention, fit the strike model.
