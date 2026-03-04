# Simulation Summary and Comparison Utilities

### Module: src/sims.py

## Scope 
This document describes the utilities used to summarize and compare the most relevant results of completed RocketPy flight simulations.

These utilities are intended to provide a high-level, physically interpretable overview of a flight and to enable direct comparison between multiple simulations, without requiring inspection of raw time histories or low-level simulation outputs.

The focus is on extracting commonly reviewed (“usual”) and engineering-relevant (“important”) metrics that characterize the overall flight behavior across its main phases.

## Definition of "Usual" and "Important"

### Usual Data
“Usual” data refers to quantities that are:

- Evaluated in almost all rocket flight analyses
- Independent of specific mission objectives
- Available for any completed RocketPy flight simulation

Examples include initial stability, rail exit conditions, burnout conditions, apogee, global maxima, and impact state.

### Important Data 
“Important” data refers to quantities that:

- Correspond to key physical flight events
- Are commonly used as design drivers or constraints
- Allow rapid engineering comparison between configurations

Examples include:

- Maximum velocity and Mach number
- Maximum dynamic pressure
- Peak accelerations (power-on and power-off)
- Stability margins
- Impact location dispersion

## `extract_usual_important_sim_data`

Extracts a compact summary of the most relevant flight metrics from a single completed RocketPy Flight simulation.

This function aggregates representative quantities from:

- Initial conditions
- Rail exit
- Motor burnout
- Apogee
- Overall flight maximums
- Ground impact

### Expected Input
- A completed RocketPy `Flight` object

### Retuned Data 
Returns a dictionary containing key flight quantities, including:

- Initial and Environmental Conditions

  - Initial static stability margin (calibers)

  - Frontal surface wind velocity [m/s]

  - Lateral surface wind velocity [m/s]

  -  Rail Exit Conditions

  - Velocity magnitude at rail exit [m/s]

  - Static stability margin at rail exit (calibers)

  - Angle of attack at rail exit [°]

  - Thrust-to-weight ratio at rail exit [-]

- Motor Burnout Conditions

  - Time of motor burnout [s]

  - Dynamic pressure at burnout [Pa]

  - Acceleration magnitude at burnout [m/s²]

- Apogee

  - Apogee altitude above ground level [m]

  - Time of apogee [s]

  - Global Maximum Values (Entire Flight)

  - Maximum speed and corresponding time

  - Maximum Mach number and corresponding time

  - Maximum dynamic pressure and corresponding time

  - Maximum acceleration during motor burn (power-on)

  - Maximum acceleration after burnout (power-off)

  - Peak accelerations expressed in Gs (normalized by standard gravity)

  - Maximum stability margin

- Impact Conditions

  - Impact time [s]

  - Impact speed [m/s]

  - Impact X and Y coordinates [m]

  - Impact latitude and longitude [°]

  - Impact radius from launch point [m]

## `compare_usual_important_data`
Compares the summarized results of multiple flight simulations in a structured and reproducible format.

This function applies `extract_usual_important_sim_data` to each simulation and aggregates the results into a tabular representation suitable for trade studies and batch analysis.
 
  
