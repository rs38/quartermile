"""
sim/powertrain.py – Tire mechanics, kinematics, and powertrain force calculations.
"""

import numpy as np

from sim.constants import (
    TIRE_COMPOUND_GRIP,
    MIN_WHEEL_RADIUS_M,
    LAUNCH_SPEED_THRESHOLD_MS,
)


def tire_grip_multiplier(tire_width_mm: float, tire_compound: str = "summer") -> float:
    """
    Return a combined grip multiplier accounting for tyre width and compound.

    Wider tyres gain grip with a sub-linear (0.30-power) scaling relative to a
    245 mm baseline. The width factor is clamped to [0.90, 1.18].
    """
    width_factor = (tire_width_mm / 245.0) ** 0.30
    width_factor = float(np.clip(width_factor, 0.90, 1.18))
    return width_factor * TIRE_COMPOUND_GRIP.get(tire_compound, 1.00)


def interp_curve(curve_points: list, x_value: float) -> float:
    """Linear interpolation over a list of [x, y] breakpoints."""
    points = np.array(curve_points, dtype=float)
    return float(np.interp(x_value, points[:, 0], points[:, 1]))


def wheel_rpm_from_speed(v: float, wheel_radius_m: float) -> float:
    """Convert vehicle speed (m/s) to wheel rotational speed (RPM)."""
    return (v / max(wheel_radius_m, MIN_WHEEL_RADIUS_M)) * 60.0 / (2.0 * np.pi)


def get_gear_ratio(car: dict, gear_index: int) -> float:
    """Look up the transmission ratio for the given gear (0-indexed), clamped to valid range."""
    ratios = car["ice"]["gear_ratios"]
    idx = int(np.clip(gear_index, 0, len(ratios) - 1))
    return ratios[idx]


def compute_ice_torque_and_force(v: float, car: dict, state: dict) -> tuple[float, float]:
    """
    Compute instantaneous wheel torque (Nm) and drive force (N) for an ICE powertrain.

    Side-effect: updates ``state["engine_rpm"]``.
    Returns: (wheel_torque, drive_force)
    """
    ice = car["ice"]
    ratio = get_gear_ratio(car, state["gear_index"])
    fd = ice["final_drive"]
    engine_rpm = wheel_rpm_from_speed(v, car["wheel_radius_m"]) * ratio * fd
    if v < LAUNCH_SPEED_THRESHOLD_MS:
        engine_rpm = max(engine_rpm, ice["launch_rpm"])
    else:
        engine_rpm = max(engine_rpm, ice["idle_rpm"])
    engine_rpm = min(engine_rpm, ice["redline_rpm"])
    state["engine_rpm"] = engine_rpm
    engine_torque = interp_curve(ice["torque_curve_rpm_nm"], engine_rpm)
    wheel_torque = (
        engine_torque * ratio * fd
        * ice["engine_efficiency"]
        * ice["driveline_efficiency"]
    )
    drive_force = wheel_torque / max(car["wheel_radius_m"], MIN_WHEEL_RADIUS_M)
    return wheel_torque, drive_force


def compute_bev_torque_and_force(v: float, car: dict, state: dict) -> tuple[float, float]:
    """
    Compute instantaneous wheel torque (Nm) and drive force (N) for a BEV powertrain.

    Side-effect: updates ``state["motor_rpm"]``.
    Returns: (wheel_torque, drive_force)
    """
    motor = car["motor"]
    ratio = motor["single_speed_ratio"]
    motor_rpm = wheel_rpm_from_speed(v, car["wheel_radius_m"]) * ratio
    motor_rpm = min(motor_rpm, motor["max_rpm"])
    state["motor_rpm"] = motor_rpm
    motor_torque = interp_curve(motor["torque_curve_rpm_nm"], motor_rpm)
    wheel_torque = (
        motor_torque * ratio
        * motor["motor_efficiency"]
        * motor["inverter_efficiency"]
    )
    drive_force = wheel_torque / max(car["wheel_radius_m"], MIN_WHEEL_RADIUS_M)
    return wheel_torque, drive_force


def maybe_schedule_shift(v: float, car: dict, state: dict) -> None:
    """Trigger an upshift when the engine hits shift_rpm."""
    if "ice" not in car:
        return
    ice = car["ice"]
    ratios = ice["gear_ratios"]
    if state["in_shift"] or state["gear_index"] >= len(ratios) - 1:
        return
    if state["engine_rpm"] >= ice["shift_rpm"]:
        state["pending_gear_index"] = state["gear_index"] + 1
        if ice["gearbox_type"] == "manual":
            state["in_shift"] = True
            state["shift_timer_s"] = ice["shift_time_s"]
            state["shift_count"] += 1
        else:
            state["gear_index"] = state["pending_gear_index"]
            state["shift_count"] += 1
