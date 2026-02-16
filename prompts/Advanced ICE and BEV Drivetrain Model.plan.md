Plan: Advanced ICE/BEV Drivetrain Model (DRAFT)
This plan upgrades the notebook from a constant-power approximation to a stateful quarter-mile model with realistic drivetrain behavior, while preserving your current UX: one specs cell and the final combined race plots. Based on your decisions, scope is ICE + BEV (PHEV skipped), manual shifts apply zero wheel power during shift time, ICE launch uses a simple clutch heuristic, and acceleration-vs-speed will be derived from time-simulated samples (including shift effects). The refactor stays localized to the existing notebook flow in quarter_mile_race.ipynb, so you still edit inputs in one place and run cells top-to-bottom.

Steps

Update notebook documentation text in quarter_mile_race.ipynb:10-23 and quarter_mile_race.ipynb:244-248 to reflect new scope (ICE + BEV), gearbox shift-time behavior, and wheel-efficiency losses.
Redesign the single input cell in quarter_mile_race.ipynb:50-72 so each car spec includes powertrain_type, wheel_radius_m, driveline efficiencies, and nested config blocks:
ICE block: torque_curve_rpm_nm, idle_rpm, redline_rpm, gear_ratios, final_drive, shift_rpm, shift_time_s, gearbox_type.
BEV block: motor_torque_curve_rpm_nm or torque_plateau_nm + base_rpm, max_motor_rpm, single-speed ratio, and motor efficiency.
Refactor model cell logic in quarter_mile_race.ipynb:82-166 by splitting acceleration into modular helpers:
curve interpolation (interp_curve)
speed→wheel rpm→engine/motor rpm mapping
source torque/power at current rpm
wheel force from gear ratio and driveline efficiency
traction clamp + aero drag subtraction.
Replace scalar-only race dynamics with stateful simulation in simulate_quarter_mile: track gear_index, in_shift, shift_timer_s, rpm, and append state histories each timestep for plotting/diagnostics.
Implement manual shift model: when upshift condition triggers (rpm >= shift_rpm), set in_shift=True; apply zero wheel drive force until shift_timer_s >= shift_time_s; then engage next gear.
Implement ICE launch heuristic: enforce minimum launch rpm behavior at very low speed using clutch-slip approximation, then transition to normal rpm mapping once wheel speed rises.
Apply drivetrain efficiency consistently so delivered wheel power/force is lower than engine or motor output (engine/motor efficiency × gearbox/final-drive efficiency chain).
Update results/plots cells in quarter_mile_race.ipynb:176-185, quarter_mile_race.ipynb:195-207, and quarter_mile_race.ipynb:217-234:
print ET/trap plus shift count and final gear
acceleration plot uses time-simulated (speed, accel) samples
keep final cell as the combined distance-time and speed-time plots.
Verification

Run cells in order (Cells 2→7) and confirm no errors.
Confirm manual car shows visible acceleration dips during shifts in sampled acceleration behavior.
Confirm wheel output changes when efficiency values are adjusted.
Sanity checks: unrealistic top speed/accel does not occur at high rpm; BEV transitions from torque-rich launch to power-limited behavior.
Decisions

Shift behavior: zero wheel power for full manual shift time.
ICE launch: simple clutch heuristic (not full clutch dynamics).
Powertrain scope: ICE + BEV only; PHEV excluded.
Acceleration plot definition: time-simulated acceleration samples (state/shift dependent).