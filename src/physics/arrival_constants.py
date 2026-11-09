"""
Arrival-race physics constants (single source; import, never redefine).
"""

from __future__ import annotations

# Human reaction floor paid when orientation is unknown (s).
HUMAN_REACTION_FLOOR_S: float = 0.25

# Receiver first-touch and control limits
# McMorris et al. / elite motor control first-touch deceleration window
RECEIVER_FIRST_TOUCH_LATENCY_S: float = 0.45

# Continuous first-touch retention logistic curve parameters
# Steepness over a ~200ms physical disruption window
RETENTION_LOGISTIC_STEEPNESS_K: float = 15.0
# Cushion threshold where retention drops to 50% under direct tackle
RETENTION_CRITICAL_CUSHION_S: float = 0.15

# Kinematic ball mechanics & turf friction parameters
# Initial strike velocity for professional driven ground passes (~79.2 km/h)
PASS_GROUND_INITIAL_SPEED_MS: float = 22.0
# Coulomb rolling friction on FIFA standard hybrid turf: mu_roll ~ 0.25 * 9.81 m/s^2
PASS_TURF_ROLLING_DECELERATION_MSS: float = 2.45

# Presser sprint acceleration profile (Morin et al. sprint biomechanics)
# Peak burst acceleration from standing/jogging stance
PRESSER_MAX_BURST_ACCEL_MSS: float = 3.5
PRESSER_SPRINT_MAX_SPEED_MS: float = 8.5
