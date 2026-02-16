# Advanced ICE/BEV Drivetrain Model Plan

This plan upgrades the notebook from a constant-power approximation to a stateful quarter-mile model with realistic drivetrain behavior, while preserving the existing UX: one specs cell and the final combined race plots.

## Scope and decisions
- Powertrain scope: ICE + BEV only (PHEV excluded)
- Manual shift behavior: zero wheel power during full `shift_time_s`
- ICE launch model: simple clutch heuristic near launch RPM
- Acceleration plot definition: time-simulated acceleration samples

## Steps
1. Update notebook text to reflect ICE + BEV scope, shift-time behavior, and efficiency losses.
2. Keep a single input cell with nested per-car specs:
   - ICE: torque curve, gear ratios, final drive, idle/launch/redline/shift RPM, shift time
   - BEV: motor torque curve, single-speed ratio, max motor RPM, efficiencies
3. Refactor model into modular helpers:
   - curve interpolation
   - speed→wheel RPM→engine/motor RPM mapping
   - source torque lookup and wheel-force calculation
   - traction clamp + drag/rolling resistance
4. Use stateful simulation (`gear_index`, `in_shift`, `shift_timer_s`) for quarter-mile run.
5. Apply drivetrain efficiency so wheel output is lower than source output.
6. Update result summaries and keep final combined race plots.

## Verification
- Execute cells in order and confirm no errors.
- Confirm manual cars show shift-related acceleration dips.
- Confirm changing efficiency values changes ET/trap speed.
- Confirm BEV transitions from strong low-speed force to high-speed taper.

## Notes
- The model is intentionally simplified (no full clutch thermals or battery SOC depletion model).
- Parameters are tunable in one place (`car_specs`) for quick scenario testing.
