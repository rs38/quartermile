"""
sim/constants.py – Physical constants, default parameters, and lookup tables.
"""

# Physical constants
G: float = 9.81                # gravitational acceleration, m/s²
RHO_AIR: float = 1.225         # air density at sea level, kg/m³
QUARTER_MILE_M: float = 402.336 # race distance, m
DEFAULT_DT: float = 0.01       # default forward-Euler timestep, s

# Calculation & domain constants
HP_TORQUE_FACTOR: float = 7745.0  # constant converting (Nm * RPM) to HP (~60 * 745.7 / 2pi)
MIN_WHEEL_RADIUS_M: float = 0.2    # minimum wheel radius safety clamp, m
LAUNCH_SPEED_THRESHOLD_MS: float = 1.5  # threshold below which launch_rpm applies, m/s

# Drivetrain torque & grip factor lookup table
DRIVETRAIN_BASE: dict = {
    "RWD": {"drive_factor": 0.93},
    "AWD": {"drive_factor": 1.00},
}

# Tire compound friction multiplier lookup table
TIRE_COMPOUND_GRIP: dict = {
    "all_season":  0.95,
    "summer":      1.00,
    "track":       1.08,
    "drag_radial": 1.15,
}
