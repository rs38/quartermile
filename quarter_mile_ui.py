"""
quarter_mile_ui.py – ipywidgets form builder and matplotlib plotting helpers
for the quarter-mile notebook.

All notebook-facing UI and visualisation logic lives here so the notebook
itself stays focused on configuration and exploration.

Compatibility: standard CPython, JupyterLab, JupyterLite / Pyodide (WASM).
Requires ipywidgets and matplotlib in addition to numpy.
"""

import copy

import numpy as np
import matplotlib.pyplot as plt
import ipywidgets as widgets

from quarter_mile_sim import interp_curve, QUARTER_MILE_M

_TIRE_COMPOUNDS = ["all_season", "summer", "track", "drag_radial"]


# ── Form builder ──────────────────────────────────────────────────────────────

def make_car_form(slot_label: str, default_key: str, car_database: dict):
    """
    Build an ipywidgets form for one car slot.

    Parameters
    ----------
    slot_label : str
        Label shown next to the preset dropdown (e.g. ``"Car 1"``).
    default_key : str
        Key in *car_database* to select on load.
    car_database : dict
        The car preset dictionary (e.g. ``CAR_DATABASE`` from the notebook).

    Returns
    -------
    tuple[widgets.VBox, callable]
        ``(box_widget, get_spec_fn)`` where ``get_spec_fn()`` returns
        ``(name, spec_dict)`` reflecting the current widget values.
    """
    db_keys = list(car_database.keys())
    preset_dd = widgets.Dropdown(
        options=db_keys, value=default_key,
        description=f"{slot_label}:",
        style={"description_width": "50px"},
        layout=widgets.Layout(width="210px"),
    )
    pt_label = widgets.Label(layout=widgets.Layout(margin="2px 0 0 8px"))
    mass_txt = widgets.FloatText(
        description="Mass (kg):",
        style={"description_width": "80px"}, layout=widgets.Layout(width="220px"),
    )
    cmpd_dd = widgets.Dropdown(
        options=_TIRE_COMPOUNDS, description="Tire cmpd:",
        style={"description_width": "80px"}, layout=widgets.Layout(width="220px"),
    )
    tirw_sl = widgets.IntSlider(
        min=185, max=345, step=5, description="Width (mm):",
        style={"description_width": "80px"}, layout=widgets.Layout(width="310px"),
    )
    # ICE-only widgets
    lrpm_sl = widgets.IntSlider(
        min=500, max=4000, step=100, description="Launch RPM:",
        style={"description_width": "90px"}, layout=widgets.Layout(width="310px"),
    )
    srpm_sl = widgets.IntSlider(
        min=3000, max=8500, step=100, description="Shift RPM:",
        style={"description_width": "90px"}, layout=widgets.Layout(width="310px"),
    )
    stim_sl = widgets.FloatSlider(
        min=0.05, max=0.60, step=0.05, readout_format=".2f",
        description="Shift time s:",
        style={"description_width": "90px"}, layout=widgets.Layout(width="310px"),
    )
    ice_vbox = widgets.VBox([lrpm_sl, srpm_sl, stim_sl])

    def _populate(key: str) -> None:
        spec = car_database[key]
        pt = spec["powertrain"]
        pt_label.value = f"  {pt['type'].upper()} · {pt['driving_axles'].upper()}"
        mass_txt.value = spec["vehicle"]["mass"]
        cmpd_dd.value = spec["vehicle"]["tire"].get("compound", "summer")
        tirw_sl.value = spec["vehicle"]["tire"]["width_mm"]
        is_ice = pt["type"].upper() == "ICE"
        ice_vbox.layout.display = "" if is_ice else "none"
        if is_ice:
            gb = pt["gearbox"]
            m0 = pt.get("motors", [{}])[0]
            lrpm_sl.value = gb.get("launch_rpm", m0.get("min_rpm", 900))
            srpm_sl.value = gb.get("shift_rpm", m0.get("max_rpm", 7000))
            stim_sl.value = gb.get("shift_time_s", 0.30)

    _populate(default_key)
    preset_dd.observe(lambda ch: _populate(ch["new"]), names="value")

    def get_spec():
        key = preset_dd.value
        spec = copy.deepcopy(car_database[key])
        spec["vehicle"]["mass"] = mass_txt.value
        spec["vehicle"]["tire"]["compound"] = cmpd_dd.value
        spec["vehicle"]["tire"]["width_mm"] = tirw_sl.value
        if spec["powertrain"]["type"].upper() == "ICE":
            gb = spec["powertrain"]["gearbox"]
            gb["launch_rpm"] = lrpm_sl.value
            gb["shift_rpm"] = srpm_sl.value
            gb["shift_time_s"] = stim_sl.value
        return key, spec

    box = widgets.VBox(
        [widgets.HBox([preset_dd, pt_label]), mass_txt, cmpd_dd, tirw_sl, ice_vbox],
        layout=widgets.Layout(
            border="1px solid #ccc", padding="8px",
            margin="4px", min_width="340px",
        ),
    )
    return box, get_spec


