# Wind Model Generators — Non-Symmetric and Variable Profiles

**Module:** `src/sims`

---

## 1. Purpose

This document describes the advanced wind profile generator functions available in `src/sims`. These generators produce atmospheric wind profiles with non-symmetric or variable behavior across altitude, intended for use in flight simulation parametric studies and dispersion analysis.

The functions documented here extend the basic constant-wind models by introducing angular variability, speed variability, or both, enabling more realistic atmospheric conditions in simulation runs.

---

## 2. Background: Non-Symmetric Wind Profiles

### 2.1 Definition

A **constant (symmetric)** wind model applies a single direction and speed uniformly at every altitude. A **non-symmetric** wind model departs from this uniformity in one or more of the following ways:

- The wind direction (angle) varies stochastically with altitude.
- The wind speed (magnitude) varies stochastically with altitude.
- Both direction and speed vary independently with altitude.

### 2.2 Mathematical Formulation

Wind is decomposed into two horizontal components following the meteorological convention:

```
u(z) = -v(z) * sin(θ(z))     [East-West component, positive Eastward]
v(z) = -v(z) * cos(θ(z))     [North-South component, positive Northward]
```

Where `z` is altitude [m], `v(z)` is wind speed [m/s], and `θ(z)` is wind direction [degrees, meteorological convention: 0° = North, 90° = East, 180° = South, 270° = West].

The negative signs arise from the meteorological convention, where the angle describes the direction the wind **comes from**, not the direction it flows toward.

### 2.3 Stochastic Variability Model

Variability is introduced as low-frequency filtered noise added to a base value. The process is:

1. White Gaussian noise `n ~ N(0,1)` is generated for each altitude sample.
2. A 2nd-order Butterworth low-pass filter with normalized cutoff frequency `f_c = 0.05` is applied, producing smooth spatially correlated variations.
3. The filtered noise is normalized to unit standard deviation, then scaled by turbulence intensity and absolute deviation.

For a base value `B` (speed or angle), the resulting profile at each altitude sample is:

```
X(z) = B + deviation * turbulence * n_filtered(z)
```

Where `turbulence` is a dimensionless relative intensity coefficient and `deviation` is an absolute scale factor in the same units as `X`.

### 2.4 Comparison with Constant Models

| Aspect | Constant Model | Non-Symmetric Model |
|--------|---------------|---------------------|
| Wind speed | Uniform at all altitudes | Varies with altitude (stochastic) |
| Wind direction | Uniform at all altitudes | Varies with altitude (stochastic) |
| Spatial correlation | Perfect (same everywhere) | Smooth (low-pass filtered noise) |
| Reproducibility | Deterministic | Stochastic (seeded by system RNG) |
| Use case | Baseline runs, sensitivity | Realistic dispersion and uncertainty analysis |
| Input complexity | Single angle and speed | Base value + turbulence + deviation |

---

## 3. Physical Interpretation

### 3.1 Why the Atmosphere Is Not Symmetric

In reality, the atmosphere is structured in layers — the troposphere, tropopause, and lower stratosphere — each with distinct thermal, pressure, and dynamic properties. Within each layer, wind is not a single uniform flow but the result of large-scale pressure gradients, the Coriolis effect, terrain interaction, and local thermal convection. This produces two observable phenomena that a constant model cannot capture:

**Wind shear** refers to the change in wind speed or direction with altitude. It is common for surface winds to blow at 5 m/s from the West while winds at 3,000 m blow at 15 m/s from the Southwest. For a rocket, wind shear means that the aerodynamic loads and drift change continuously throughout the ascent, not just at one fixed condition. The `generate_variable_wind_profile` function directly models this.

**Atmospheric turbulence** refers to irregular, spatially correlated fluctuations superimposed on the mean wind. Turbulence is not random from meter to meter — it has a characteristic length scale, meaning a gust sustained over hundreds of meters of altitude is physically realistic, while a direction that reverses every 10 m is not. The low-pass Butterworth filter in all three non-symmetric generators enforces this physical coherence: perturbations are smooth and correlated across altitude, not point-by-point noise.

### 3.2 Effect on Rocket Flight

Wind acts on the rocket primarily as a crosswind component relative to the rocket's velocity vector. The key aerodynamic consequence is the **angle of attack (AoA)**: any difference between the rocket's heading and the local airflow direction produces an AoA, which in turn generates a lateral aerodynamic force. This force causes the rocket to drift and, during the rail phase, loads the rail buttons.

The three non-symmetric models affect flight in distinct ways:

