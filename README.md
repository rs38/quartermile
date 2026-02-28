# Quarter-Mile Race Notebook (RWD vs AWD)

## try it out: 
https://rs38.github.io/quartermile/lab/index.html?path=quarter_mile_race.ipynb


This project contains a Jupyter notebook that simulates a standing-start quarter-mile race (402.336 m) between configurable cars.

- Notebook: `quarter_mile_race.ipynb` – configuration, plots, and interactive exploration
- Physics module: `quarter_mile_sim.py` – all reusable business logic (importable in CPython and JupyterLite / Pyodide WASM)
- Main scenario: one ICE car vs one BEV car
- Outputs: elapsed time, trap speed, acceleration behavior, wheel torque behavior, and race curves

## Project Structure

| File | Purpose |
|---|---|
| `quarter_mile_race.ipynb` | Interactive notebook – edit car specs, re-run cells, view plots |
| `quarter_mile_sim.py` | Reusable physics engine – constants, schema adapter, simulator |

`quarter_mile_sim.py` exposes:
- **Constants**: `G`, `RHO_AIR`, `QUARTER_MILE_M`, `DEFAULT_DT`, `DRIVETRAIN_BASE`, `TIRE_COMPOUND_GRIP`
- **Helpers**: `tire_grip_multiplier`, `interp_curve`, `wheel_rpm_from_speed`
- **Adapter**: `make_car(name, spec)` – maps the typed `car_specs` schema to a runtime dict
- **Simulator**: `simulate_quarter_mile(car, dt, distance_target)` – forward-Euler integration

## Notebook Structure

`quarter_mile_race.ipynb` is organized into these cells:

1. **Intro**: purpose and what can be customized
2. **Imports**: `numpy`, `matplotlib`, and `from quarter_mile_sim import …`
3. **Configuration (`car_specs`)**: typed schema for each car
4. **Build cars**: `cars = {name: make_car(name, spec) for …}`
5. **Results summary**: ET/trap speed and winner
6. **Acceleration + Wheel Torque vs Speed**
7. **Power Curve (HP vs RPM)**
8. **Race Plots**: distance-time and speed-time
9. **Notes**

## Configuration Schema (Typed)

The configuration in Cell 3 follows this model:

- **Car**
  - `name`
  - `vehicle`
  - `powertrain`

- **Vehicle**
  - `mass` (kg)
  - `CdA` (m²)
  - `wheel_radius_m` (m)
  - `rolling_resistance` (dimensionless)
  - `tire`

- **Tire**
  - `width_mm`
  - `compound` (`all_season`, `summer`, `track`, `drag_radial`)
  - `base_mu` (base traction coefficient)

- **Powertrain**
  - `type` (`ICE` or `BEV`)
  - `driving_axles` (`RWD` or `AWD`)
  - `efficiency` (dict)
  - `motors` (list of motor/engine definitions)
  - `gearbox` (gearbox definition)

- **Motor / Engine definition** (inside `motors` list)
  - `name`
  - `min_rpm`
  - `max_rpm`
  - `torque_curve_rpm_nm` as `[[rpm, Nm], ...]`

- **Gearbox**
  - For ICE:
    - `type` (`manual` or `auto`)
    - `gear_ratios` (list)
    - `final_drive`
    - `launch_rpm`
    - `shift_rpm`
    - `shift_time_s`
  - For BEV:
    - `type` (`single_speed`)
    - `ratio`

### Runtime Adapter

The function `make_car(name, spec)` in `quarter_mile_sim.py` maps this typed schema into the internal runtime structure used by the solver (`ice` or `motor` blocks, plus normalized drivetrain/tire fields).
Cell 4 of the notebook calls it as `cars = {name: make_car(name, spec) for name, spec in car_specs.items()}`.

## Math and Physics Model

The simulation is a forward Euler integration with timestep `dt` until distance reaches quarter-mile.

### 1) Wheel and Motor/Engine Speed

- Wheel RPM from vehicle speed:

  \[
  \text{wheel\_rpm} = \frac{v}{r_w} \cdot \frac{60}{2\pi}
  \]

- ICE engine RPM:

  \[
  \text{engine\_rpm} = \text{wheel\_rpm} \cdot G_i \cdot G_f
  \]

- BEV motor RPM:

  \[
  \text{motor\_rpm} = \text{wheel\_rpm} \cdot G_s
  \]

where:
- \(v\) = vehicle speed (m/s)
- \(r_w\) = wheel radius (m)
- \(G_i\) = selected gear ratio
- \(G_f\) = final drive
- \(G_s\) = single-speed ratio

### 2) Torque Curve Interpolation

Torque at current RPM is obtained by linear interpolation over `torque_curve_rpm_nm` points.

### 3) Wheel Torque and Drive Force

- ICE wheel torque:

  \[
  T_w = T_e \cdot G_i \cdot G_f \cdot \eta_e \cdot \eta_d
  \]

- BEV wheel torque:

  \[
  T_w = T_m \cdot G_s \cdot \eta_m \cdot \eta_i
  \]

- Drive force:

  \[
  F_{drive} = \frac{T_w}{r_w}
  \]

### 4) Traction Limit

Max usable tractive force:

\[
F_{traction,max} = \mu \cdot m \cdot g \cdot f_{drive}
\]

Used force:

\[
F_{usable} = \min(F_{drive}, F_{traction,max})
\]

where:
- \(\mu\) is adjusted by tire width and compound
- \(f_{drive}\) is drivetrain factor (`RWD` vs `AWD`)

### 5) Resistive Forces

- Aerodynamic drag:

  \[
  F_{drag} = \frac{1}{2}\rho C_dA v^2
  \]

- Rolling resistance:

  \[
  F_{roll} = C_{rr} m g
  \]

### 6) Net Acceleration and Integration

\[
F_{net} = F_{usable} - F_{drag} - F_{roll}
\]

\[
a = \frac{F_{net}}{m}
\]

Euler update each timestep:

\[
v_{t+\Delta t} = \max(0, v_t + a\Delta t)
\]

\[
x_{t+\Delta t} = x_t + v_{t+\Delta t}\Delta t
\]

### 7) Shifting Logic (ICE)

- Upshift is scheduled when `engine_rpm >= shift_rpm`.
- `manual` gearbox applies a zero-drive-force window for `shift_time_s`.
- `auto` gearbox changes gear without zero-force shift window in this simplified model.

### 8) Power Plot Conversion

Power curve in HP uses torque and RPM:

\[
HP \approx \frac{T(\text{Nm}) \cdot RPM}{7745}
\]

## Assumptions / Simplifications

- 1D straight-line model (no yaw, no grade, no wind gusts)
- No thermal limits, SOC limits, battery voltage sag, or clutch-slip detail
- No wheelspin transient model beyond traction cap
- Single equivalent motor used for BEV force generation
- Shift behavior simplified to manual zero-power interval

## How to Use

1. Open `quarter_mile_race.ipynb`.
2. Edit `car_specs` in Cell 3.
3. Run cells top-to-bottom.
4. Compare ET/trap speed and plots.

## Notes for Future Extension

- Add true multi-motor BEV distribution by axle
- Add battery/SOC dependent power limits
- Add clutch-slip launch and more detailed automatic shift model
- Add road slope/wind inputs
