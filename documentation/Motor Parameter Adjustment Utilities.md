# Motor Parameter Adjustment Utilities

**Module:** `src/adjust_parameters`

---

## 1. Purpose

This document describes the utility functions in `src/adjust_parameters` used to compute and adjust motor parameters before a simulation is executed. These utilities serve as a preprocessing layer between the raw motor configuration files (`parameters/motors/motors_parameters.json`) and the RocketPy `SolidMotor` constructor.

Their role is to fill in parameters that are not directly available in the motor datasheet or manufacturer specifications, using geometric and mass models derived from the known physical configuration of the motor. A sentinel value of `-1` in the JSON configuration signals that a parameter must be computed rather than read directly.

---

## 2. Design Principle: Sentinel-Based Parameter Resolution

Motor configuration files may contain incomplete parameter sets. Rather than requiring every parameter to be explicitly specified, the convention is to store `-1` for any parameter that can be derived from other available values. `eval_adjust_motor_parameters` inspects each parameter and either uses the explicit value or computes it via the corresponding utility function.

This approach makes the JSON configuration files self-documenting: a `-1` value explicitly signals a derived quantity, and contributors can identify which parameters are measured and which are estimated without reading the source code.

The sentinel value `-1` must never be used as a legitimate physical value. All motor parameters have strictly positive physical meaning (radii, masses, heights, positions), so `-1` is unambiguous as a placeholder.

---

## 3. Reference Frame and Unit Conventions

All functions in this module operate under the following conventions, consistent with the RocketPy coordinate system used in `File_simulation`:

| Quantity | Unit | Reference |
|----------|------|-----------|
| Mass | kg | — |
| Length / radius / height | m | — |
| Inertia | kg·m² | Motor center of mass |
| Position (axial) | m | Nozzle exit as origin, positive toward nose |

Positions such as `grains_center_of_mass_position` and `center_of_dry_mass_position` are measured along the motor axis from the nozzle exit toward the forward end of the motor case.

---

## 4. Physical Models

### 4.1 Dry Motor Inertia Model

The dry motor (casing without propellant) is modeled as a **thin-walled hollow cylinder**. This is a standard first-order approximation for solid motor casings, where the structural mass is concentrated near the outer radius and the wall thickness is small relative to the radius.

Under this assumption, the moments of inertia about the center of mass are:

```
Ixx = 0.5 * m * r² + (1/12) * m * h²     [transverse, roll axis]
Iyy = Ixx                                  [transverse, pitch axis — symmetric]
Izz = m * r²                               [axial, spin axis]
```

Where `m` is the dry mass [kg], `r` is the outer radius [m], and `h` is the total height (length) of the motor case [m].

The `Ixx` and `Iyy` terms combine the rotational inertia about the spin axis (`0.5 * m * r²`, hollow cylinder term) with the parallel-axis contribution from the axial extent of the body (`(1/12) * m * h²`, slender rod term). The `Izz` term treats the mass as concentrated at the outer radius, consistent with a thin shell.

### 4.2 Nozzle Radius Model

The nozzle throat radius is estimated from the combustion chamber (case) radius using a fixed area contraction ratio:

```
nozzle_radius = 0.85 * chamber_radius
```

This implies a nozzle throat area equal to 72.25% of the chamber cross-sectional area (`0.85² ≈ 0.7225`), which is a conservative approximation consistent with typical solid motor nozzle contraction ratios for motors in the high-power rocketry range.

This estimate is used only when the nozzle radius is not available in the motor datasheet. When a measured value exists, it must be specified explicitly in the JSON configuration and the sentinel value must not be used.

### 4.3 Geometric Fallback Assumptions in `eval_adjust_motor_parameters`

When individual geometric parameters are absent from the motor datasheet, the following physical assumptions are applied as fallbacks:

| Parameter | Fallback assumption | Physical justification |
|-----------|--------------------|-----------------------|
| `grain_outer_radius` | Equal to `case_radius` | Propellant grain fills the case bore; no liner thickness accounted for. |
| `grain_initial_inner_radius` | 50% of `grain_outer_radius` | Neutral-burning approximation: inner port radius is half the outer radius, yielding a wall thickness equal to the inner radius. |
| `grain_initial_height` | Equal to `case_length` | Grain stack occupies the full usable case length. |
| `grains_center_of_mass_position` | 50% of `grain_initial_height` | Uniform grain density; center of mass at geometric midpoint of the grain stack. |
| `center_of_dry_mass_position` | 50% of `case_length` | Uniform mass distribution of the dry casing; center of mass at geometric midpoint. |