**`generate_cte_wind_nsy_angle`** — The wind magnitude is constant, but the direction rotates smoothly with altitude. As the rocket climbs through regions of different wind direction, the effective crosswind component changes sign and magnitude. This primarily affects the **lateral drift trajectory** and the **heading of impact point** without changing the total aerodynamic loading significantly, since speed is fixed.

**`generate_nsy_wind_nsy_angle`** — Both speed and direction vary. Speed variations directly alter the **dynamic pressure** of the crosswind component (`q = 0.5 * ρ * v²`), which scales the lateral aerodynamic force non-linearly. A gust at apogee with doubled wind speed produces four times the lateral force. This model is the appropriate choice when quantifying structural load uncertainty or impact dispersion due to gusty conditions.

**`generate_variable_wind_profile`** — Layered structure with independent turbulence per band. The most physically complete model. Wind shear between layers creates discrete changes in the crosswind environment as the rocket transits each boundary. This is relevant for predicting the **roll-averaged drift envelope**, evaluating **stability margin sensitivity** across the flight envelope, and characterizing **impact ellipse** orientation and size in dispersion Monte Carlo runs.

### 3.3 Role of the Low-Pass Filter

Real atmospheric turbulence has a **turbulence length scale** — the characteristic distance over which the wind field is correlated. For the lower troposphere (0–3,000 m) this scale is typically on the order of hundreds to thousands of meters. A white noise signal applied directly to each altitude sample would imply turbulence reversing direction every 10 m, which is unphysical.

The 2nd-order Butterworth filter with `f_c = 0.05` (normalized, applied over the 10 m altitude grid) suppresses variations with spatial periods shorter than approximately 200 m, retaining only large-scale coherent structures. This makes the simulated turbulence physically plausible for the scales relevant to a rocket flight (typically 0–10,000 m AGL during powered and coasting phases).

### 3.4 Constant Model vs. Non-Symmetric Model: Practical Impact

A constant wind model represents the **mean atmospheric state** and is appropriate for nominal performance analysis: apogee altitude, nominal drift, stability margins at defined conditions. It is deterministic and fast to interpret.

A non-symmetric model represents **one realization** of a stochastic atmosphere. A single run with a non-symmetric model is not more accurate than a constant model — it is a different scenario. The value emerges when running many realizations (Monte Carlo) and analyzing the **statistical distribution** of outputs: impact dispersion ellipse, apogee altitude spread, maximum AoA distribution, and rail exit velocity variance. Non-symmetric models must be used in ensembles, not in isolation.

---

## 4. Output Format and Simulation Compatibility

All three functions return a RocketPy `Environment` instance configured via `set_atmospheric_model("custom_atmosphere", ...)`. The wind U and V arrays are formatted as NumPy arrays of shape `(N, 2)`, where each row is `[altitude_m, wind_component_mps]`.

This output is directly compatible with `File_simulation.run_single_flight_sim()` and `File_simulation.run_multiple_flight_sims()`, which accept an `Environment` instance as the `env` parameter.

Units follow the project CSV standard: decimal separator is a dot (`.`), no units embedded in numeric values.

---

## 5. Function Reference

---

### 5.1 `generate_cte_wind_nsy_angle`

#### Signature

```python
generate_cte_wind_nsy_angle(lat, lon, elev, angle, speed, turbulence, deviation)
```

#### Purpose

Generates an atmospheric environment with **constant wind speed** at all altitudes but a **stochastically varying wind direction**. This isolates the effect of directional variability while keeping the wind magnitude fixed.

#### Parameters

| Parameter | Type | Unit | Description |
|-----------|------|------|-------------|
| `lat` | float | degrees | Launch site latitude. |
| `lon` | float | degrees | Launch site longitude. |
| `elev` | float | m | Launch site elevation above sea level. |
| `angle` | float | degrees | Base wind direction (meteorological convention, 0° = North). |
| `speed` | float | m/s | Wind speed magnitude, constant at all altitudes. |
| `turbulence` | float | dimensionless | Relative turbulence intensity coefficient. Scales the filtered noise amplitude. |
| `deviation` | float | degrees | Absolute deviation scale for the directional noise. Controls the maximum angular spread. |

#### Returns

A RocketPy `Environment` instance configured with a custom atmospheric model using the generated wind U and V component profiles.

#### Profile Generation Logic

1. Generate a full altitude grid from 0 to 79,990 m in 10 m increments (8,000 samples).
2. Generate white Gaussian noise of the same length and apply a 2nd-order Butterworth low-pass filter (cutoff = 0.05) to produce smooth, correlated angle variability.
3. Normalize the filtered signal to unit standard deviation and compute the perturbed angle:

   ```
   θ(z) = angle + deviation * turbulence * n_filtered(z)
   ```

