# Plan: Externalize CAR_DATABASE — Format & Normalization Suggestions

## TL;DR

The current `CAR_DATABASE` (90 lines of nested Python dicts) lives inline in the notebook. All three viable tabular formats — **CSV**, **SQLite**, and **JSON** — work in JupyterLite via co-located files and `open()` / `sqlite3` from stdlib. Below are three format options with trade-offs, followed by normalization suggestions for the 1:N relationships (motors, gear ratios, torque curves).

---

## A. Format Options

All formats below:
- Work in Pyodide (JupyterLite) when placed alongside the notebook
- Use only stdlib — no pandas needed
- Are read via standard `open()` or `sqlite3.connect()`

### Option 1: Multi-CSV (most "tabular")

Multiple `.csv` files, one per entity. Each references parents via a key column.

| File | Columns | Rows for current data |
|------|---------|----------------------|
| `cars.csv` | `name, mass, CdA, wheel_radius_m, rolling_resistance, powertrain_type, driving_axles, tire_ref, gearbox_ref` | 5 |
| `tires.csv` | `tire_id, width_mm, compound, base_mu` | 5 (or fewer if shared) |
| `motors.csv` | `motor_id, car_name, slot, name, min_rpm, max_rpm` | 5 |
| `torque_curves.csv` | `motor_id, rpm, torque_nm` | ~40 (7–9 points × 5 motors) |
| `gearboxes.csv` | `gearbox_id, type, final_drive, launch_rpm, shift_rpm, shift_time_s, single_speed_ratio` | 5 |
| `gear_ratios.csv` | `gearbox_id, gear_index, ratio` | ~34 (6–8 ratios × 3 ICE + 0 BEV) |
| `efficiencies.csv` | `car_name, engine, driveline, motor, inverter` | 5 |

**Pros:** Truly tabular, spreadsheet-editable, git-diffable, easy to display as DataFrames in the notebook.
**Cons:** 7 files to keep in sync; needs ~60 lines of assembly logic in `quarter_mile_sim.py` to JOIN them back into the `make_car()` input format. The 1:N joins (torque curves, gear ratios) require grouping.

**Reader:** `csv.DictReader` (stdlib, zero-cost).

### Option 2: SQLite (single-file relational)

One `cars.db` file with proper relational tables and foreign keys.

| Table | PK | FK |
|-------|----|----|
| `cars` | `name` | `tire_id → tires`, `gearbox_id → gearboxes` |
| `tires` | `tire_id` | — |
| `motors` | `motor_id` | `car_name → cars` |
| `torque_points` | `(motor_id, rpm)` | `motor_id → motors` |
| `gearboxes` | `gearbox_id` | — |
| `gear_ratios` | `(gearbox_id, gear_index)` | `gearbox_id → gearboxes` |

**Pros:** Single file, proper FK constraints, queryable (`SELECT ... JOIN`), typed columns.
**Cons:** Binary — not git-diffable or human-editable; needs a build/seed script to populate; overkill for 5 cars; harder to casually inspect.

**Reader:** `sqlite3` (stdlib, included in Pyodide WASM build).

### Option 3: JSON (closest to current structure)

One `car_database.json` file that mirrors the current nested dict structure.

```
car_database.json          # same shape as today's CAR_DATABASE dict
├── "Sport Coupe": { vehicle: {...}, powertrain: {...} }
├── "Electric Sedan": { ... }
└── ...
```

**Pros:** Zero assembly logic — `json.load()` produces the exact dict `make_car()` already expects. Smallest code change. Human-readable. Git-diffable.
**Cons:** Not tabular (nested hierarchy). Harder to edit in spreadsheet tools. No schema enforcement.

**Reader:** `json` (stdlib, zero-cost).

### Recommendation Matrix

