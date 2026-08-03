"""
sim/engine.py – Forward-Euler numerical integration solver and dynamic equations of motion.
"""

import numpy as np

from sim.constants import G, RHO_AIR, QUARTER_MILE_M, DEFAULT_DT
from sim.powertrain import (
    compute_ice_torque_and_force,
    compute_bev_torque_and_force,
    maybe_schedule_shift,
)


def initialize_state(car: dict) -> dict:
    """Return a fresh per-run mutable state dict for the given car."""
    return {
        "gear_index": 0,
        "in_shift": False,
        "shift_timer_s": 0.0,
        "pending_gear_index": 0,
        "shift_count": 0,
        "engine_rpm": 0.0,
        "motor_rpm": 0.0,
    }


def propulsion_force_and_torque(
    v: float, car: dict, state: dict, dt_step: float
) -> tuple[float, float]:
    """
    Return (wheel_torque, net_propulsion_force) for the current timestep.

    Handles zero-power shift window for manual gearboxes.
    """
    if car["powertrain_type"] == "ICE":
        if state["in_shift"]:
            state["shift_timer_s"] -= dt_step
            if state["shift_timer_s"] <= 0.0:
                state["in_shift"] = False
                state["gear_index"] = state["pending_gear_index"]
            return 0.0, 0.0
        w_tq, force = compute_ice_torque_and_force(v, car, state)
        maybe_schedule_shift(v, car, state)
        return w_tq, force

    if car["powertrain_type"] == "BEV":
        return compute_bev_torque_and_force(v, car, state)

    return 0.0, 0.0


def acceleration_and_state(
    v: float, car: dict, state: dict, dt_step: float
) -> tuple[float, float]:
    """
    Compute net longitudinal acceleration (m/s²) and current wheel torque (Nm),
    accounting for traction limit, aerodynamic drag, and rolling resistance.

    Returns: (accel, wheel_torque)
    """
    wheel_torque, drive_force = propulsion_force_and_torque(v, car, state, dt_step)
    traction_force_max = car["mu"] * car["mass"] * G * car["drive_factor"]
    usable_force = min(drive_force, traction_force_max)
    drag_force = 0.5 * RHO_AIR * car["CdA"] * (v ** 2)
    rolling_force = car["rolling_resistance"] * car["mass"] * G
    net_force = usable_force - drag_force - rolling_force
    accel = net_force / car["mass"]
    return accel, wheel_torque


def simulate_quarter_mile(
    car: dict,
    dt: float = DEFAULT_DT,
    distance_target: float = QUARTER_MILE_M,
) -> dict:
    """
    Forward-Euler integration from standstill until the car covers
    ``distance_target`` metres or 60 seconds have elapsed.

    Parameters
    ----------
    car : dict
        Runtime car dict produced by :func:`make_car`.
    dt : float
        Integration timestep in seconds (default ``DEFAULT_DT``).
    distance_target : float
        Race distance in metres (default ``QUARTER_MILE_M``).

    Returns
    -------
    dict
        Time-series arrays (``time``, ``distance``, ``speed``, ``accel``,
        ``gear``, ``engine_rpm``, ``motor_rpm``, ``wheel_torque``) plus
        scalar summary fields (``elapsed_time``, ``trap_speed``,
        ``shift_count``).
    """
    t, x, v = 0.0, 0.0, 0.0
    state = initialize_state(car)

    times:         list = [t]
    distances:     list = [x]
    speeds:        list = [v]
    accels:        list = [0.0]
    gears:         list = [state["gear_index"] + 1]
    engine_rpms:   list = [0.0]
    motor_rpms:    list = [0.0]
    wheel_torques: list = [0.0]

    while x < distance_target and t <= 60.0:
        a, wheel_torque = acceleration_and_state(v, car, state, dt)

        v = max(0.0, v + a * dt)
        x = x + v * dt
        t = t + dt

        times.append(t)
        distances.append(x)
        speeds.append(v)
        accels.append(a)
        gears.append(state["gear_index"] + 1)
        engine_rpms.append(state["engine_rpm"])
        motor_rpms.append(state["motor_rpm"])
        wheel_torques.append(wheel_torque)

    return {
        "time":         np.array(times),
        "distance":     np.array(distances),
        "speed":        np.array(speeds),
        "accel":        np.array(accels),
        "gear":         np.array(gears),
        "engine_rpm":   np.array(engine_rpms),
        "motor_rpm":    np.array(motor_rpms),
        "wheel_torque": np.array(wheel_torques),
        "elapsed_time": t,
        "trap_speed":   v,
        "shift_count":  state["shift_count"],
    }
