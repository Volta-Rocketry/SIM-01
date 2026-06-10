"""
environment/
============
Atmospheric environment module for VOLTA rocket flight simulations - IREC 2026.

Contains two files:

    download_era5.py        - Downloads ERA5 files from the Copernicus CDS.
                            Run once from a computer with internet access.

    environment_builder.py  - Loads the downloaded ERA5 files and builds
                            RocketPy Environment objects for simulations
                            and Monte Carlo analysis.
                            Does not require internet access.

Quick usage
-----------
    from environment import EnvironmentBuilder

    builder = EnvironmentBuilder()
    envs, labels = builder.build_historical_environments()
"""

from .environment_builder import EnvironmentBuilder

__all__ = ["EnvironmentBuilder"]