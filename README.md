# Quarter-Mile Race Notebook

## Try it out
https://rs38.github.io/quartermile/lab/index.html?path=quarter_mile_race.ipynb


This project contains a Jupyter notebook that simulates a standing-start quarter-mile race (402.336 m) between any two cars chosen from a built-in database.

- Notebook: `quarter_mile_race.ipynb` – interactive form UI for selecting and customising cars, with live plots
- Physics module: `quarter_mile_sim.py` – all reusable business logic (importable in CPython and JupyterLite / Pyodide WASM)
- Car database: 5 presets with identity-based names (Sport Coupe, Electric Sedan, Muscle Car, Electric Hypercar, Performance Wagon)
- Outputs: elapsed time, trap speed, acceleration behaviour, wheel torque behaviour, and race curves

## Project Structure

| Path | Purpose |
|---|---|
| `quarter_mile_race.ipynb` | Interactive notebook – select car presets, tweak parameters, run race |
| `quarter_mile_cars.py` | Vehicle preset database (`CAR_DATABASE`) |
| `quarter_mile_sim.py` | Physics engine facade (re-exports `sim` package for WASM/CPython compatibility) |
| `quarter_mile_ui.py` | UI facade (re-exports `ui` package for WASM/CPython compatibility) |
| `sim/` | Physics package (`constants.py`, `powertrain.py`, `adapter.py`, `engine.py`) |
| `ui/` | Presentation package (`forms.py`, `plots.py`) |
| `tests/` | Unit tests (`test_quarter_mile.py`) |

`quarter_mile_sim.py` exposes:
- **Constants**: `G`, `RHO_AIR`, `QUARTER_MILE_M`, `DEFAULT_DT`, `HP_TORQUE_FACTOR`, `DRIVETRAIN_BASE`, `TIRE_COMPOUND_GRIP`
- **Helpers**: `tire_grip_multiplier`, `interp_curve`, `wheel_rpm_from_speed`, `get_gear_ratio`
- **Adapter**: `make_car(name, spec)` – maps the typed `car_specs` schema to a runtime dict
- **Simulator**: `simulate_quarter_mile(car, dt, distance_target)` – forward-Euler numerical solver

## Notebook Structure

`quarter_mile_race.ipynb` is organized into these cells:

1. **Intro**: purpose and how to use the interactive form
2. **Imports**: `numpy`, `matplotlib`, `from quarter_mile_sim import …`, `from quarter_mile_ui import …`
3. **Car database (`CAR_DATABASE`)**: imported from `quarter_mile_cars.py`
4. **Interactive form + Run Race**: `ipywidgets` form for picking and tweaking two cars, a **▶ Run Race** button, and output area
5. **Notes**

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
The notebook's **Run Race** handler calls it as `cars = {n: make_car(n, s) for n, s in car_specs.items()}`.

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
2. Run all cells (the form auto-runs a race on first execution).
3. Select **Car 1** and **Car 2** from the preset dropdowns.
4. Optionally adjust mass, tire compound/width, and ICE shift parameters using the form controls.
5. Press **▶  Run Race** to re-run the simulation and update all charts.
6. To add a custom car, extend `CAR_DATABASE` in cell 3.

## Notes for Future Extension

- Add true multi-motor BEV distribution by axle
- Add battery/SOC dependent power limits
- Add clutch-slip launch and more detailed automatic shift model
- Add road slope/wind inputs
