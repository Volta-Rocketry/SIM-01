# Core Simulation Class

### Module: src/sims.py

### Class: File_simulation

## Overview 
`File_simulation` is the core orchestration class of the simulation framework.
It encapsulates the full lifecycle of a rocket flight simulation using RocketPy, from configuration loading to execution of single or multiple flight simulations.

This class acts as a high-level wrapper around RocketPy objects, allowing contributors to run standardized simulations without interacting directly with RocketPy’s low-level APIs.

It loads configuration data, initializes RocketPy objects, and executes
single or multiple flight simulations, serving as the boundary between
configuration definition and simulation execution.

## Responsibilities     
The `File_simulation` class is responsible for:

- Validating supported rocket and motor configurations

- Loading rocket and motor parameters from configuration files

- Constructing physically consistent RocketPy Rocket and SolidMotor objects

- Managing simulation readiness state

- Executing single-flight simulations

- Executing multiple-flight (parametric) simulations

- Providing basic inspection and visualization utilities

## How it fits into the overall simulation pipeline
This class acts as the main entry point for running rocket flight simulations.
It loads configuration data, initializes RocketPy objects, and executes
single or multiple flight simulations.

## Internal Data Handling and Lifecycle

### Initialization Phase
The lifecycle of a `File_simulation` instance begins with its initialization.
During this phase, the class stores the selected configuration file name and
motor name, initializes internal state flags, and prepares placeholders for
RocketPy objects.

This behavior is implemented in the class constructor:

```python
sim = File_simulation(file_name, motor_name)
```

 The class performs the following steps:

1. Verifies that the requested rocket configuration (file_name) is supported.

2. Verifies that the requested motor configuration (motor_name) is supported.

3. Loads rocket parameters from:

```
parameters/rocket/parameters_<file_name>.json
```
4. Loads motor parameters from:
```
parameters/motors/motors_parameters.json
```
5. Adjusts incomplete or missing motor parameters using
`eval_adjust_motor_parameters`

6. Constructs: 
- A RocketPy `SolidMotor`
- A RocketPy `Rocket`

7. Adds aerodynamic surfaces, recovery systems, rail buttons, and motor to the rocket.

8. Marks the rocket as ready for simulation. 

At the end of initialization, the rocket is fully constructed but no simulation has been executed.

### Simulation Phase 

#### Single Flight Simulation 
```Python
sim.run_single_flight_sim(
    env=environment,
    rail_length=5.7,
    inclination=5.0,
    heading=90
)
```
This method:
- Converts inclination from a user-friendly convention (0° = vertical)
to RocketPy’s convention (90° = vertical).

- Instantiates a RocketPy `Flight` object.
- Executes the numerical integration immediately.
Stores the result internally as `single_flight_sim`.

#### Multiple Flight Simulation
```
sims, keys = sim.run_multiple_flight_sims(
    envs=envs,
    envs_names=env_names,
    rail_lengths=[5.7],
    inclinations=[0],
    headings=[0],
    elevations=[0]
)
```
This method:
- Generates all combinations of the provided parameters.

- Runs a RocketPy `Flight` for each combination.

- Stores results in a dictionary keyed by simulation conditions.

- Returns both the simulation dictionary and a list of keys.

This functionality is intended for parametric studies, such as wind dispersion or sensitivity analysis.

## Assumptions and Limitations

### Assumptions
- Rocket and motor configurations are defined exclusively via JSON parameter files.

- All supported configurations are explicitly whitelisted in the code.

- Motor parameters may be partially defined and will be completed programmatically.

- RocketPy is treated as the authoritative physics engine.

### Limitations 
- The class does not support dynamic modification of rocket geometry after initialization.

- Atmospheric environments must be constructed externally and passed in.

- Output handling and persistence are limited to in-memory objects.

## Out of Scope 
The following responsibilities are explicitly out of scope for `File_simulation`:

- Implementing physical models or numerical solvers

- Generating atmospheric models

- Modeling sensor behavior (IMU, GPS, barometer)

- Handling telemetry, communication, or avionics logic

- Performing statistical post-processing or uncertainty propagation

- Managing file exports or long-term data storage

## Usage Example 
```
from sims import File_simulation
from sims import generate_cte_wind_cte_angle

# Create environment
env = generate_cte_wind_cte_angle(angle=270, speed=5)

# Create simulation object
sim = File_simulation(
    file_name="IREC_version1",
    motor_name="AeroTech_N3300R"
)

# Run single flight simulation
sim.run_single_flight_sim(
    env=env,
    rail_length=5.7,
    inclination=5,
    heading=90
)

# Inspect results
sim.single_flight_sim.plots.trajectory_3d()
```
## Notes 
- This class is designed to be stable and conservative.

- Any new rocket or motor configuration must be added to the supported lists and parameter files.