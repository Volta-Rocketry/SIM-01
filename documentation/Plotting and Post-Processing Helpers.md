# Plotting and Post-Processing Helpers

**Module:** `src/sims`

---

## 1. Purpose

This document describes the helper functions available in `src/sims` for post-processing and visualization preparation of completed flight simulations. These utilities extract raw data from RocketPy `Flight` objects and return it in formats ready for direct use in plotting libraries or further analysis pipelines.

These helpers are strictly read-only with respect to simulation state. They do not modify the `Flight` object, do not re-run any simulation logic, and have no side effects. They are designed to be called independently after a simulation has completed.

---

## 2. Design Principle: Separation of Simulation and Post-Processing

The simulation core (`File_simulation`) is responsible for constructing and executing flights. Post-processing helpers are responsible for extracting and reshaping data from completed results. These two concerns must remain separate:

- Helpers receive a completed `Flight` instance as input.
- Helpers return plain Python or NumPy data structures.
- No RocketPy API calls that trigger computation should be made inside helpers beyond attribute or array access.
- Helpers must be usable independently of `File_simulation` — any completed RocketPy `Flight` object is a valid input.

---

## 3. External Dependencies

| Dependency | Usage |
|------------|-------|
| `rocketpy.Flight` | Input type for all helpers. Must be a completed simulation object. |
| `numpy` | Implicit — RocketPy function sources (`.source`) return NumPy arrays. |

No additional imports are required beyond what is already present in `src/sims`.

---

## 4. Function Reference

---

### 4.1 `extract_map_data`

#### Signature

```python
extract_map_data(sim)
```

#### Purpose

Extracts the geographic trajectory of the rocket as parallel arrays of latitude and longitude values sampled across the full flight duration. The output is intended for geographic trajectory plotting, such as overlaying the flight path on a map or computing the ground track.

#### Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `sim` | `rocketpy.Flight` | Completed RocketPy Flight simulation object. Must have run to at least partial flight (rail exit or beyond). |

#### Output

| Name | Type | Unit | Description |
|------|------|------|-------------|
| `latitudes` | array-like | degrees | Latitude values sampled along the flight trajectory. |
| `longitudes` | array-like | degrees | Longitude values sampled along the flight trajectory. |

Both arrays are returned as a tuple `(latitudes, longitudes)` and share the same length and index correspondence — element `i` of `latitudes` corresponds to element `i` of `longitudes`.

#### Output Format

```python
latitudes, longitudes = extract_map_data(sim)
# latitudes  -> array of shape (N,), values in decimal degrees
# longitudes -> array of shape (N,), values in decimal degrees
```

The arrays are sourced directly from `sim.latitude_array` and `sim.longitude_array`, which RocketPy populates during simulation execution at each recorded time step.

#### Intended Use Cases

- Plotting the rocket ground track on a geographic map (e.g. using `matplotlib`, `folium`, or `plotly`).
- Computing total horizontal displacement from launch to impact.
- Overlaying multiple simulation trajectories for dispersion analysis.

#### Example

```python
sim = File_simulation("AURORA_v02", "AeroTech_N2000W")
sim.run_single_flight_sim(env=env, rail_length=5.2, inclination=0, heading=90)

latitudes, longitudes = extract_map_data(sim.single_flight_sim)

import matplotlib.pyplot as plt
plt.plot(longitudes, latitudes)
plt.xlabel("Longitude [deg]")
plt.ylabel("Latitude [deg]")
plt.title("Rocket Ground Track")
plt.show()
```

#### Notes

- `sim.latitude_array` and `sim.longitude_array` are pre-computed arrays stored by RocketPy at the end of the simulation. They are not callable functions — they are accessed as attributes, not evaluated at specific time values.
- The sampling resolution of the arrays depends on RocketPy's internal integration time step and is not configurable through this helper.

---

### 4.2 `extract_rb_ind`

#### Signature

```python
extract_rb_ind(sim)
```

#### Purpose

Extracts the time history of normal and shear forces acting on both rail buttons (upper and lower) during the launch rail phase. The output is intended for structural load analysis and plotting of rail button force profiles over time.

Rail buttons are the mechanical interface between the rocket and the launch rail. They experience significant normal and shear loading during the powered rail phase due to thrust misalignment, wind-induced angle of attack, and rail friction. This helper provides the raw time-series data needed to evaluate those loads.

#### Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `sim` | `rocketpy.Flight` | Completed RocketPy Flight simulation object. Must include a rail phase with recorded rail button force data. |

#### Output

