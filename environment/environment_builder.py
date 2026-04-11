"""
environment_builder.py
======================
Module for building the atmospheric environments used in VOLTA rocket
flight simulations - IREC 2026.

Two modes of operation:

    1. Historical mode (no internet required):
    Loads ERA5 files downloaded previously (one per year) and builds
    a list of RocketPy Environment objects, one for each combination
    of year, day and hour available. This list feeds directly into
    the Monte Carlo analysis in run_multiple_flight_sims().

    2. Forecast mode (internet required):
    Downloads a real-time meteorological forecast (GFS, NAM or RAP)
    and builds a single Environment object. Used in the days before
    the launch when a reliable forecast is available.

Launch site: Midland, Texas - IREC 2026
    Latitude  : 31.9686 N
    Longitude : 102.0779 W
    Elevation : 873 m above sea level

Authors
-------
Simulation Subsystem - VOLTA
"""

import datetime
import os
import warnings

from rocketpy import Environment


# ---------------------------------------------------------------------------
# Fixed launch site data - IREC Midland, Texas
# ---------------------------------------------------------------------------

MIDLAND_LAT = 31.9686
MIDLAND_LON = -102.0779
MIDLAND_ELEV = 873.0

# Local time zone: CDT = UTC-5 in June
MIDLAND_TIMEZONE = "America/Chicago"

# String that RocketPy needs to read ERA5 files from ECMWF.
# It tells RocketPy how the variables are named inside the .nc file
# (e.g. "temperature", "u_component_of_wind", etc.).
# If the data source changes, this value would need to be updated.
ECMWF_DICTIONARY = "ECMWF"

# Folder where the downloaded ERA5 files are stored
DATA_DIR = "data/weather"


# ---------------------------------------------------------------------------
# Helper function: finds ERA5 files automatically by year
# ---------------------------------------------------------------------------