| Criterion | CSV | SQLite | JSON |
|-----------|-----|--------|------|
| Truly tabular | **best** | **best** | no |
| Human-editable | spreadsheet | needs tool | text editor |
| Git-diffable | **yes** | no | **yes** |
| Assembly code needed | ~60 lines | ~40 lines (SQL) | ~2 lines |
| Schema enforcement | none | FK + types | none |
| Number of files | 7 | 1 | 1 |
| Pyodide compatible | **yes** | **yes** | **yes** |

---

## B. Normalization Suggestions for 1:N Relationships

The current data has these entity relationships:

```
Car ──1:1──▶ Vehicle ──1:1──▶ Tire
 │
 └──1:1──▶ Powertrain ──1:N──▶ Motor ──1:N──▶ TorqueCurvePoint
                │
                └──1:1──▶ Gearbox ──1:N──▶ GearRatio
                │
                └──1:1──▶ Efficiency
```

### Entity catalog approach (applicable to any format)

Extract reusable entities into named catalogs so multiple cars can reference the same motor, gearbox, or tire by key:

| Catalog | Example entries | Benefit |
|---------|----------------|---------|
| **Motors** | `"LS3_V8"`, `"Dual_EV_500kW"` | Same engine in Sport Coupe and a future Roadster variant |
| **Gearboxes** | `"Tremec_6MT"`, `"ZF_8HP"`, `"EV_Single_9.0"` | Same transmission shared across platforms |
| **Tires** | `"305_30_summer"`, `"325_track"` | Same tire package across cars |
| **Torque curves** | Embedded in motor (1:N points) | Always motor-specific, stays nested |
| **Efficiency profiles** | `"ice_street"`, `"bev_high"` | Avoid duplicating identical efficiency values |

A car entry then becomes a lightweight composition of references:

```
"Sport Coupe":
    motor_ref: "ICE_Inline6_860"
    gearbox_ref: "Manual_6spd_373"
    tire_ref: "305_summer_110"
    efficiency_ref: "ice_street"
    mass: 1500, CdA: 0.66, ...
```

A `resolve_car(name, catalogs)` function in `quarter_mile_sim.py` would dereference the keys and assemble the full spec dict that `make_car()` already expects.

### How each format handles the 1:N patterns

| Relationship | CSV | SQLite | JSON |
|-------------|-----|--------|------|
| Car → Motor (1:N) | Separate `motors.csv` with `car_name` FK | `motors` table with FK | Nested `"motors": [...]` list |
| Motor → TorqueCurve (1:N) | Separate `torque_curves.csv` with `motor_id` FK | `torque_points` table | Nested `"torque_curve_rpm_nm": [[...]]` |
| Gearbox → GearRatios (1:N) | Separate `gear_ratios.csv` with `gearbox_id` FK | `gear_ratios` table | Nested `"gear_ratios": [...]` |
| Shared motors across cars | Same `motor_id` in multiple car rows | FK join | `"motor_ref": "key"` + catalogue dict |

### Future multi-motor BEV consideration

The README mentions "multi-motor BEV distribution by axle" as a future feature. Today `motors[0]` is all that's read. With normalization:
- **CSV/SQLite:** add a `slot` column (`"front"`, `"rear"`) to the motors table — no schema change needed
- **JSON:** the existing `motors` list naturally extends to multiple entries with an added `"axle"` field

---

## Steps (if implementing)

1. Choose a format (above)
2. Create the data file(s) alongside the notebook — e.g. `data/car_database.json` or `data/*.csv`
3. Add a `load_car_database(path)` function to `quarter_mile_sim.py` that reads and returns the dict
4. If using catalogs: add a `resolve_car_refs(car_spec, catalogs)` function that dereferences keys
5. Replace the `CAR_DATABASE = {...}` literal in the notebook with a one-liner: `CAR_DATABASE = load_car_database("data/car_database.json")`
6. Co-locate the data files in the JupyterLite deployment root so Pyodide can `open()` them

## Verification

- Run all notebook cells and confirm the interactive form + plots work identically
- Test in JupyterLite (`jupyter lite build && jupyter lite serve`) to verify file access from Pyodide
