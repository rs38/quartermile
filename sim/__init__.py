"""
sim package – Quarter-mile race simulation physics engine.
"""

from sim.constants import (
    G,
    RHO_AIR,
    QUARTER_MILE_M,
    DEFAULT_DT,
    HP_TORQUE_FACTOR,
    DRIVETRAIN_BASE,
    TIRE_COMPOUND_GRIP,
)
from sim.powertrain import (
    tire_grip_multiplier,
    interp_curve,
    wheel_rpm_from_speed,
    get_gear_ratio,
)
from sim.adapter import make_car
from sim.engine import (
    initialize_state,
    simulate_quarter_mile,
)

__all__ = [
    "G",
    "RHO_AIR",
    "QUARTER_MILE_M",
    "DEFAULT_DT",
    "HP_TORQUE_FACTOR",
    "DRIVETRAIN_BASE",
    "TIRE_COMPOUND_GRIP",
    "tire_grip_multiplier",
    "interp_curve",
    "wheel_rpm_from_speed",
    "get_gear_ratio",
    "make_car",
    "initialize_state",
    "simulate_quarter_mile",
]