| Name | Type | Unit | Description |
|------|------|------|-------------|
| `t` | `numpy.ndarray` | s | Time array corresponding to all force samples. |
| `rb1_normal_force` | `numpy.ndarray` | N | Normal force on the upper rail button over time. |
| `rb1_shear_force` | `numpy.ndarray` | N | Shear force on the upper rail button over time. |
| `rb2_normal_force` | `numpy.ndarray` | N | Normal force on the lower rail button over time. |
| `rb2_shear_force` | `numpy.ndarray` | N | Shear force on the lower rail button over time. |

All five arrays share the same length and time index. Returned as a tuple `(t, rb1_normal_force, rb1_shear_force, rb2_normal_force, rb2_shear_force)`.

#### Output Format

```python
t, rb1_nf, rb1_sf, rb2_nf, rb2_sf = extract_rb_ind(sim)
# t      -> array of shape (N,), time in seconds
# rb1_nf -> array of shape (N,), upper button normal force in Newtons
# rb1_sf -> array of shape (N,), upper button shear force in Newtons
# rb2_nf -> array of shape (N,), lower button normal force in Newtons
# rb2_sf -> array of shape (N,), lower button shear force in Newtons
```

Force arrays are extracted from the `.source` attribute of the corresponding RocketPy `Function` objects, which stores the raw `(time, value)` pairs as a 2D NumPy array. Column 0 is time, column 1 is the force value:

```python
rb1_normal_force = sim.rail_button1_normal_force.source[:, 1]
t                = sim.rail_button1_normal_force.source[:, 0]
```

#### Intended Use Cases

- Plotting normal and shear force time histories for both rail buttons on a single figure to assess load asymmetry.
- Comparing peak rail button loads across multiple simulations in a parametric study.
- Validating that rail button forces remain within structural limits during launch.
- Input to fatigue or margin-of-safety calculations for rail button design.

#### Example

```python
t, rb1_nf, rb1_sf, rb2_nf, rb2_sf = extract_rb_ind(sim.single_flight_sim)

import matplotlib.pyplot as plt
fig, axes = plt.subplots(2, 2, figsize=(10, 6))

axes[0, 0].plot(t, rb1_nf)
axes[0, 0].set_title("Upper Button — Normal Force")
axes[0, 0].set_ylabel("Force [N]")

axes[0, 1].plot(t, rb1_sf)
axes[0, 1].set_title("Upper Button — Shear Force")

axes[1, 0].plot(t, rb2_nf)
axes[1, 0].set_title("Lower Button — Normal Force")
axes[1, 0].set_ylabel("Force [N]")
axes[1, 0].set_xlabel("Time [s]")

axes[1, 1].plot(t, rb2_sf)
axes[1, 1].set_title("Lower Button — Shear Force")
axes[1, 1].set_xlabel("Time [s]")

plt.tight_layout()
plt.show()
```

#### Notes

- Force data is only physically meaningful during the rail phase (from launch to rail exit). RocketPy may record near-zero values after rail exit — verify against `sim.out_of_rail_time` if the analysis is restricted to the rail phase.
- `rb1` refers to the **upper** rail button and `rb2` to the **lower** rail button, consistent with the position convention in `File_simulation.create_rocket()` where `rail_button1` is set at `upper_position` and `rail_button2` at `upper_position + distance`.
- The `.source` attribute is a NumPy array internal to RocketPy's `Function` class. It is not part of the public API and may change across RocketPy versions.

---

## 5. Independent Usage

Both helpers are fully independent of `File_simulation`. Any completed RocketPy `Flight` object can be passed directly:

```python
from rocketpy import Flight, Rocket, SolidMotor, Environment
from src.sims import extract_map_data, extract_rb_ind

# Assuming `flight` is any completed Flight instance
latitudes, longitudes = extract_map_data(flight)
t, rb1_nf, rb1_sf, rb2_nf, rb2_sf = extract_rb_ind(flight)
```

Neither helper modifies the `Flight` object or triggers re-computation of any simulation quantity.

---

## 6. Notes and Constraints

- Both helpers assume the simulation has run to completion. Passing a `Flight` object that was interrupted or raised an exception during execution may produce incomplete or misaligned arrays.
- Array lengths depend on RocketPy's internal time step and are not guaranteed to be identical between `extract_map_data` and `extract_rb_ind` for the same simulation, since geographic arrays and force function sources may be sampled at different resolutions internally.
- Units are not embedded in array values. Units must be tracked externally by the caller, consistent with the project CSV standards.
- Neither helper performs unit conversion, resampling, or filtering. Any such transformations are the responsibility of the calling code.