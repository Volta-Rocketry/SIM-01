"""
download_era5.py
================
Temporary tool to download ERA5 data from the Copernicus CDS.

This script is run ONCE from a computer with internet access.
Once the .nc files are downloaded, this script is no longer needed:
all remaining work continues in environment_builder.py.

What does this script download?
--------------------------------
Two NetCDF files for Midland, Texas (IREC 2026):

1. Pressure levels data (midland_pressure_levels_YYYY.nc, one per year):
Contains vertical profiles of temperature, wind (U, V) and geopotential
for multiple pressure levels (100 hPa to 1000 hPa).
This is the main file RocketPy uses to build the full atmospheric
profile from ground level to the stratosphere.

2. Surface data (midland_surface_YYYY.nc, one per year):
Contains ground-level variables: 2 m temperature, surface pressure,
wind at 10 m and 100 m, and surface geopotential.
Required by the RocketPy EnvironmentAnalysis class.

Time range downloaded
----------------------
June 15-20 of each year from 2015 to 2024 (10 years of historical data).
This covers exactly the IREC competition window.
Representative UTC hours are included to capture the different
possible launch times during the competition day.

Geographic area
---------------
Small bounding box centered over Midland, Texas:
    North: 33.0 deg | South: 31.5 deg | East: -101.5 deg | West: -103.0 deg
Resolution: 0.25 deg x 0.25 deg (~28 km), sufficient for competition
rockets whose flight is entirely local.

Setup instructions
-------------------
Before running this script you must:

1. Create a free account on the Copernicus CDS:
https://cds.climate.copernicus.eu

2. After logging in, go to your profile and copy your Personal Access Token:
https://cds.climate.copernicus.eu/profile

3. Create the credentials file. On Windows open Notepad and save
the following content as (include the quotes when saving)::

    "C:\\Users\\YourUsername\\.cdsapirc"

On Linux/Mac save it as::

    ~/.cdsapirc

The file content must be exactly::

    url: https://cds.climate.copernicus.eu/api
    key: YOUR_TOKEN_HERE

4. Accept the ERA5 terms of use on the CDS website:
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-pressure-levels?tab=download#manage-licences
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=download#manage-licences

5. Install the required dependencies::

    pip install cdsapi netCDF4

6. Run this script from the project root folder::

    python environment/download_era5.py

The download may take between 20 minutes and 2 hours depending
on internet speed and CDS server load.

Note on download times
-----------------------
The CDS server processes requests in a queue. It is normal for the
script to wait a few minutes before the download begins.
Do not close the terminal while it is running.

If the download is interrupted, simply run the script again.
It will automatically skip years that were already downloaded.

Authors
-------
Simulation Subsystem - VOLTA
"""

import os
import sys


# ---------------------------------------------------------------------------
# Dependency check before importing
# ---------------------------------------------------------------------------

def _check_cdsapi():
    """
    Checks that the cdsapi library is installed.

    If it is not installed, stops the program with a clear message
    explaining how to install it.

    Returns
    -------
    bool
        True if cdsapi is available.

    Raises
    ------
    SystemExit
        If cdsapi is not installed.
    """
    import importlib.util
    spec = importlib.util.find_spec("cdsapi")
    if spec is None:
        print("\n[ERROR] The 'cdsapi' library is not installed.")
        print()
        print("  Install it with:")
        print("      pip install cdsapi")
        print()
        print("  Then make sure to configure your .cdsapirc file")
        print("  with your Copernicus CDS token.")
        print("  See the instructions at the top of this file.")
        sys.exit(1)
    return True


# ---------------------------------------------------------------------------
# Launch site constants
# ---------------------------------------------------------------------------

# IREC launch site coordinates in Midland, Texas
MIDLAND_LAT = 31.047292        # Decimal latitude [deg]
MIDLAND_LON = -103.527281      # Decimal longitude [deg]
MIDLAND_ELEV = 890.0         # Elevation above sea level [m]

# Download bounding box [North, West, South, East]
# Small box of ~150 km x 150 km centered over Midland
AREA_BBOX = [31.8, -104.3, 30.3, -102.8]

# Historical years to download (10 years, IREC window June 15-20)
HISTORICAL_YEARS = [str(y) for y in range(2015, 2025)]

# Competition window days
COMPETITION_DAYS = ["15", "16", "17", "18", "19", "20"]

# Representative UTC hours covering typical IREC launch times.
# Launches are usually between 7am and 2pm local time (CDT = UTC-5),
# which corresponds to 12:00 - 19:00 UTC.
REPRESENTATIVE_HOURS_UTC = ["00:00", "06:00", "12:00", "15:00", "18:00", "19:00", "20:00"]

