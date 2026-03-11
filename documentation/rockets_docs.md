# Rockets Documentation

## parameters_AURORA_v04.json

**Source file:** `rocket.ork`
**OpenRocket version:** 24.12
**Rocket name:** AURORA_v04
**Designer:** VOLTA UDEA

### Description

This file contains the rocket parameter series for the Aurora Mission vehicle,
extracted from the latest stable OpenRocket file (`rocket.ork`). It follows the
standard repository format under `parameters/rockets/` and serves as the
authoritative reference configuration for simulations and downstream tooling.

### OpenRocket reference mapping

| Parameter field | OpenRocket component |
|---|---|
| `airframe.radius` | Body tube outer radius (all sections) |
| `airframe.mass` | Total structural mass without motor |
| `airframe.center_of_mass_without_motor` | CG position from nose tip, without motor |
| `airframe.rocket_length` | Sum of all component lengths: nosecone (0.875) + Section A (1.12) + coupler (0.18) + Section B (1.39) + tailcone (0.068) |
| `nosecone` | `<nosecone>` — shape: haack, shapeparameter: 0.0 (Von Karman C=0) |
| `fins` | `<trapezoidfinset>` inside Fuselage Section B |
| `fins.position` | Leading edge from nose tip: Section B start (2.175 m) + offset from aft end |
| `rail_buttons.upper_position` | `<railbutton>` axialoffset from aft of Section B (3.565 m) |
| `rail_buttons.distance` | `instanceseparation` between the two buttons |
| `parachutes.main` | SRAD main parachute, deploys at 450 m AGL |
| `parachutes.drogue` | SRAD drogue parachute, deploys at apogee |

### Notes for contributors

- **Motor:** No motor is embedded in this `.ork` file. Motor mount hardware
  is modeled as mass components (thrust disks, centering ring).
- **`airframe.mass` and `airframe.center_of_mass_without_motor`:** These values
  come from physical weigh-in and OpenRocket simulation output, not from a
  global override in the `.ork` file.
- **`airframe.inertia`:** Not extracted from the `.ork` file. Current values
  are carried over from the previous version and must be updated from CAD.
- **Drogue parachute:** Not modeled in this OpenRocket version. Parameters
  are carried over from the previous design and must be validated independently.
- **Drag curves:** Referenced files (`Aurora_version_power_off/on_drag_curve.csv`)
  must exist under `csv_files/aerodynamic/` before running simulations.
- **Parachute Cd:** Value of 1.7 follows the effective/ballistic convention
  used by the repository, not the geometric Cd from OpenRocket (0.75).