4. Compute U and V components from the perturbed angle and the fixed speed:

   ```
   u(z) = -speed * sin(radians(θ(z)))
   v(z) = -speed * cos(radians(θ(z)))
   ```

5. Build the environment by calling `set_atmospheric_model` with the resulting altitude-indexed U and V arrays.

#### Example Profile

```python
env = generate_cte_wind_nsy_angle(
    lat=32.990254,
    lon=-106.974998,
    elev=1400,
    angle=270,       # Base wind from the West
    speed=8.0,       # 8 m/s constant
    turbulence=0.15, # 15% relative turbulence
    deviation=10.0   # +/- ~10 deg angular spread
)
```

In this example, wind blows primarily from the West at 8 m/s, but its direction fluctuates smoothly across altitude by approximately ±10–15 degrees.

---

### 5.2 `generate_nsy_wind_nsy_angle`

#### Signature

```python
generate_nsy_wind_nsy_angle(lat, lon, elev, angle, speed,
                            speed_turbulence, speed_deviation,
                            angle_turbulence, angle_deviation)
```

#### Purpose

Generates an atmospheric environment where **both wind speed and wind direction vary independently** with altitude using stochastic low-frequency noise. This is the most general single-layer non-symmetric model, suitable for full turbulence dispersion studies.

#### Parameters

| Parameter | Type | Unit | Description |
|-----------|------|------|-------------|
| `lat` | float | degrees | Launch site latitude. |
| `lon` | float | degrees | Launch site longitude. |
| `elev` | float | m | Launch site elevation above sea level. |
| `angle` | float | degrees | Base wind direction (meteorological convention). |
| `speed` | float | m/s | Base wind speed. |
| `speed_turbulence` | float | dimensionless | Relative turbulence intensity for speed variability. |
| `speed_deviation` | float | m/s | Absolute deviation scale for speed noise. |
| `angle_turbulence` | float | dimensionless | Relative turbulence intensity for directional variability. |
| `angle_deviation` | float | degrees | Absolute deviation scale for directional noise. |

#### Returns

A RocketPy `Environment` instance configured with independent stochastic speed and angle profiles across the full altitude range.

#### Profile Generation Logic

1. Generate a full altitude grid from 0 to 79,990 m in 10 m increments (8,000 samples).
2. Generate two **independent** white Gaussian noise signals — one for speed, one for angle.
3. Apply the same 2nd-order Butterworth low-pass filter (cutoff = 0.05) independently to each noise signal.
4. Normalize each filtered signal to unit standard deviation and compute the perturbed profiles:

   ```
   v(z) = speed + speed_deviation * speed_turbulence * n_speed_filtered(z)
   θ(z) = angle + angle_deviation * angle_turbulence * n_angle_filtered(z)
   ```

5. Compute U and V components:

   ```
   u(z) = -v(z) * sin(radians(θ(z)))
   w(z) = -v(z) * cos(radians(θ(z)))
   ```

6. Build the environment using the resulting altitude-indexed U and V arrays.

#### Key Difference from `generate_cte_wind_nsy_angle`

Both speed and angle are perturbed independently. Setting `speed_turbulence = 0` and `speed_deviation = 0` reduces this function to the behavior of `generate_cte_wind_nsy_angle`. Setting `angle_turbulence = 0` and `angle_deviation = 0` produces a noisy-speed, constant-angle profile.

#### Example Profile

```python
env = generate_nsy_wind_nsy_angle(
    lat=32.990254,
    lon=-106.974998,
    elev=1400,
    angle=180,            # Base wind from the South
    speed=10.0,           # 10 m/s base speed
    speed_turbulence=0.1, # 10% speed turbulence
    speed_deviation=2.0,  # +/- ~2 m/s speed spread
    angle_turbulence=0.1, # 10% angular turbulence
    angle_deviation=15.0  # +/- ~15 deg angular spread
)
```

---

### 5.3 `generate_variable_wind_profile`

#### Signature

```python
generate_variable_wind_profile(lat, lon, elev,
                               heights_ref, angles_ref, speeds_ref,
                               speed_turbulence=0.1, speed_deviation=2,
                               angle_turbulence=0.0, angle_deviation=0,
                               max_altitude=80000, dz=10)
```

#### Purpose

Generates a **layered wind profile** where each altitude band has its own base speed and direction, with optional independent stochastic perturbations applied per layer. This is the most complete wind model in the module, suitable for simulating realistic atmospheric wind shear scenarios with turbulence.

#### Parameters