# Standard pressure levels (from surface up to ~30 km altitude).
# RocketPy needs these levels to build the vertical wind and
# temperature profiles.
PRESSURE_LEVELS = [
    "1000", "975", "950", "925", "900", "875", "850", "825",
    "800", "775", "750", "700", "650", "600", "550", "500",
    "450", "400", "350", "300", "250", "225", "200", "175",
    "150", "125", "100"
]

# Output folder for downloaded files
OUTPUT_DIR = "data/weather"


# ---------------------------------------------------------------------------
# Download functions
# ---------------------------------------------------------------------------

def download_pressure_levels(output_dir=OUTPUT_DIR,
                            years=HISTORICAL_YEARS,
                            days=COMPETITION_DAYS,
                            hours=REPRESENTATIVE_HOURS_UTC,
                            area=AREA_BBOX,
                            pressure_levels=PRESSURE_LEVELS):
    """
    Downloads ERA5 pressure levels data for the IREC competition window.

    This file is the main input for RocketPy to build the full atmospheric
    profile (wind, temperature, pressure vs. altitude) using
    set_atmospheric_model(type="Reanalysis").

    One NetCDF file is downloaded per year to stay within the CDS
    server request size limits.

    Variables downloaded
    --------------------
    - geopotential     : Geopotential height per pressure level.
                        Used by RocketPy to convert pressure to altitude.
    - temperature      : Air temperature [K] per pressure level.
    - u_component_of_wind : East-west wind component [m/s].
    - v_component_of_wind : North-south wind component [m/s].

    Parameters
    ----------
    output_dir : str
        Folder where downloaded files are saved.
        Default: "data/weather".

    years : list of str
        List of years to download. Default: 2015-2024.

    days : list of str
        List of days of the month to download ("15" to "20").
        Default: days 15 to 20.

    hours : list of str
        List of UTC hours to download (format "HH:00").
        Default: representative hours covering IREC launch window.

    area : list of float
        Bounding box [North, West, South, East] in decimal degrees.
        Default: box over Midland, Texas.

    pressure_levels : list of str
        List of pressure levels in hPa to download.
        Default: standard levels from 100 to 1000 hPa.

    Returns
    -------
    list of str
        List of paths to the downloaded NetCDF files.
    """
    _check_cdsapi()
    import cdsapi

    os.makedirs(output_dir, exist_ok=True)
    downloaded_files = []

    print("\n" + "=" * 60)
    print("Downloading ERA5 - Pressure levels (year by year)")
    print("=" * 60)
    print(f"  Month : June (06)")
    print(f"  Days  : {', '.join(days)}")
    print(f"  Hours : {', '.join(hours)} UTC")
    print(f"  Area  : {area}")
    print()

    for year in years:
        output_file = os.path.join(
            output_dir,
            f"midland_pressure_levels_{year}.nc"
        )

        # Skip this year if the file already exists
        if os.path.exists(output_file):
            print(f"  [{year}] Already exists, skipping: {output_file}")
            downloaded_files.append(output_file)
            continue

        print(f"  [{year}] Downloading... (do not close the terminal)")

        client = cdsapi.Client()

        client.retrieve(
            "reanalysis-era5-pressure-levels",
            {
                "product_type": "reanalysis",
                "format": "netcdf",
                "variable": [
                    "geopotential",
                    "temperature",
                    "u_component_of_wind",
                    "v_component_of_wind",
                ],
                "pressure_level": pressure_levels,
                "year": [year],
                "month": ["06"],
                "day": days,
                "time": hours,
                "area": area,
            },
            output_file
        )

        print(f"  [{year}] OK -> {output_file}")
        downloaded_files.append(output_file)

    print(f"\n[OK] Pressure levels downloaded: {len(downloaded_files)} files.")
    return downloaded_files