# ── Plot helpers ──────────────────────────────────────────────────────────────

def plot_accel_torque_vs_speed(cars: dict, results: dict) -> None:
    """Plot acceleration (primary y-axis) and wheel torque (secondary) vs speed."""
    fig, ax1 = plt.subplots(figsize=(10, 4))
    ax2 = ax1.twinx()
    c1, c2 = "tab:blue", "tab:red"
    ax1.set_xlabel("Speed (km/h)")
    ax1.set_ylabel("Acceleration (m/s²)", color=c1)
    ax2.set_ylabel("Wheel Torque (Nm)", color=c2)
    ax1.tick_params(axis="y", labelcolor=c1)
    ax2.tick_params(axis="y", labelcolor=c2)
    for name, r in results.items():
        spd = r["speed"] * 3.6
        order = np.argsort(spd)
        ax1.plot(spd[order], r["accel"][order], label=name, linewidth=2)
        ax2.plot(
            spd[order], r["wheel_torque"][order],
            label=f"{name} (torque)", linestyle="--", linewidth=2,
        )
    ax1.set_title("Acceleration and Wheel Torque vs Speed")
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")
    plt.tight_layout()
    plt.show()


def plot_power_curves(cars: dict) -> None:
    """Plot engine/motor power curves (HP vs RPM) for all cars."""
    fig, ax = plt.subplots(figsize=(10, 4))
    for name, car in cars.items():
        if car["powertrain_type"] == "ICE":
            rpm_r = np.linspace(0, car["ice"]["redline_rpm"], 150)
            tq = np.array([interp_curve(car["ice"]["torque_curve_rpm_nm"], r) for r in rpm_r])
        else:
            rpm_r = np.linspace(0, car["motor"]["max_rpm"], 150)
            tq = np.array([interp_curve(car["motor"]["torque_curve_rpm_nm"], r) for r in rpm_r])
        ax.plot(rpm_r, tq * rpm_r / 7745, label=name, linewidth=2)
    ax.set_xlabel("RPM")
    ax.set_ylabel("Power (HP)")
    ax.set_title("Power Curve vs RPM")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.show()


def plot_distance_speed_vs_time(
    results: dict, quarter_mile_m: float = QUARTER_MILE_M
) -> None:
    """Plot distance vs time and speed vs time side-by-side for all cars."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for name, r in results.items():
        axes[0].plot(r["time"], r["distance"], label=name)
        axes[1].plot(r["time"], r["speed"] * 3.6, label=name)
    axes[0].axhline(
        quarter_mile_m, linestyle="--", linewidth=1,
        color="k", alpha=0.7, label="Quarter mile",
    )
    axes[0].set_title("Distance vs Time")
    axes[0].set_xlabel("Time (s)")
    axes[0].set_ylabel("Distance (m)")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()
    axes[1].set_title("Speed vs Time")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Speed (km/h)")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    plt.tight_layout()
    plt.show()


# ── Summary printer ───────────────────────────────────────────────────────────

def print_race_summary(cars: dict, results: dict) -> None:
    """Print a one-line summary per car and announce the winner."""
    for name, r in results.items():
        car = cars[name]
        line = (
            f"{name} | {car['powertrain_type']} | {car['drivetrain']} |"
            f" {car['tire_width_mm']:.0f}mm {car['tire_compound']}"
        )
        if car["powertrain_type"] == "ICE":
            line += (
                f" | {car['ice']['gearbox_type']}"
                f" {len(car['ice']['gear_ratios'])}spd"
                f" | shifts={r['shift_count']}"
            )
        print(line)
        print(
            f"  mass={car['mass']:.0f} kg  →  ET={r['elapsed_time']:.2f} s,"
            f" trap={r['trap_speed']*3.6:.1f} km/h"
        )
    winner = min(results.items(), key=lambda kv: kv[1]["elapsed_time"])[0]
    print(f"\n🏁 Winner over quarter mile: {winner}")


# ── Combined race output ──────────────────────────────────────────────────────

def run_race_output(
    cars: dict, results: dict, quarter_mile_m: float = QUARTER_MILE_M
) -> None:
    """Print race summary and display all three standard plots."""
    print_race_summary(cars, results)
    plot_accel_torque_vs_speed(cars, results)
    plot_power_curves(cars)
    plot_distance_speed_vs_time(results, quarter_mile_m)