def find_files_by_year(data_dir=DATA_DIR, years=None):
    """
    Searches the data folder for downloaded ERA5 pressure level files
    and returns a dictionary mapping each year to its corresponding file.

    This is necessary because download_era5.py downloads one separate
    file per year (e.g. midland_pressure_levels_2019.nc) instead of
    a single file containing all years.

    Parameters
    ----------
    data_dir : str
        Folder where the downloaded .nc files are stored.
        Default: "data/weather".

    years : list of int or None
        Years to search for. Default: [2015, 2016, ..., 2024].

    Returns
    -------
    dict
        Dictionary with format {year: file_path}.
        Only includes years for which the file exists.
        Example: {2019: "data/weather/midland_pressure_levels_2019.nc"}
    """
    if years is None:
        years = list(range(2015, 2025))

    files = {}
    for year in years:
        path = os.path.join(data_dir, f"midland_pressure_levels_{year}.nc")
        if os.path.exists(path):
            files[year] = path
        else:
            warnings.warn(
                f"No file found for year {year}: '{path}'\n"
                "Run download_era5.py to download it.",
                RuntimeWarning,
                stacklevel=2,
            )

    return files


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class EnvironmentBuilder:
    """
    Class for building RocketPy atmospheric environments.

    A class is used here because both modes (historical and forecast)
    share the same launch site data. Instead of passing latitude,
    longitude and elevation to each function separately, they are
    stored once here and all methods use them automatically.

    Since download_era5.py downloads one file per year, this builder
    receives a dictionary mapping each year to its file. If that
    dictionary is not provided, it searches for the files automatically
    in the data folder.

    Parameters
    ----------
    files_by_year : dict or None
        Dictionary {year: path} with the downloaded ERA5 files.
        Example: {2019: "data/weather/midland_pressure_levels_2019.nc"}
        If None, files are searched automatically in data_dir.

    data_dir : str
        Folder to search for files if files_by_year is None.
        Default: "data/weather".

    latitude : float
        Launch site latitude in decimal degrees. Default: Midland TX.

    longitude : float
        Launch site longitude in decimal degrees. Default: Midland TX.

    elevation : float
        Launch site elevation in meters. Default: Midland TX.
    """

    def __init__(
        self,
        files_by_year=None,
        data_dir=DATA_DIR,
        latitude=MIDLAND_LAT,
        longitude=MIDLAND_LON,
        elevation=MIDLAND_ELEV,
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation

        # If no files are provided, search for them automatically
        if files_by_year is not None:
            self.files_by_year = files_by_year
        else:
            self.files_by_year = find_files_by_year(data_dir)

        if len(self.files_by_year) == 0:
            warnings.warn(
                "No ERA5 files found in the data folder.\n"
                "Run download_era5.py first.",
                RuntimeWarning,
                stacklevel=2,
            )
        else:
            years_found = sorted(self.files_by_year.keys())
            print(f"EnvironmentBuilder ready. Files found: {years_found}")

    # -----------------------------------------------------------------------
    # Internal method: builds one Environment for a single date
    # -----------------------------------------------------------------------

    def _build_single_environment(self, date):
        """
        Builds a RocketPy Environment object for a specific date and
        hour using the ERA5 file for the corresponding year.

        Since files are separated by year, this method looks up the
        files_by_year dictionary to find which file to use based on
        the year of the requested date.

        This method is internal (underscore at the start of the name).
        It is not called directly from outside; it is used by
        build_historical_environments() inside its loop.

        Parameters
        ----------
        date : tuple of int
            Date and time in UTC: (year, month, day, hour).
            Example: (2019, 6, 17, 15) is June 17 2019 at 15:00 UTC,
            which corresponds to 10:00 AM local time in Texas (CDT).

        Returns
        -------
        rocketpy.Environment
            Environment configured with the ERA5 profile for that date.
        """
        year = date[0]

        # Check that a file exists for this specific year
        if year not in self.files_by_year:
            raise FileNotFoundError(
                f"No ERA5 file available for year {year}.\n"
                "Run download_era5.py to download it."
            )

        file_path = self.files_by_year[year]

        # Create the Environment object with the launch site location and date
        env = Environment(
            date=date,
            latitude=self.latitude,
            longitude=self.longitude,
            elevation=self.elevation,
            timezone=MIDLAND_TIMEZONE,
        )

        # Load the atmospheric profile from the ERA5 file for that year.
        # type="Reanalysis" is the correct type for historical ERA5 files.
        # dictionary="ECMWF" tells RocketPy how the variables are named
        # inside the .nc file, since ERA5 comes from ECMWF and uses their
        # naming convention, which is different from NOAA or other providers.
        env.set_atmospheric_model(
            type="Reanalysis",
            file=file_path,
            dictionary=ECMWF_DICTIONARY,
        )

        return env

    # -----------------------------------------------------------------------
    # Historical mode: builds the list of environments for Monte Carlo
    # -----------------------------------------------------------------------

    def build_historical_environments(
        self,
        years=None,
        month=6,
        days=None,
        utc_hours=None,
    ):
        """
        Builds a list of Environment objects using historical ERA5 data,
        one for each combination of year, day and hour.

        This list is the direct input for the 'envs' parameter in
        run_multiple_flight_sims() for Monte Carlo simulations.
        Each environment represents the real atmospheric conditions
        over Midland at a specific moment in the past within the
        competition window (June 15-20).

        With the default values, up to 180 environments are built:
        10 years x 6 days x 3 hours = 180 environments.

        Parameters
        ----------
        years : list of int or None
            Historical years to include. If None, all years for which
            an ERA5 file was found are used.

        month : int
            Competition month. Default: 6 (June).

        days : list of int or None
            Days of the month. Default: [15, 16, 17, 18, 19, 20].

        utc_hours : list of int or None
            UTC hours to include. IREC launches are typically between
            7am and 2pm local time (CDT), which corresponds to
            12:00 - 19:00 UTC because CDT = UTC-5.
            Default: [12, 15, 18].

        Returns
        -------
        envs : list of rocketpy.Environment
            List of successfully built environments.

        labels : list of str
            Labels in the same order as envs.
            Format: "ERA5_YYYY_MMDD_HHZ"
            Example: "ERA5_2019_0617_15Z"
        """
        # If no years specified, use all years that have a downloaded file
        if years is None:
            years = sorted(self.files_by_year.keys())

        if days is None:
            days = [15, 16, 17, 18, 19, 20]

        if utc_hours is None:
            # 12Z = 7am CDT, 15Z = 10am CDT, 18Z = 1pm CDT
            # Covers the typical IREC launch time window
            utc_hours = [12, 15, 18]

        envs = []
        labels = []
        total = len(years) * len(days) * len(utc_hours)
        counter = 0

        print(f"\nBuilding {total} historical ERA5 environments...")
        print(f"  Years : {years}")
        print(f"  Days  : {days}")
        print(f"  Hours : {utc_hours} UTC")
        print()

        for year in years:
            for day in days:
                for hour in utc_hours:
                    counter += 1
                    date = (year, month, day, hour)
                    label = f"ERA5_{year}_{month:02d}{day:02d}_{hour:02d}Z"

                    try:
                        env = self._build_single_environment(date)
                        envs.append(env)
                        labels.append(label)
                        print(f"  [{counter:>4}/{total}] {label} OK")

                    except Exception as error:
                        # If a year or date fails it is skipped with a warning
                        # and the loop continues with the rest. This prevents
                        # a missing ERA5 data point from breaking the whole
                        # process.
                        warnings.warn(
                            f"Could not build {label}: {error}",
                            RuntimeWarning,
                            stacklevel=2,
                        )
                        print(f"  [{counter:>4}/{total}] {label} SKIPPED ({error})")

        print(f"\n  Total built: {len(envs)} out of {total} environments.")
        print(f"  Ready to pass to Monte Carlo.\n")

        return envs, labels

    # -----------------------------------------------------------------------
    # Forecast mode: single environment for days before the launch
    # -----------------------------------------------------------------------

    def build_forecast_environment(
        self,
        model="GFS",
        date=None,
        utc_hour=18,
    ):
        """
        Builds an Environment using a real-time meteorological forecast
        downloaded from the NOAA NOMADS server.

        Requires internet. Used in the days before the launch when a
        reliable forecast is available for the flight date.

        Model options:
            GFS : Global, 0.25 degree resolution, up to 10 days ahead.
                Good for general planning before the competition.
            NAM : Regional North America, ~5 km resolution, up to 60 hours.
                More detail over Texas than GFS.
            RAP : Regional North America, ~13 km, updated every hour,
                up to 21 hours ahead. Best option on launch day.

        Parameters
        ----------
        model : str
            Forecast model: "GFS", "NAM" or "RAP".
            Default: "GFS".

        date : tuple of int or None
            Date in UTC: (year, month, day, hour).
            Default: tomorrow at the hour indicated in utc_hour.

        utc_hour : int
            UTC hour. Only used if date is None.
            Default: 18 (corresponds to 1pm local CDT time).

        Returns
        -------
        rocketpy.Environment
            Environment with the downloaded forecast profile.
        """
        valid_models = ["GFS", "NAM", "RAP"]
        if model not in valid_models:
            raise ValueError(
                f"Model '{model}' not recognized. "
                f"Available options: {valid_models}"
            )

        # If no date is specified, use tomorrow as a reference
        if date is None:
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
            date = (tomorrow.year, tomorrow.month, tomorrow.day, utc_hour)

        print(f"\nBuilding environment with {model} forecast...")
        print(f"  Date (UTC): {date[0]}-{date[1]:02d}-{date[2]:02d} {date[3]:02d}:00")
        print(f"  Downloading from NOAA NOMADS server (requires internet)...")
        print()

        # Create the Environment with the launch site location
        env = Environment(
            date=date,
            latitude=self.latitude,
            longitude=self.longitude,
            elevation=self.elevation,
            timezone=MIDLAND_TIMEZONE,
        )

        # type="Forecast" makes RocketPy automatically download the most
        # recent forecast of the specified model from NOAA.
        # No local file or credentials are required.
        env.set_atmospheric_model(
            type="Forecast",
            file=model,
        )

        print(f"  {model} environment ready.\n")
        return env

    # -----------------------------------------------------------------------
    # Visualization
    # -----------------------------------------------------------------------

    def plot_environment(self, env):
        """
        Shows the atmospheric profile plots for an Environment object.

        Generates vertical profiles of pressure, temperature, density
        and wind (U and V components) using RocketPy's built-in
        plotting function.

        Parameters
        ----------
        env : rocketpy.Environment
            Environment built with one of the methods of this class.
        """
        env.plots.atmospheric_model()

    def print_environment_info(self, env):
        """
        Prints a summary of the atmospheric environment to the console.

        Shows surface conditions (pressure, temperature, wind), the
        type of model loaded, and launch site details.

        Parameters
        ----------
        env : rocketpy.Environment
            Environment built with one of the methods of this class.
        """
        env.prints.atmospheric_model()