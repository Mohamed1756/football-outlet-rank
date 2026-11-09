"""
Arrival-race physics constants (single source; import, never redefine).
"""

from __future__ import annotations

# Human reaction floor paid when presser orientation is unknown (s).
GK_REACTION_TIME_DEFAULT_S: float = 0.25

# Receiver first-touch and control limits
# McMorris et al. / elite motor control first-touch deceleration window
RECEIVER_FIRST_TOUCH_LATENCY_S: float = 0.45
# Minimum post-receipt cushion before an arriving presser disrupts ball control
MIN_POST_RECEIPT_CUSHION_S: float = 0.20

# Continuous first-touch retention logistic curve parameters
# Steepness over a ~200ms physical disruption window
RETENTION_LOGISTIC_STEEPNESS_K: float = 15.0
# Cushion threshold where retention drops to 50% under direct tackle
RETENTION_CRITICAL_CUSHION_S: float = 0.15

# Kinematic ball mechanics & turf friction parameters
# Initial strike velocity for professional driven goalkeeper ground passes (~79.2 km/h)
PASS_GROUND_INITIAL_SPEED_MS: float = 22.0
# Coulomb rolling friction on FIFA standard hybrid turf: mu_roll ~ 0.25 * 9.81 m/s^2
PASS_TURF_ROLLING_DECELERATION_MSS: float = 2.45

# Presser sprint acceleration profile (Morin et al. sprint biomechanics)
# Peak burst acceleration from standing/jogging stance
PRESSER_MAX_BURST_ACCEL_MSS: float = 3.5
# Maximum sustained sprint speed for professional outfield presser (~30.6 km/h)
PRESSER_SPRINT_MAX_SPEED_MS: float = 8.5
# Mean hip-turn latency under uniform orientation: the expectation of the
# compute_hip_pivot_latency curve over [0, pi] is ~0.39 s. An unknown-facing
# presser pays this minus turn-while-sprinting overlap, floored at the human
# reaction floor. Prior; replaces the flat 0.25 s that assumed the presser
# already faced its target.
UNKNOWN_MEAN_TURN_S: float = 0.40
# Maximum realistic lead passing sprint displacement before receiver checks/slows run
MAX_LEAD_DISPLACEMENT_M: float = 8.0
# Receiver facing fallback floor in m/s. Relocated unchanged.
VELOCITY_FACING_FLOOR_MS: float = 0.5
# Readiness multiplier for unknown receiver orientation. Relocated unchanged.
UNKNOWN_FACING_MULTIPLIER: float = 0.85
# Readiness bonus when the receiver shields back-to-presser. Relocated unchanged.
SHIELD_BONUS: float = 1.10
# Readiness multiplier when open-chested to a converging presser. Relocated unchanged.
EXPOSED_MULTIPLIER: float = 0.80
# Shield cone half-angle in degrees. Relocated unchanged.
SHIELD_ANGLE_DEG: float = 45.0