def download_surface(output_dir=OUTPUT_DIR,
                    years=HISTORICAL_YEARS,
                    days=COMPETITION_DAYS,
                    hours=REPRESENTATIVE_HOURS_UTC,
                    area=AREA_BBOX):
    """
    Downloads ERA5 surface data for the IREC competition window.

    This file is the secondary input for the RocketPy EnvironmentAnalysis
    class, which uses it to statistically characterize surface conditions.

    One NetCDF file is downloaded per year to stay within the CDS
    server request size limits.

    Variables downloaded
    --------------------
    - geopotential                  : Surface geopotential (terrain elevation).
    - 2m_temperature                : Temperature at 2 m above ground [K].
    - surface_pressure              : Surface pressure [Pa].
    - 10m_u_component_of_wind       : Wind at 10 m, U component [m/s].
    - 10m_v_component_of_wind       : Wind at 10 m, V component [m/s].
    - 100m_u_component_of_wind      : Wind at 100 m, U component [m/s].
    - 100m_v_component_of_wind      : Wind at 100 m, V component [m/s].
    - instantaneous_10m_wind_gust   : Maximum wind gust at 10 m [m/s].
    - total_precipitation           : Total precipitation [m].

    Parameters
    ----------
    output_dir : str
        Folder where downloaded files are saved.
        Default: "data/weather".

    years : list of str
        List of years to download. Default: 2015-2024.

    days : list of str
        List of days of the month to download.
        Default: days 15 to 20.

    hours : list of str
        List of UTC hours to download.
        Default: representative hours covering IREC launch window.

    area : list of float
        Bounding box [North, West, South, East].
        Default: box over Midland, Texas.

    Returns
    -------
    list of str
        List of paths to the downloaded NetCDF files.
    """
    _check_cdsapi()
    import cdsapi

    os.makedirs(output_dir, exist_ok=True)
    downloaded_files = []

    print("\n" + "=" * 60)
    print("Downloading ERA5 - Surface data (year by year)")
    print("=" * 60)
    print(f"  Month : June (06)")
    print(f"  Days  : {', '.join(days)}")
    print(f"  Hours : {', '.join(hours)} UTC")
    print(f"  Area  : {area}")
    print()

    for year in years:
        output_file = os.path.join(
            output_dir,
            f"midland_surface_{year}.nc"
        )

        # Skip this year if the file already exists
        if os.path.exists(output_file):
            print(f"  [{year}] Already exists, skipping: {output_file}")
            downloaded_files.append(output_file)
            continue

        print(f"  [{year}] Downloading... (do not close the terminal)")

        client = cdsapi.Client()

        client.retrieve(
            "reanalysis-era5-single-levels",
            {
                "product_type": "reanalysis",
                "format": "netcdf",
                "variable": [
                    "geopotential",
                    "2m_temperature",
                    "surface_pressure",
                    "10m_u_component_of_wind",
                    "10m_v_component_of_wind",
                    "100m_u_component_of_wind",
                    "100m_v_component_of_wind",
                    "instantaneous_10m_wind_gust",
                    "total_precipitation",
                ],
                "year": [year],
                "month": ["06"],
                "day": days,
                "time": hours,
                "area": area,
            },
            output_file
        )

        print(f"  [{year}] OK -> {output_file}")
        downloaded_files.append(output_file)

    print(f"\n[OK] Surface data downloaded: {len(downloaded_files)} files.")
    return downloaded_files


def download_all(output_dir=OUTPUT_DIR):
    """
    Downloads both ERA5 files (pressure levels and surface) in sequence.

    This is the main entry point of this module. Running this function
    from a computer with internet is everything needed to prepare the
    historical atmospheric data for IREC.

    Parameters
    ----------
    output_dir : str
        Folder where both sets of NetCDF files will be saved.
        Created automatically if it does not exist.
        Default: "data/weather".

    Returns
    -------
    dict
        Dictionary with the lists of downloaded file paths::

            {
                "pressure_levels": ["data/weather/midland_pressure_levels_2015.nc", ...],
                "surface":         ["data/weather/midland_surface_2015.nc", ...]
            }

    Notes
    -----
    Both downloads are done in sequence because the CDS does not allow
    parallel requests with a single account. Total estimated time is
    20 minutes to 2 hours depending on server load.
    """
    print("\n" + "=" * 60)
    print("  VOLTA - ERA5 Data Download for IREC 2026")
    print("  Site: Midland, Texas | Window: June 15-20")
    print("=" * 60)

    files_pl = download_pressure_levels(output_dir=output_dir)
    files_sfc = download_surface(output_dir=output_dir)

    print("\n" + "=" * 60)
    print("  DOWNLOAD COMPLETED")
    print("=" * 60)
    print(f"  Pressure levels : {len(files_pl)} files")
    print(f"  Surface data    : {len(files_sfc)} files")
    print()
    print("  These files can now be used with environment_builder.py")
    print("  without an internet connection.")
    print("=" * 60 + "\n")

    return {
        "pressure_levels": files_pl,
        "surface": files_sfc
    }


# ---------------------------------------------------------------------------
# Entry point when running directly from the terminal
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """
    Run this script directly to download the ERA5 data.

    From the project root folder::

        python environment/download_era5.py

    Make sure your .cdsapirc file is configured before running.
    See the setup instructions at the top of this file.
    """
    download_all()