These assumptions are first-order geometric estimates. They are acceptable for simulation when manufacturer data is unavailable, but introduce uncertainty in the computed center of mass and inertia. If more accurate data is available, it must be provided explicitly in the JSON file.

---

## 5. Function Reference

---

### 5.1 `calculate_dry_motor_inertia`

#### Signature

```python
calculate_dry_motor_inertia(dry_mass, radius, height)
```

#### Purpose

Computes the three principal moments of inertia of the dry motor casing modeled as a thin-walled hollow cylinder about its center of mass.

#### Parameters

| Parameter | Type | Unit | Description |
|-----------|------|------|-------------|
| `dry_mass` | float | kg | Total dry mass of the motor, excluding propellant. |
| `radius` | float | m | Outer radius of the motor case. Used as the representative structural radius under the thin-shell assumption. |
| `height` | float | m | Total axial length of the motor case. |

#### Returns

| Type | Shape | Unit | Description |
|------|-------|------|-------------|
| `numpy.ndarray` | (3,) | kg·m² | Array `[Ixx, Iyy, Izz]` where Ixx = Iyy are the transverse moments and Izz is the axial (spin) moment. |

#### Physical Model

```
Ixx = 0.5 * dry_mass * radius² + (1/12) * dry_mass * height²
Iyy = Ixx
Izz = dry_mass * radius²
```

#### Example

```python
inertia = calculate_dry_motor_inertia(
    dry_mass=1.2,   # kg
    radius=0.038,   # m
    height=0.350    # m
)
# inertia -> array([Ixx, Iyy, Izz]) in kg·m²
```

---

### 5.2 `calculate_nozzle_radius`

#### Signature

```python
calculate_nozzle_radius(chamber_radius)
```

#### Purpose

Estimates the nozzle throat radius from the combustion chamber radius using a fixed contraction ratio of 0.85, corresponding to a throat-to-chamber area ratio of approximately 0.723.

#### Parameters

| Parameter | Type | Unit | Description |
|-----------|------|------|-------------|
| `chamber_radius` | float | m | Internal radius of the motor combustion chamber (case bore radius). |

#### Returns

| Type | Unit | Description |
|------|------|-------------|
| float | m | Estimated nozzle throat radius. |

#### Physical Model

```
nozzle_radius = 0.85 * chamber_radius
```

#### When to Use

Use this function only when the nozzle throat radius is not available from the motor datasheet or manufacturer specification. If a measured value exists, it must be set explicitly in the JSON configuration and this function must not be called for that motor.

#### Example

```python
nozzle_r = calculate_nozzle_radius(chamber_radius=0.038)
# nozzle_r -> 0.0323 m
```

---

### 5.3 `eval_adjust_motor_parameters`

#### Signature

```python
eval_adjust_motor_parameters(motor_data)
```

#### Purpose

Inspects a motor parameter dictionary loaded from the JSON configuration file and resolves all sentinel values (`-1`) by computing the missing parameters using the available geometric and mass data. Returns the fully resolved parameter dictionary ready for direct use in the RocketPy `SolidMotor` constructor.

This function is the single entry point for motor parameter preprocessing and must always be called between loading the JSON file and constructing the `SolidMotor` object.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `motor_data` | dict | Motor parameter dictionary loaded from `parameters/motors/motors_parameters.json`. Keys must follow the schema described below. |

#### Required Keys in `motor_data`

