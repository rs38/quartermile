"""
quarter_mile_sim.py – Quarter-mile race simulation physics engine.

All business logic lives here so the notebook stays focused on
configuration, exploration, and visualisation.

Compatibility: standard CPython AND JupyterLite / Pyodide (WASM).
Place this file alongside quarter_mile_race.ipynb in the deployment
root so that Pyodide can import it directly.

Only numpy is required at runtime.  No file I/O, no C extensions beyond
numpy itself – both constraints are required for Pyodide compatibility.
"""

import numpy as np

# ── Physical constants ────────────────────────────────────────────────────────
G = 9.81                # gravitational acceleration, m/s²
RHO_AIR = 1.225         # air density at sea level, kg/m³
QUARTER_MILE_M = 402.336  # race distance, m
DEFAULT_DT = 0.01       # default forward-Euler timestep, s

# ── Lookup tables ─────────────────────────────────────────────────────────────
DRIVETRAIN_BASE: dict = {
    "RWD": {"drive_factor": 0.93},
    "AWD": {"drive_factor": 1.00},
}

TIRE_COMPOUND_GRIP: dict = {
    "all_season":  0.95,
    "summer":      1.00,
    "track":       1.08,
    "drag_radial": 1.15,
}

# ── Tire / grip helpers ───────────────────────────────────────────────────────

def tire_grip_multiplier(tire_width_mm: float, tire_compound: str = "summer") -> float:
    """
    Returns a combined grip multiplier accounting for tyre width and compound.

    Wider tyres gain grip with a sub-linear (0.30-power) scaling relative to a
    245 mm baseline.  The width factor is clamped to [0.90, 1.18].
    """
    width_factor = (tire_width_mm / 245.0) ** 0.30
    width_factor = float(np.clip(width_factor, 0.90, 1.18))
    return width_factor * TIRE_COMPOUND_GRIP.get(tire_compound, 1.00)


def interp_curve(curve_points: list, x_value: float) -> float:
    """Linear interpolation over a list of [x, y] breakpoints."""
    points = np.array(curve_points, dtype=float)
    return float(np.interp(x_value, points[:, 0], points[:, 1]))


# ── Kinematics helpers ────────────────────────────────────────────────────────

def wheel_rpm_from_speed(v: float, wheel_radius_m: float) -> float:
    """Convert vehicle speed (m/s) to wheel rotational speed (RPM)."""
    return (v / max(wheel_radius_m, 0.2)) * 60.0 / (2.0 * np.pi)


def get_gear_ratio(car: dict, gear_index: int) -> float:
    """Look up the transmission ratio for the given gear (0-indexed), clamped to valid range."""
    ratios = car["ice"]["gear_ratios"]
    idx = int(np.clip(gear_index, 0, len(ratios) - 1))
    return ratios[idx]


# ── Schema → runtime adapter ──────────────────────────────────────────────────

def make_car(name: str, spec: dict) -> dict:
    """
    Map the typed ``car_specs`` schema to the flat runtime structure used by
    the solver.

    Parameters
    ----------
    name : str
        Dictionary key / display name used as the car identifier.
    spec : dict
        One entry from the ``car_specs`` configuration dict, following the
        ``Car → Powertrain → Motor / Gearbox`` schema documented in the README.

    Returns
    -------
    dict
        Flat runtime representation ready for ``simulate_quarter_mile``.
    """
    vehicle = spec["vehicle"]
    tire = vehicle["tire"]
    powertrain = spec["powertrain"]

    drivetrain = powertrain["driving_axles"].upper()
    tire_factor = tire_grip_multiplier(tire["width_mm"], tire.get("compound", "summer"))

    car: dict = {
        "name": spec.get("name", name),
        "powertrain_type": powertrain["type"].upper(),
        "mass": float(vehicle["mass"]),
        "drivetrain": drivetrain,
        "CdA": float(vehicle["CdA"]),
        "wheel_radius_m": float(vehicle.get("wheel_radius_m", 0.34)),
        "rolling_resistance": float(vehicle.get("rolling_resistance", 0.015)),
        "mu": float(tire.get("base_mu", 1.05)) * tire_factor,
        "drive_factor": DRIVETRAIN_BASE[drivetrain]["drive_factor"],
        "tire_width_mm": float(tire["width_mm"]),
        "tire_compound": tire.get("compound", "summer"),
    }

    motors = powertrain.get("motors", [])
    gearbox = powertrain.get("gearbox", {})
    efficiency = powertrain.get("efficiency", {})

    if car["powertrain_type"] == "ICE":
        engine = motors[0]
        car["ice"] = {
            "gearbox_type": gearbox.get("type", "auto").lower(),
            "gear_ratios": [float(x) for x in gearbox.get("gear_ratios", [3.0, 2.0, 1.4, 1.0])],
            "final_drive": float(gearbox.get("final_drive", 3.5)),
            "idle_rpm": float(engine.get("min_rpm", 900)),
            "launch_rpm": float(gearbox.get("launch_rpm", engine.get("min_rpm", 900))),
            "shift_rpm": float(gearbox.get("shift_rpm", engine.get("max_rpm", 7000))),
            "redline_rpm": float(engine.get("max_rpm", 7000)),
            "shift_time_s": float(gearbox.get("shift_time_s", 0.30)),
            "engine_efficiency": float(efficiency.get("engine", 0.36)),
            "driveline_efficiency": float(efficiency.get("driveline", 0.90)),
            "torque_curve_rpm_nm": engine["torque_curve_rpm_nm"],
        }

    if car["powertrain_type"] == "BEV":
        motor = motors[0]
        car["motor"] = {
            "single_speed_ratio": float(gearbox.get("ratio", 9.0)),
            "max_rpm": float(motor.get("max_rpm", 18000)),
            "motor_efficiency": float(efficiency.get("motor", 0.92)),
            "inverter_efficiency": float(efficiency.get("inverter", 0.96)),
            "torque_curve_rpm_nm": motor["torque_curve_rpm_nm"],
        }

    return car