| Parameter | Type | Unit | Description |
|-----------|------|------|-------------|
| `lat` | float | degrees | Launch site latitude. |
| `lon` | float | degrees | Launch site longitude. |
| `elev` | float | m | Launch site elevation above sea level. |
| `heights_ref` | list[float] | m | Altitude breakpoints defining layer boundaries. Must be in ascending order. |
| `angles_ref` | list[float] | degrees | Base wind direction for each layer. Must have the same length as `heights_ref`. |
| `speeds_ref` | list[float] | m/s | Base wind speed for each layer. Must have the same length as `heights_ref`. |
| `speed_turbulence` | float | dimensionless | Relative turbulence intensity for speed. Default: 0.1. |
| `speed_deviation` | float | m/s | Absolute deviation scale for speed noise. Default: 2. |
| `angle_turbulence` | float | dimensionless | Relative turbulence intensity for direction. Default: 0.0. |
| `angle_deviation` | float | degrees | Absolute deviation scale for directional noise. Default: 0. |
| `max_altitude` | float | m | Maximum altitude of the generated profile. Default: 80,000 m. |
| `dz` | float | m | Altitude resolution of the grid. Default: 10 m. |

#### Raises

`ValueError` if `heights_ref`, `angles_ref`, and `speeds_ref` do not have the same length.

#### Returns

A RocketPy `Environment` instance configured with a layered custom atmospheric model.

#### Profile Generation Logic

1. Generate a full altitude grid from 0 to `max_altitude` in `dz` increments.
2. For each layer `i` defined by the interval `[heights_ref[i], heights_ref[i+1])`:
   - Generate independent white Gaussian noise signals for speed and angle across the samples in that layer.
   - Apply the 2nd-order Butterworth low-pass filter (cutoff = 0.05) to each signal.
   - Normalize to unit standard deviation and compute perturbed values:
     ```
     v(z) = speeds_ref[i] + speed_deviation * speed_turbulence * n_speed_filtered(z)
     θ(z) = angles_ref[i] + angle_deviation * angle_turbulence * n_angle_filtered(z)
     ```
3. The final layer covers all altitudes at or above `heights_ref[-1]`, applying the last reference values plus turbulence.
4. Compute U and V components across the full grid and build the environment.

> **Note:** The profile is piecewise constant between breakpoints — each layer holds its base value plus noise. There is no interpolation between reference altitudes; the transition between layers is a discrete step.

#### Example Profile — Wind Shear Scenario

```python
env = generate_variable_wind_profile(
    lat=32.990254,
    lon=-106.974998,
    elev=1400,
    heights_ref=[0, 500, 2000, 5000, 10000],
    angles_ref=[270, 260, 240, 210, 200],   # Backing wind with altitude
    speeds_ref=[5.0, 7.0, 10.0, 14.0, 18.0], # Speed increasing with altitude
    speed_turbulence=0.1,
    speed_deviation=1.5,
    angle_turbulence=0.05,
    angle_deviation=8.0
)
```

This profile represents a realistic wind shear scenario: surface winds from the West at 5 m/s backing and increasing to 18 m/s at 10,000 m, with moderate turbulence in both speed and direction per layer.

---

## 6. Output Format Details

All generators return a configured `Environment` object. Internally, wind components are passed as NumPy arrays of shape `(N, 2)`:

```
wind_u = [[altitude_0, u_0], [altitude_1, u_1], ..., [altitude_N, u_N]]
wind_v = [[altitude_0, v_0], [altitude_1, v_1], ..., [altitude_N, v_N]]
```

These arrays are passed directly to:

```python
env.set_atmospheric_model(
    "custom_atmosphere",
    pressure=None,
    temperature=None,
    wind_u=wind_u,
    wind_v=wind_v
)
```

Pressure and temperature are set to `None`, meaning RocketPy uses its internal standard atmosphere model for those quantities.

---

## 7. Usage with the Simulation Core

The returned `Environment` object is passed directly to simulation methods in `File_simulation`:

```python
sim = File_simulation("AURORA_v02", "AeroTech_N2000W")

env = generate_nsy_wind_nsy_angle(
    lat=32.990254, lon=-106.974998, elev=1400,
    angle=270, speed=8.0,
    speed_turbulence=0.1, speed_deviation=2.0,
    angle_turbulence=0.1, angle_deviation=10.0
)

sim.run_single_flight_sim(
    env=env,
    rail_length=5.2,
    inclination=0,   # Vertical launch
    heading=90
)
```

For dispersion studies using `run_multiple_flight_sims`, generate a list of environments — each a different realization of the stochastic model:

```python
envs = [generate_nsy_wind_nsy_angle(...) for _ in range(50)]
envs_names = [f"nsy_{i}" for i in range(50)]

sims, keys = sim.run_multiple_flight_sims(
    envs=envs,
    envs_names=envs_names,
    rail_lengths=[5.2],
    inclinations=[0],
    headings=[90],
    elevations=[1400]
)
```