"""
quarter_mile_sim.py – Quarter-mile race simulation physics engine (Facade).

All business logic lives in the `sim` package. This module acts as a
backward-compatible facade for existing code and Pyodide / WASM notebooks.

Compatibility: standard CPython AND JupyterLite / Pyodide (WASM).
"""

from sim import (
    G,
    RHO_AIR,
    QUARTER_MILE_M,
    DEFAULT_DT,
    HP_TORQUE_FACTOR,
    DRIVETRAIN_BASE,
    TIRE_COMPOUND_GRIP,
    tire_grip_multiplier,
    interp_curve,
    wheel_rpm_from_speed,
    get_gear_ratio,
    make_car,
    initialize_state,
    simulate_quarter_mile,
)
from sim.powertrain import (
    compute_ice_torque_and_force as ice_drive_force,
    compute_bev_torque_and_force as motor_drive_force,
)
from sim.engine import (
    propulsion_force_and_torque,
    acceleration_and_state,
)

def propulsion_force(v: float, car: dict, state: dict, dt_step: float) -> float:
    """Return net propulsion force (N) for the current timestep."""
    _, force = propulsion_force_and_torque(v, car, state, dt_step)
    return force

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
    "ice_drive_force",
    "motor_drive_force",
    "propulsion_force",
    "acceleration_and_state",
    "simulate_quarter_mile",
]