| Key | Type | Unit | Description |
|-----|------|------|-------------|
| `dry_mass` | float | kg | Dry motor mass. |
| `dry_inertia` | list or -1 | kg·m² | Inertia vector `[Ixx, Iyy, Izz]`, or -1 to compute. |
| `nozzle_radius` | float or -1 | m | Nozzle throat radius, or -1 to estimate. |
| `case_radius` | float | m | Motor case outer radius. Required when `nozzle_radius` or `grain_outer_radius` is -1. |
| `case_length` | float | m | Motor case total length. Required when `grain_initial_height`, `grains_center_of_mass_position`, or `center_of_dry_mass_position` is -1. |
| `grain_outer_radius` | float or -1 | m | Grain outer radius, or -1 to use `case_radius`. |
| `grain_initial_inner_radius` | float or -1 | m | Grain inner port radius, or -1 to compute as 50% of `grain_outer_radius`. |
| `grain_initial_height` | float or -1 | m | Total grain stack height, or -1 to use `case_length`. |
| `grains_center_of_mass_position` | float or -1 | m | Axial position of grain CoM from nozzle exit, or -1 to compute. |
| `center_of_dry_mass_position` | float or -1 | m | Axial position of dry casing CoM from nozzle exit, or -1 to compute. |

#### Returns

| Type | Description |
|------|-------------|
| dict | The same `motor_data` dictionary with all `-1` sentinel values replaced by computed quantities. `dry_inertia` is returned as a `list`, consistent with JSON-loaded data. All other parameters are returned as `float`. |

#### Resolution Logic

For each parameter, the function applies the following logic:

```
if motor_data[param] == -1:
    motor_data[param] = <computed value>
else:
    motor_data[param] = motor_data[param]   # explicit value used as-is
```

The resolution order is fixed and must not be changed, as some computed parameters depend on others resolved earlier in the same call (e.g. `grain_initial_inner_radius` depends on `grain_outer_radius`, which may itself have been resolved from `case_radius` in the same call).

#### Effect on Simulation

The resolved parameters directly populate the RocketPy `SolidMotor` constructor in `File_simulation.create_rocket()`. Incorrect or poorly estimated values affect:

- **Center of mass position:** influences the rocket's static stability margin and trim behavior throughout the burn.
- **Dry inertia:** affects the rocket's rotational dynamics and angular acceleration response to aerodynamic moments.
- **Nozzle radius:** used by RocketPy for thrust vector and exit flow calculations.
- **Grain geometry:** determines the propellant volume, burn surface area evolution, and mass flow rate model.

#### Example

```python
import json
from src.adjust_parameters import eval_adjust_motor_parameters

with open("parameters/motors/motors_parameters.json", "r", encoding="utf-8-sig") as f:
    all_motors = json.load(f)

motor_data = all_motors["AeroTech_N2000W"]
motor_data = eval_adjust_motor_parameters(motor_data)

# motor_data is now fully resolved and ready for SolidMotor construction
```

---

## 6. Impact on Simulation Accuracy

The parameter adjustment utilities introduce estimation error when sentinel values are used. The table below summarizes the sensitivity of simulation outputs to each estimated parameter:

| Estimated Parameter | Affected Simulation Output | Sensitivity |
|--------------------|---------------------------|-------------|
| `dry_inertia` | Angular dynamics, roll rate, pitch/yaw response | Moderate — affects rotational behavior but not trajectory in low-AoA flight |
| `nozzle_radius` | Thrust vector, exit pressure model | Low to moderate — manufacturer thrust curve takes precedence |
| `grain_outer_radius` | Burn surface area, mass flow | Moderate — affects thrust curve shape if not overridden by measured data |
| `grain_initial_inner_radius` | Initial burn surface, ignition transient | Moderate |
| `grain_initial_height` | Propellant volume, total impulse | High — directly scales available propellant mass |
| `grains_center_of_mass_position` | Static margin during burn | Moderate — affects stability evolution throughout powered phase |
| `center_of_dry_mass_position` | Post-burnout center of mass | Low to moderate |

When simulation accuracy is critical, all sentinel values should be replaced with measured or manufacturer-provided data in the JSON configuration file.

---

## 7. Notes and Constraints

- The sentinel value `-1` must not be used as a legitimate physical parameter. All physically meaningful motor parameters are strictly positive.
- `eval_adjust_motor_parameters` modifies the `motor_data` dictionary in place before returning it. The original dictionary loaded from JSON is mutated — if the original must be preserved, a deep copy should be made before calling this function.
- `case_radius` and `case_length` are always required in the JSON configuration, even if all other parameters are explicitly provided. They serve as the geometric basis for all fallback computations.
- Units must comply with project standards: decimal separator is a dot (`.`), no units embedded in numeric values, all lengths in meters, masses in kilograms.