# Contributing Guidelines

## Purpose

This document defines the minimum technical and organizational standards for contributing to this repository. These rules exist to ensure consistency, maintainability, reproducibility, and long-term sustainability of the project.

All contributors are expected to comply with these guidelines. Non-compliant contributions may be rejected during review.

---

## General Principles

* Prefer clarity over cleverness.
* Code must be readable by someone outside the original authoring context.
* Avoid unnecessary complexity.
* All contributions must be traceable and reviewable.
* Generated files must not be committed unless explicitly required.

---

## Repository Structure

* Source code must reside under the appropriate language-specific directories.
* Data files (CSV, JSON) must be placed in clearly named data directories.
* Scripts, tools, and utilities must not be mixed with core application logic.

---

## CSV File Standards

CSV files are treated as structured data inputs or outputs and must follow these rules:

* Use comma (`,`) as the delimiter.
* Always include a header row.
* Use UTF-8 encoding without BOM.
* Decimal separator must be a dot (`.`).
* Missing values must be explicit (`NaN` or empty), not inferred.
* Do not embed units in numeric values; units must be documented separately.

Example:

```
time_s,altitude_m,velocity_mps
0.0,0.0,0.0
0.1,1.2,12.5
```

---

## JSON File Standards

JSON files are used for configuration, metadata, or structured interchange.

Rules:

* JSON must be valid and strictly compliant (no comments).
* Use snake_case for keys.
* Avoid deeply nested structures unless justified.
* Configuration values must be explicit; no magic defaults.
* Do not store executable logic in JSON.

Example:

```json
{
  "sampling_rate_hz": 50,
  "serial_port": "/dev/ttyUSB0",
  "enable_logging": true
}
```

---

## Python Contribution Guidelines

### Naming Conventions

* Modules and files: snake_case
* Functions and variables: snake_case
* Classes: PascalCase
* Constants: UPPER_CASE
* Private/internal members: prefix with a single underscore (`_`)

Example:

```python
MAX_BUFFER_SIZE = 1024

class TelemetryParser:
    def __init__(self, sampling_rate_hz: int):
        self._sampling_rate_hz = sampling_rate_hz

    def parse_frame(self, raw_frame: bytes) -> dict:
        parsed_data = {}
        return parsed_data
```

### Code Style

* Follow PEP 8.
* Use type hints where applicable.
* Prefer explicit imports.
* Avoid global state.

### Documentation

* All public functions and classes must include docstrings.
* Docstrings must describe purpose, parameters, and return values.

Example:

```python
def compute_altitude(pressure: float) -> float:
    """
    Compute altitude from pressure using a standard atmosphere model.

    :param pressure: Measured pressure in Pascals.
    :return: Altitude in meters.
    """
```

### Data Handling

* Do not hardcode file paths.
* Use standard libraries (`csv`, `json`, `pathlib`).
* Explicitly validate inputs.

---

## C++ Contribution Guidelines

### Language and Tooling

* Target standard: C++17 or later (unless stated otherwise).
* Use CMake for build configuration.
* Code must compile without warnings on supported toolchains.

### Naming Conventions

* Classes: PascalCase
* Functions and variables: camelCase
* Constants: UPPER_CASE
* Files: snake_case or match class name

### Code Structure

* Separate interface (`.h`) and implementation (`.cpp`).
* Keep headers minimal and self-contained.
* Avoid unnecessary template or macro usage.

### Documentation

* Public APIs must be documented using Doxygen-style comments.

Example:

```cpp
/**
 * @brief Computes velocity from position samples.
 * @param deltaPosition Difference in position (m).
 * @param deltaTime Time interval (s).
 * @return Velocity in m/s.
 */
double computeVelocity(double deltaPosition, double deltaTime);
```

---

## Commit Messages

* Use clear, descriptive commit messages.
* Prefer imperative mood ("Add", "Fix", "Refactor").
* One logical change per commit.

Example:

```
Add CSV parser validation for telemetry input
```

---

## Pull Requests

* Each PR must address a single concern.
* Include a clear description of the change.
* Reference related issues if applicable.
* Code must pass all automated checks.
* Maintainers reserve the right to request changes.

---

## Governance and Licensing

By contributing to this repository, you agree that your contributions are governed by the project governance model and distributed under the same license as the project.

Refer to:

* GOVERNANCE.md
* LICENSE

---

## Final Note

These guidelines may evolve. Proposed changes must be discussed through issues and approved according to the governance process.