# ── Simulation state ──────────────────────────────────────────────────────────

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


# ── Drivetrain force helpers ──────────────────────────────────────────────────

def ice_drive_force(v: float, car: dict, state: dict) -> float:
    """
    Compute instantaneous wheel force (N) for an ICE powertrain.

    Side-effect: updates ``state["engine_rpm"]``.
    """
    ice = car["ice"]
    ratio = get_gear_ratio(car, state["gear_index"])
    fd = ice["final_drive"]
    engine_rpm = wheel_rpm_from_speed(v, car["wheel_radius_m"]) * ratio * fd
    if v < 1.5:
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
    return wheel_torque / max(car["wheel_radius_m"], 0.2)


def motor_drive_force(v: float, car: dict, state: dict) -> float:
    """
    Compute instantaneous wheel force (N) for a BEV powertrain.

    Side-effect: updates ``state["motor_rpm"]``.
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
    return wheel_torque / max(car["wheel_radius_m"], 0.2)


def _maybe_schedule_shift(v: float, car: dict, state: dict) -> None:
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


def propulsion_force(v: float, car: dict, state: dict, dt_step: float) -> float:
    """
    Return net propulsion force (N) for the current timestep.

    Handles the zero-power shift window for manual gearboxes.
    """
    if car["powertrain_type"] == "ICE":
        if state["in_shift"]:
            state["shift_timer_s"] -= dt_step
            if state["shift_timer_s"] <= 0.0:
                state["in_shift"] = False
                state["gear_index"] = state["pending_gear_index"]
            return 0.0
        force = ice_drive_force(v, car, state)
        _maybe_schedule_shift(v, car, state)
        return force
    if car["powertrain_type"] == "BEV":
        return motor_drive_force(v, car, state)
    return 0.0


def acceleration_and_state(v: float, car: dict, state: dict, dt_step: float) -> float:
    """
    Compute net longitudinal acceleration (m/s²), accounting for traction limit,
    aerodynamic drag, and rolling resistance.
    """
    drive_force = propulsion_force(v, car, state, dt_step)
    traction_force_max = car["mu"] * car["mass"] * G * car["drive_factor"]
    usable_force = min(drive_force, traction_force_max)
    drag_force = 0.5 * RHO_AIR * car["CdA"] * v ** 2
    rolling_force = car["rolling_resistance"] * car["mass"] * G
    net_force = usable_force - drag_force - rolling_force
    return net_force / car["mass"]


# ── Main simulation entry point ───────────────────────────────────────────────

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

    times:        list = [t]
    distances:    list = [x]
    speeds:       list = [v]
    accels:       list = [0.0]
    gears:        list = [state["gear_index"] + 1]
    engine_rpms:  list = [0.0]
    motor_rpms:   list = [0.0]
    wheel_torques: list = [0.0]

    while x < distance_target and t <= 60.0:
        a = acceleration_and_state(v, car, state, dt)

        # Record wheel torque at current state (before advancing v)
        if car["powertrain_type"] == "ICE":
            ice = car["ice"]
            ratio = get_gear_ratio(car, state["gear_index"])
            fd = ice["final_drive"]
            engine_torque = interp_curve(ice["torque_curve_rpm_nm"], state["engine_rpm"])
            wheel_torque = (
                engine_torque * ratio * fd
                * ice["engine_efficiency"]
                * ice["driveline_efficiency"]
            )
        elif car["powertrain_type"] == "BEV":
            motor = car["motor"]
            ratio = motor["single_speed_ratio"]
            motor_torque = interp_curve(motor["torque_curve_rpm_nm"], state["motor_rpm"])
            wheel_torque = (
                motor_torque * ratio
                * motor["motor_efficiency"]
                * motor["inverter_efficiency"]
            )
        else:
            wheel_torque = 0.0

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
