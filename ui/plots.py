"""
ui/plots.py – Matplotlib plotting helpers and race output formatting.
"""

import numpy as np
import matplotlib.pyplot as plt

from sim.constants import QUARTER_MILE_M, HP_TORQUE_FACTOR
from sim.powertrain import interp_curve


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
        ax.plot(rpm_r, tq * rpm_r / HP_TORQUE_FACTOR, label=name, linewidth=2)
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


def run_race_output(
    cars: dict, results: dict, quarter_mile_m: float = QUARTER_MILE_M
) -> None:
    """Print race summary and display all three standard plots."""
    print_race_summary(cars, results)
    plot_accel_torque_vs_speed(cars, results)
    plot_power_curves(cars)
    plot_distance_speed_vs_time(results, quarter_mile_m)
