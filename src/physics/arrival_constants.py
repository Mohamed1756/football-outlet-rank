"""
Arrival-race physics constants (single source; import, never redefine).

Values are assumed profiles, not measurements: each comment names the
external source for the concept and states what was assumed. Fitted
quantities live in src/models/pressing/calibration.py instead.
"""

from __future__ import annotations

# Assumed simple visual-reaction floor (conventional 200-300 ms athlete
# range; no paper claims this exact value).
HUMAN_REACTION_FLOOR_S: float = 0.25

# Receiver first-touch and control limits. Time-to-control concept from
# Spearman et al. 2017 (Hudl SSAC: physics-based pass probabilities,
# lambda ~4.3/s control rate); our 0.45 s + logistic below is a
# re-parameterization, not their fit.
RECEIVER_FIRST_TOUCH_LATENCY_S: float = 0.45

# Continuous first-touch retention logistic curve parameters
# Steepness over a ~200ms physical disruption window
RETENTION_LOGISTIC_STEEPNESS_K: float = 15.0
# Cushion threshold where retention drops to 50% under direct tackle
RETENTION_CRITICAL_CUSHION_S: float = 0.15

# Kinematic ball mechanics & turf friction parameters
# Assumed strike for a professional driven ground pass (~79 km/h).
# Ball-surface interaction is regulated (FIFA Quality Programme for
# Football Turf, Test Manual I); rolling-friction treatment follows the
# Coulomb simplification, cf. the drag-model alternative in Spearman
# et al. 2017. mu_roll ~ 0.25 assumed, not measured here.
PASS_GROUND_INITIAL_SPEED_MS: float = 22.0
PASS_TURF_ROLLING_DECELERATION_MSS: float = 2.45

# Presser sprint acceleration profile. Force-velocity profiling method from
# Morin et al. (2016, simple field method for sprint F-v-P; extended in
# Samozino et al. 2021, Scand J Med Sci Sports). 3.5 m/s^2 burst and
# 8.5 m/s cap are assumed team-sport values, not a measured cohort.
PRESSER_MAX_BURST_ACCEL_MSS: float = 3.5
PRESSER_SPRINT_MAX_SPEED_MS: float = 8.5
