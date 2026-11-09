# Arrival Race

Safety of a receiving outlet as a physical race, not a distance heuristic.

`margin(j) = t_press(j) - t_ball(j)` — outlet `j` is viable iff margin > 0.

- `t_ball`: ground-pass flight with 22 m/s initial strike, Coulomb turf decel 2.45 m/s². No constant-speed fiction.
- `t_press`: sprint burst 3.5 m/s², 8.5 m/s cap, plus engagement latency from body orientation (back-turned ~0.70 s, engaged plant-only, unknown 0.25 s floor).
- Inputs carry distrust: `gate_tracking_velocity` zeroes >8.5 m/s or capped vectors; `lead_target` bounds receiver displacement to 8.0 m.
- Receipt priced too: `receiver_readiness` adds 0.45 s first touch plus hip-turn latency; `post_cushion_s` subtracts it from margin; `retention_prob` maps the cushion through a logistic (steepness 15, 50% at 0.15 s).

## Novelty

No open metric prices pass safety against defender arrival with kinematics. xT/xG cover outfield value after receipt; this covers whether receipt survives. Burst-accel arrival (static 3 m presser ~1.31 s, not 3.0 s walk artifact) plus facing latency plus a calibrated retention curve is unpublished as a reusable unit.

## Value

Pure functions `PressingSnapshot → ArrivalResult(margin_s, t_press_s, t_ball_s, best_presser_id)` and `receiver → ReadinessResult → retention_prob` per outlet. Numpy-only, no CV, no tracker, no homography. Any tracking feed in, seconds and probabilities out. Fittable: margin → retention on 360 freeze-frames.

## Status

Core tested (flight scaling, burst kinematics, facing latency, velocity gating, retention calibration). Prior feeds were untrustworthy (video LOO 16 m vs 1–2 m signal); core was never the fault. Next: calibrate retention threshold on StatsBomb 360 open data in `data/wc2022`, `data/euro2020`, `data/laliga`.
