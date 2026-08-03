"""
sim/adapter.py – Schema-to-runtime adapter for vehicle specifications.
"""

from sim.constants import DRIVETRAIN_BASE
from sim.powertrain import tire_grip_multiplier


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
        ``Car → Powertrain → Motor / Gearbox`` schema.

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
