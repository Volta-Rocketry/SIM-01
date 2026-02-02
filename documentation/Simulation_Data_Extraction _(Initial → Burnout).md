# Simulation Data Extraction (Initial → Burnout)

### Module: src/sims.py

## Scope 
This document describes the utilities responsible for extracting relevant
simulation data during the early phases of a rocket flight simulation.
The focus is on clearly defining what physical event each extraction
represents, what data is expected, and what data is returned, so that
contributors can use these utilities without inspecting the implementation.

## Flight Phases Overview

| Phase | Description |
|---|---|
|Initial Conditions | Simulation start, before significant motion or thrust effects|
|Out of Rail | Instant when the rocket exits the launch rail
|Burnout| Instant when motor thrust becomes zero|

Each phase corresponds to a physically meaningful flight event and should
not be confused with time-based sampling.

## `extract_initial_conditions_sim_data`

### Physical meaning
Represents the initial state of the rocket at simulation start (t = 0).
At this stage, the vehicle is either stationary or undergoing negligible motion,
and no significant aerodynamic or thrust-induced effects have occurred.

### Expected input
- A completed RocketPy `Flight` object
- The flight must contain valid time-zero state data

### Returned data 
A dictionary containing, at minimum:

- Simulation time
- Position components
- Velocity components
- Acceleration components
- Vehicle mass

Returned values correspond to the first recorded simulation state.

### Assumptions and edge cases

- Assumes the simulation starts at `t = 0`
- If initial state data is missing or corrupted, extraction must fail
- Does not perform interpolation

### Usage example

```
initial_data = extract_initial_conditions_sim_data(flight)
```


## `extract_out_of_rail_sim_data`

### Physical meaning 
Represents the instant when the rocket leaves the launch rail.
This marks the transition from rail-constrained motion to free flight,
where aerodynamic forces and attitude dynamics fully apply.

### Expected input 

- A completed RocketPy `Flight` object
- The simulation must include a launch rail phase

### Returned data

A dictionary containing:

- Time at rail exit
- Position components
- Velocity components
- Acceleration components
- Orientation or attitude-related values (if available)


### Usage example 
 
```
rail_exit_data = extract_out_of_rail_sim_data(flight)
```

## `extract_burn_out_sim_data` 

### Physical meaning 

Represents motor burnout, defined as the instant when motor thrust becomes
zero. This event marks the transition from powered ascent to ballistic
flight.

### Expected input 

- A completed RocketPy `Flight` object
- The motor thrust curve must be available

### Returned data 

A dictionary containing: 

Dictionary containing the rocket state at motor burnout with the following
    keys:
 - time : float
        Time in seconds at which motor burnout occurs.
 - z : float
        Altitude above sea level (ASL) at motor burnout, in meters.
- altitude : float
        Altitude above ground level (AGL) at motor burnout, in meters.
- speed : float
        Rocket velocity magnitude relative to ground at motor burnout, in m/s.
- mach : float
        Mach number of the rocket at motor burnout.
- freestream_speed : float
        Freestream airspeed relative to the rocket at motor burnout, in m/s.
- dynamic_pressure : float
        Dynamic pressure experienced by the rocket at motor burnout, in pascals.

### Assumptions and edge cases

- Assumes a single continuous burn
- If burnout cannot be detected, extraction must fail
- Does not extrapolate thrust data

### Usage example 

```
burnout_data = extract_burn_out_sim_data(flight)
```
