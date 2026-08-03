"""
quarter_mile_ui.py – ipywidgets form builder and matplotlib plotting facade.

All UI and visualization logic lives in the `ui` package. This module acts
as a backward-compatible facade for existing notebooks and Pyodide / WASM deployments.

Compatibility: standard CPython, JupyterLab, JupyterLite / Pyodide (WASM).
"""

from ui import (
    make_car_form,
    plot_accel_torque_vs_speed,
    plot_power_curves,
    plot_distance_speed_vs_time,
    print_race_summary,
    run_race_output,
)

__all__ = [
    "make_car_form",
    "plot_accel_torque_vs_speed",
    "plot_power_curves",
    "plot_distance_speed_vs_time",
    "print_race_summary",
    "run_race_output",
]
