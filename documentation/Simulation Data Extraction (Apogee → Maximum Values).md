# Simulation Data Extraction (Apogee → Maximum Values)

### Module: src/sims.py

## Scope 
This document describes the utilities responsible for extracting relevant
simulation data during the mid- and late-flight phases of a rocket flight
simulation.

The goal is to clearly define the physical flight event associated with each
extraction function, the meaning of the returned metrics, and the conventions
used, so contributors can correctly interpret the results without inspecting
the implementation.

## Coordinate System and Units

- RocketPy uses a launch-centered coordinate system:
  - X-axis: Points East (positive values = East direction)

  - Y-axis: Points North (positive values = North direction)

  - Z-axis: Points upward (positive values = altitude above launch site)

- Velocities and speeds are expressed in meters per second [m/s]

- Accelerations are expressed in meters per second squared [m/s²]

- Angles are expressed in degrees [°]

- Time is expressed in seconds [s]

- Altitude:

  - z: Altitude above launch site (ASL)

  - altitude: Rocket altitude above ground level as a Function of time. Ground level is defined by the environment elevation (AGL)

- Forces are expressed in Newtons [N]

- Stability margin is expressed in calibers 

## `extract_apogee_sim_data`
Apogee is the moment when the rocket reaches its maximum altitude. The apogee will be displayed in both “Above Sea Level (ASL)” and “Above Ground Level (AGL)” formats.


### Expected Input 
A completed RocketPy Flight object

### Returned Data 
A dictionary containing:
- time: Time, in seconds, in which the rocket’s vertical velocity reaches zero in the apogee.
- x: X coordinate (positive east) of the center of mass of the rocket when it reaches apogee.
- y: Y coordinate (positive north) of the center of mass of the rocket when it reaches apogee.
- latitude: Rocket’s latitude coordinates (positive North) when it reaches apogee.
- longitude: Rocket’s longitude coordinates (positive East) when it reaches apogee. 
- z: ASL when it reaches apogee.
- altitude: AGL when it reaches apogee.
- freestream_speed: Freestream velocity magnitude, in m/s

## `extract_impact_sim_data`
Represents the ground impact event, corresponding to the final state of the
simulation when the rocket reaches ground level after descent.

### Expected Input 
- A completed RocketPy Flight object
- The simulation must continue until ground impact

### Returned Data

A dictionary containing:

- time: Time of impact
- x: X coordinate (positive east) of the center of mass of the rocket when it impacts ground.
- y: Y coordinate (positive east) of the center of mass of the rocket when it impacts ground.
- latitude: Rocket’s latitude coordinates (positive North) when it impacts ground.
- longitude: Rocket’s longitude coordinates (positive East) when it impacts ground.
- z: ASL when it impacts ground. 
- altitude: AGL when it impacts ground.
- speed: Rocket velocity magnitude in m/s relative to ground in the time of impact.

## `extract_maximum_values_sim_data`
Provides a summary of the maximum values recorded during the flight for various parameters.

### Expected Input 
- A completed RocketPy Flight object

### Maximum Value Computation and Returned data:
Some functions used in this new function have already been used and explained previously. Those that have not been used before are listed below. 

| RocketPy Quantity | Returned Maximum Metrics |
|---|---|
|`Flight.speed (Function)`: Rocket velocity magnitude in m/s relative to ground as a function of time.| `Flight.max_speed_time (float)` – Maximum velocity magnitude in m/s reached by the rocket relative to ground during flight. `Flight.max_speed (float)` – Time in seconds at which rocket reaches maximum velocity magnitude relative to ground. | 
| `Flight.mach_number (Function)` :  Rocket’s Mach number defined as its freestream speed divided by the speed of sound at its altitude. Expressed as a function of time. | `Flight.max_mach_number (float)` – Rocket’s maximum Mach number experienced during flight. `Flight.max_mach_number_time (float)` – Time at which the rocket experiences the maximum Mach number.|
| `Flight.reynolds_number (Function)` : Rocket’s Reynolds number, using its diameter as reference length and free_stream_speed as reference velocity. Expressed as a function of time.| `Flight.max_reynolds_number (float)` – Rocket’s maximum Reynolds number experienced during flight `Flight.max_reynolds_number_time (float)` – Time at which the rocket experiences the maximum Reynolds number.|
| `Flight.dynamic_pressure (Function)` : Dynamic pressure experienced by the rocket in Pa as a function of time, defined by 0.5*rho*V^2, where rho is air density and V is the freestream speed.| `Flight.max_dynamic_pressure (float)` – Maximum dynamic pressure, in Pa, experienced by the rocket `Flight.max_dynamic_pressure_time (float)` – Time at which the rocket experiences maximum dynamic pressure.|
| `Flight.acceleration (Function)` : Rocket acceleration magnitude in m/s² relative to ground as a function of time.|`max_acceleration_power_on_time` – Time at which the rocket reaches its maximum acceleration during motor burn. `max_acceleration_power_on` – Maximum acceleration reached by the rocket during motor burn. `max_acceleration_power_off_time` – Time at which the rocket reaches its maximum acceleration after motor burn. `max_acceleration_power_off` – Maximum acceleration reached by the rocket after motor burn. | 
 `max_Gs_power_on` is the peak net acceleration during motor burn, expressed in multiples of Earth’s gravity.| `self.standard_g` = 9.80665 |
| `stability_margin` : Stability margin of the rocket along the flight, it considers the variation of the center of pressure position according to the mach number, as well as the variation of the center of gravity position according to the propellant mass evolution. | `max_stability_margin` – Maximum stability margin. |
| `Flight.rail_button1_normal_force (Function)` : Upper rail button normal force in N as a function of time. | `Flight.max_rail_button1_normal_force (float)` – Maximum upper rail button normal force experienced during rail flight phase in N.|
| `Flight.rail_button1_shear_force (Function)` : Upper rail button shear force in N as a function of time.| `Flight.max_rail_button1_shear_force (float)` – Maximum upper rail button shear force experienced during rail flight phase in N.|
| `Flight.rail_button2_normal_force (Function)` : Lower rail button normal force in N as a function of time.| `Flight.max_rail_button2_normal_force (float)` – Maximum lower rail button normal force experienced during rail flight phase in N.|
| `Flight.rail_button2_shear_force (Function)` : Lower rail button shear force in N as a function of time.| `Flight.max_rail_button2_shear_force (float)` – Maximum lower rail button shear force experienced during rail flight phase in N.|
 

