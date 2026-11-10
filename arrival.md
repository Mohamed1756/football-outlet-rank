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
  `live_pressers` advances pressers by gated velocity over ball flight
  (mechanism tested, default off; 360 carries no velocities, so the
  calibration stays frozen).
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

## Rank-space calibration (WC2022, 41,561 ground passes)

- Absolute frozen-shape seconds are inflated (standing starts both sides),
  so the honest unit is rank. Margin decile -> incompletion: 20.4% (bottom)
  to 0.2% (top), monotone across all 10 deciles, ~100x gradient.
- Gradient holds within short/mid/long pass-length terciles: not a proxy.
- Passers choose the safest outlet 44% of the time; failure rises
  monotonically with chosen rank (0.024 at rank 0 to ~0.21 at rank 6+).
- `src/models/pressing/calibration.py`: `rank_outlets`, `margin_decile`,
  `decile_risk`, `rank_risk`. Edges are sample-descriptive, not physics.
- Unscorable by construction: 740 recipient-less passes (mostly failed).
  Selection bias toward structured balls; noted, not fixed.

## Replication (Euro2020 33,761 + LaLiga 28,694, frozen WC2022 bins)

- Euro2020: monotone 0.204 -> 0.004 (53x). LaLiga: monotone 0.205 -> 0.003
  (65x). Rank-0 failure 0.024 on all three datasets; rank curves monotone
  to rank 6, pooled tail (7+, n < 300 per set) noisy — LaLiga rank 7 dips
  to 0.157 on n=210 before rank 9 spikes on n=8.
- Verdict: the gradient is not a tournament artifact. Bottom-decile rate
  pins at 0.20 on all three; top-decile floor varies 0.002-0.004.
  Finding stands; absolute seconds still uncalibrated (standing starts).

## Cross-pace replication (Euro 2024 34,617 + WWC 2023 32,807, frozen bins)

- Euro2024: monotone 0.214 -> 0.002 (121x). Closest comparator to Euro2020;
  bins hold across tournaments four years apart. Rank-0 failure 0.020.
- WWC2023: monotone 0.273 -> 0.005 (52x) but the whole curve shifts up:
  bottom decile 0.27 (vs 0.20 men), rank-0 failure 0.048 (vs 0.020-0.024).
  Global incompletion 0.102 vs ~0.05-0.06 men.
- Reading: rank ordering survives slower pace — the gradient is shape, not
  speed. Absolute levels shift: same frozen-shape margin fails ~2x more in
  the women's game. Pace narrows real cushions the snapshot can't see, so
  equal measured shape means less true safety. Rank transfers; seconds don't.
- Verdict: the method generalizes, the levels don't. Edges stay frozen
  within a fit (all five replications reuse the WC2022 bins); a slower
  environment takes a level multiplier instead (`decile_risk` pace_k,
  WWC ~1.5x), not shifted edges: endpoint-proxy refit shows WWC edges
  coincide with WC2022 while rates sit uniformly higher. The ordering
  instrument is pace-free.

## Open priors (fitted, not proven)

- Constant 22 m/s strike for all distances. Distance-band grid on the WC2022
  endpoint proxy (42,374 passes) prefers an unphysical inverted optimum
  (26/20/16 m/s short/mid/long); flat-speed sweep peaks at 14 m/s,
  unphysical for driven long balls. Outcome-fitting cannot identify strike
  speed (bands become sorting knobs), so no band model is adopted and the
  old ~0.2 s short-ball prior is cut; `pass_speed_ms` override stays for
  live tracking data (`src/io/metrica.py` measures per-pass peak ball
  speed, capped at 35 m/s shot-max against tracker spikes).
- Unknown-facing at 360 scale means every presser pays the floor.
- `outlet_value` (retention times forward progress) is a descriptive
  reordering aid: rank-0-by-value is the safest progressive ball, not a
  fitted outcome — no progression outcome exists in the event data to fit it.
- 8 constants, every one referenced. Full video engine recoverable from tag
  `last-full-system`.
