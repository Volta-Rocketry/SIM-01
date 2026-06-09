"""
wind_analysis.py
================
Statistical wind analysis from ERA5 pressure-level data.
VOLTA Simulation Subsystem – IREC 2026

Purpose
-------
Extract U/V wind statistics from ERA5 historical data (2015-2024)
across altitude levels relevant to Cattleya's flight envelope.

Outputs
-------
1. wind_stats.csv       – Per-level statistics (mean, std, percentiles, %).
2. wind_params.json     – Monte Carlo-ready parameters per altitude band.
3. wind_summary.txt     – Human-readable report for the PTR.
4. Plots (optional)     – Call plot_all() to generate figures.

Usage
-----
    python wind_analysis.py

    # Or from another script:
    from wind_analysis import run_analysis
    stats, params = run_analysis()

Authors
-------
Simulation Subsystem – VOLTA
"""

import os
import json
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR    = "data/weather"       # Folder with .nc files
OUTPUT_DIR  = "data/analysis"      # Folder for outputs
YEARS       = list(range(2015, 2025))

# Pressure levels available in the .nc files [hPa]
PRESSURE_LEVELS = [
    1000, 975, 950, 925, 900, 875, 850, 825,
    800, 775, 750, 700, 650, 600, 550, 500,
    450, 400, 350, 300, 250, 225, 200, 175,
    150, 125, 100
]

# Altitude bands of interest for Cattleya's flight (~10 km apogee)
# Each entry: (label, min_alt_m, max_alt_m)
ALTITUDE_BANDS = [
    ("Ground–1 km",    0,     1000),
    ("1–3 km",      1000,     3000),
    ("3–6 km",      3000,     6000),
    ("6–10 km",     6000,    10000),
    ("10–15 km",   10000,    15000),
]

# Standard atmosphere: approximate altitude [m] per pressure level [hPa]
# Source: ICAO Standard Atmosphere
STD_ALT_M = {
    1000: 110,   975: 320,   950: 540,   925: 762,   900: 988,
     875: 1220,  850: 1457,  825: 1700,  800: 1949,  775: 2206,
     750: 2469,  700: 3012,  650: 3591,  600: 4206,  550: 4865,
     500: 5574,  450: 6344,  400: 7185,  350: 8117,  300: 9164,
     250: 10363, 225: 11034, 200: 11784, 175: 12632, 150: 13608,
     125: 14764, 100: 16180,
}

PERCENTILES = [5, 10, 25, 50, 75, 90, 95]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_era5_winds(data_dir=DATA_DIR, years=YEARS):
    """
    Load U and V wind components from ERA5 pressure-level NetCDF files.

    Parameters
    ----------
    data_dir : str
        Directory containing midland_pressure_levels_YYYY.nc files.
    years : list of int
        Years to load.

    Returns
    -------
    dict
        {pressure_level_hPa: {"u": np.array, "v": np.array}}
        Each array has shape (N_samples,) pooling all years/days/hours.
    """
    try:
        import netCDF4 as nc
    except ImportError:
        raise ImportError(
            "netCDF4 is required. Install with:\n"
            "    pip install netCDF4"
        )

    # Accumulate data per pressure level
    data = {p: {"u": [], "v": []} for p in PRESSURE_LEVELS}
    loaded_years = []

    for year in years:
        fpath = os.path.join(data_dir, f"midland_pressure_levels_{year}.nc")
        if not os.path.exists(fpath):
            print(f"  [WARN] File not found, skipping: {fpath}")
            continue

        with nc.Dataset(fpath, "r") as ds:
            # Identify variable names (may vary by CDS version)
            u_var = _find_var(ds, ["u", "u_component_of_wind", "u10"])
            v_var = _find_var(ds, ["v", "v_component_of_wind", "v10"])
            p_var = _find_var(ds, ["pressure_level", "level", "isobaricInhPa"])

            if u_var is None or v_var is None:
                print(f"  [WARN] U/V variables not found in {fpath}, skipping.")
                continue

            pressure_axis = ds.variables[p_var][:]  # shape: (n_levels,)
            u_all = ds.variables[u_var][:]           # shape: (time, level, lat, lon)
            v_all = ds.variables[v_var][:]

            for p in PRESSURE_LEVELS:
                # Find index of this pressure level
                idx = np.where(np.abs(pressure_axis - p) < 1.0)[0]
                if len(idx) == 0:
                    continue
                idx = idx[0]

                # Extract all time steps and spatial points, flatten
                u_slice = np.array(u_all[:, idx, :, :]).flatten()
                v_slice = np.array(v_all[:, idx, :, :]).flatten()

                # Remove masked/NaN values
                mask = ~(np.ma.is_masked(u_slice) | np.isnan(u_slice) |
                         np.ma.is_masked(v_slice) | np.isnan(v_slice))
                data[p]["u"].extend(u_slice[mask].tolist())
                data[p]["v"].extend(v_slice[mask].tolist())

        loaded_years.append(year)
        print(f"  [OK] {year} loaded.")

    if not loaded_years:
        raise FileNotFoundError(
            f"No ERA5 files found in '{data_dir}'.\n"
            f"Expected files like: midland_pressure_levels_2015.nc"
        )

    print(f"\n  Loaded {len(loaded_years)} years: {loaded_years}")

    # Convert lists to numpy arrays
    for p in PRESSURE_LEVELS:
        data[p]["u"] = np.array(data[p]["u"])
        data[p]["v"] = np.array(data[p]["v"])

    return data


def _find_var(ds, candidates):
    """Return the first candidate variable name found in a NetCDF dataset."""
    for name in candidates:
        if name in ds.variables:
            return name
    # Try case-insensitive
    lower_vars = {k.lower(): k for k in ds.variables}
    for name in candidates:
        if name.lower() in lower_vars:
            return lower_vars[name.lower()]
    return None


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def compute_wind_statistics(data):
    """
    Compute full statistical profile for U, V, and wind speed per level.

    Parameters
    ----------
    data : dict
        Output of load_era5_winds().

    Returns
    -------
    pd.DataFrame
        One row per pressure level with columns:
        pressure_hPa, altitude_m, n_samples,
        u_mean, u_median, u_std, u_p05..u_p95, u_pct_above_mean,
        v_mean, v_median, v_std, v_p05..v_p95, v_pct_above_mean,
        speed_mean, speed_median, speed_std, speed_p05..speed_p95,
        speed_pct_above_mean, dir_mean_deg, dir_std_deg
    """
    rows = []

    for p in PRESSURE_LEVELS:
        u = data[p]["u"]
        v = data[p]["v"]

        if len(u) == 0:
            continue

        speed = np.sqrt(u**2 + v**2)
        direction = np.degrees(np.arctan2(u, v)) % 360  # meteorological: 0=N

        row = {
            "pressure_hPa": p,
            "altitude_m": STD_ALT_M.get(p, np.nan),
            "n_samples": len(u),
        }

        for label, arr in [("u", u), ("v", v), ("speed", speed)]:
            row[f"{label}_mean"]   = float(np.mean(arr))
            row[f"{label}_median"] = float(np.median(arr))
            row[f"{label}_std"]    = float(np.std(arr))
            row[f"{label}_min"]    = float(np.min(arr))
            row[f"{label}_max"]    = float(np.max(arr))

            for pct in PERCENTILES:
                row[f"{label}_p{pct:02d}"] = float(np.percentile(arr, pct))

            above_mean = float(np.mean(arr > np.mean(arr)) * 100)
            row[f"{label}_pct_above_mean"] = above_mean

        # Circular mean direction
        row["dir_mean_deg"] = float(_circular_mean(direction))
        row["dir_std_deg"]  = float(_circular_std(direction))

        rows.append(row)

    df = pd.DataFrame(rows).sort_values("altitude_m").reset_index(drop=True)
    return df


def compute_band_statistics(stats_df):
    """
    Aggregate statistics by altitude band for Monte Carlo parametrization.

    Parameters
    ----------
    stats_df : pd.DataFrame
        Output of compute_wind_statistics().

    Returns
    -------
    dict
        Monte Carlo parameters per altitude band:
        {band_label: {u: {mean, std, p05, p95, skew}, v: {...}, speed: {...}}}
    """
    from scipy import stats as sp_stats

    params = {}

    for label, alt_min, alt_max in ALTITUDE_BANDS:
        mask = (
            (stats_df["altitude_m"] >= alt_min) &
            (stats_df["altitude_m"] <  alt_max)
        )
        sub = stats_df[mask]

        if sub.empty:
            continue

        band = {}
        for comp in ["u", "v", "speed"]:
            # Weighted average of statistics (weight by n_samples)
            w = sub["n_samples"].values.astype(float)
            w /= w.sum()

            mean_val   = float(np.average(sub[f"{comp}_mean"],   weights=w))
            std_val    = float(np.average(sub[f"{comp}_std"],    weights=w))
            p05_val    = float(np.average(sub[f"{comp}_p05"],    weights=w))
            p25_val    = float(np.average(sub[f"{comp}_p25"],    weights=w))
            p50_val    = float(np.average(sub[f"{comp}_p50"],    weights=w))
            p75_val    = float(np.average(sub[f"{comp}_p75"],    weights=w))
            p95_val    = float(np.average(sub[f"{comp}_p95"],    weights=w))
            above_pct  = float(np.average(sub[f"{comp}_pct_above_mean"], weights=w))

            # Skewness: >0 means tail toward high values (more cases above mean)
            skewness = (mean_val - p50_val) / std_val if std_val > 0 else 0.0

            band[comp] = {
                "mean":          round(mean_val, 4),
                "std":           round(std_val,  4),
                "p05":           round(p05_val,  4),
                "p25":           round(p25_val,  4),
                "p50_median":    round(p50_val,  4),
                "p75":           round(p75_val,  4),
                "p95":           round(p95_val,  4),
                "pct_above_mean": round(above_pct, 2),
                "pct_below_mean": round(100 - above_pct, 2),
                "skewness":      round(skewness, 4),
                # Monte Carlo suggestion: use truncated normal or empirical CDF
                "mc_dist":       "normal",
                "mc_mu":         round(mean_val, 4),
                "mc_sigma":      round(std_val,  4),
            }

        params[label] = {
            "alt_min_m": alt_min,
            "alt_max_m": alt_max,
            "components": band,
        }

    return params


def _circular_mean(angles_deg):
    """Circular mean of angles in degrees."""
    rad = np.radians(angles_deg)
    return np.degrees(np.arctan2(np.mean(np.sin(rad)), np.mean(np.cos(rad)))) % 360


def _circular_std(angles_deg):
    """Circular standard deviation of angles in degrees."""
    rad = np.radians(angles_deg)
    R = np.sqrt(np.mean(np.sin(rad))**2 + np.mean(np.cos(rad))**2)
    return np.degrees(np.sqrt(-2 * np.log(R)))


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def generate_text_report(stats_df, band_params, output_path):
    """
    Write a human-readable wind statistics report.

    Parameters
    ----------
    stats_df : pd.DataFrame
    band_params : dict
    output_path : str
    """
    lines = []
    sep = "=" * 70

    lines += [
        sep,
        "  VOLTA – IREC 2026 | ERA5 Wind Statistical Analysis",
        "  Site: Midland, Texas | Period: June 15-20, 2015-2024",
        sep,
        "",
        "SECTION 1: Statistics per pressure level",
        "-" * 70,
        f"  {'Alt(m)':>7}  {'P(hPa)':>6}  {'N':>6}  "
        f"{'U mean':>7}  {'U std':>6}  {'V mean':>7}  {'V std':>6}  "
        f"{'Spd mean':>8}  {'Spd std':>7}  {'Dir°':>5}",
        "-" * 70,
    ]

    for _, row in stats_df.iterrows():
        lines.append(
            f"  {row['altitude_m']:>7.0f}  {row['pressure_hPa']:>6.0f}  "
            f"{row['n_samples']:>6}  "
            f"{row['u_mean']:>7.2f}  {row['u_std']:>6.2f}  "
            f"{row['v_mean']:>7.2f}  {row['v_std']:>6.2f}  "
            f"{row['speed_mean']:>8.2f}  {row['speed_std']:>7.2f}  "
            f"{row['dir_mean_deg']:>5.1f}"
        )

    lines += [
        "",
        "SECTION 2: Statistics by altitude band (Monte Carlo parametrization)",
        "-" * 70,
    ]

    for band_label, band in band_params.items():
        lines += [
            "",
            f"  Band: {band_label}  ({band['alt_min_m']}–{band['alt_max_m']} m MSL)",
            "",
        ]
        for comp in ["u", "v", "speed"]:
            b = band["components"][comp]
            lines += [
                f"    [{comp.upper()}]",
                f"      Mean ± Std       : {b['mean']:>7.3f} ± {b['std']:.3f} m/s",
                f"      Median (P50)     : {b['p50_median']:>7.3f} m/s",
                f"      P05 / P95        : {b['p05']:>7.3f}  /  {b['p95']:.3f} m/s",
                f"      % above mean     : {b['pct_above_mean']:>5.1f}%",
                f"      % below mean     : {b['pct_below_mean']:>5.1f}%",
                f"      Skewness         : {b['skewness']:>+7.4f}",
                f"      MC distribution  : {b['mc_dist']} (μ={b['mc_mu']:.3f}, σ={b['mc_sigma']:.3f})",
                "",
            ]

    lines += [
        sep,
        "  NOTE ON SKEWNESS:",
        "  Positive skewness → distribution tail toward higher values",
        "  (more extreme high-wind events than low-wind events).",
        "  Negative skewness → tail toward lower/more negative values.",
        sep,
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  [OK] Text report saved: {output_path}")


# ---------------------------------------------------------------------------
# Plotting (optional – requires matplotlib)
# ---------------------------------------------------------------------------

def plot_all(stats_df, band_params, output_dir=OUTPUT_DIR):
    """
    Generate diagnostic plots for the wind analysis.

    Saves the following figures:
    - wind_profiles.png      : U/V/Speed mean ± std vs altitude.
    - wind_percentiles.png   : Percentile ribbons (P05–P95) vs altitude.
    - wind_rose_bands.png    : Wind rose per altitude band.
    - wind_pct_above.png     : % above/below mean per level.

    Parameters
    ----------
    stats_df : pd.DataFrame
    band_params : dict
    output_dir : str
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("  [WARN] matplotlib not installed. Skipping plots.")
        return

    os.makedirs(output_dir, exist_ok=True)
    alt = stats_df["altitude_m"].values

    # ------------------------------------------------------------------ #
    # 1. Mean profiles with ±1σ bands
    # ------------------------------------------------------------------ #
    fig, axes = plt.subplots(1, 3, figsize=(15, 8), sharey=True)
    fig.suptitle(
        "ERA5 Wind Profiles – Midland TX | June 15-20, 2015-2024\n"
        "Mean ± 1σ (shaded)",
        fontsize=13, fontweight="bold"
    )

    for ax, comp, color, title in zip(
        axes,
        ["u", "v", "speed"],
        ["#2196F3", "#E91E63", "#4CAF50"],
        ["U component (East +) [m/s]",
         "V component (North +) [m/s]",
         "Wind Speed [m/s]"]
    ):
        mean = stats_df[f"{comp}_mean"].values
        std  = stats_df[f"{comp}_std"].values

        ax.fill_betweenx(alt, mean - std, mean + std,
                         alpha=0.25, color=color, label="±1σ")
        ax.plot(mean, alt, color=color, lw=2, label="Mean")
        ax.axvline(0, color="gray", lw=0.8, ls="--")
        ax.set_xlabel(title, fontsize=10)
        ax.set_ylabel("Altitude MSL [m]", fontsize=10)
        ax.set_title(title.split("[")[0].strip(), fontsize=11)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 17000)

    plt.tight_layout()
    path1 = os.path.join(output_dir, "wind_profiles.png")
    fig.savefig(path1, dpi=150)
    plt.close(fig)
    print(f"  [OK] wind_profiles.png saved.")

    # ------------------------------------------------------------------ #
    # 2. Percentile ribbons
    # ------------------------------------------------------------------ #
    fig, axes = plt.subplots(1, 3, figsize=(15, 8), sharey=True)
    fig.suptitle(
        "ERA5 Wind Percentile Profiles – Midland TX | June 15-20, 2015-2024",
        fontsize=13, fontweight="bold"
    )

    percentile_pairs = [(5, 95), (25, 75)]
    alpha_vals = [0.20, 0.35]

    for ax, comp, color, title in zip(
        axes,
        ["u", "v", "speed"],
        ["#2196F3", "#E91E63", "#4CAF50"],
        ["U component [m/s]", "V component [m/s]", "Wind Speed [m/s]"]
    ):
        for (p_lo, p_hi), alpha in zip(percentile_pairs, alpha_vals):
            lo = stats_df[f"{comp}_p{p_lo:02d}"].values
            hi = stats_df[f"{comp}_p{p_hi:02d}"].values
            ax.fill_betweenx(alt, lo, hi, alpha=alpha, color=color,
                             label=f"P{p_lo}–P{p_hi}")

        median = stats_df[f"{comp}_p50"].values
        ax.plot(median, alt, color=color, lw=2, label="Median (P50)")
        ax.axvline(0, color="gray", lw=0.8, ls="--")
        ax.set_xlabel(title, fontsize=10)
        ax.set_ylabel("Altitude MSL [m]", fontsize=10)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 17000)

    plt.tight_layout()
    path2 = os.path.join(output_dir, "wind_percentiles.png")
    fig.savefig(path2, dpi=150)
    plt.close(fig)
    print(f"  [OK] wind_percentiles.png saved.")

    # ------------------------------------------------------------------ #
    # 3. % above vs below mean per altitude
    # ------------------------------------------------------------------ #
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_title(
        "Wind Speed: % of cases above vs below historical mean\n"
        "Midland TX | June 15-20, 2015-2024",
        fontsize=12, fontweight="bold"
    )

    pct_above = stats_df["speed_pct_above_mean"].values
    pct_below = 100 - pct_above

    ax.barh(alt, pct_above, height=150, color="#E91E63",
            alpha=0.8, label="% above mean")
    ax.barh(alt, -pct_below, height=150, color="#2196F3",
            alpha=0.8, label="% below mean")
    ax.axvline(0, color="black", lw=1)
    ax.axvline(50, color="gray", lw=0.8, ls="--", alpha=0.5)
    ax.axvline(-50, color="gray", lw=0.8, ls="--", alpha=0.5)
    ax.set_xlabel("Percentage of historical observations [%]", fontsize=11)
    ax.set_ylabel("Altitude MSL [m]", fontsize=11)
    ax.set_xlim(-100, 100)
    ax.set_xticks(np.arange(-100, 101, 25))
    ax.set_xticklabels([f"{abs(x)}%" for x in np.arange(-100, 101, 25)])
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis="x")
    ax.set_ylim(0, 17000)

    plt.tight_layout()
    path3 = os.path.join(output_dir, "wind_pct_above.png")
    fig.savefig(path3, dpi=150)
    plt.close(fig)
    print(f"  [OK] wind_pct_above.png saved.")

    return [path1, path2, path3]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_analysis(data_dir=DATA_DIR, output_dir=OUTPUT_DIR, make_plots=True):
    """
    Run the complete wind statistical analysis pipeline.

    Parameters
    ----------
    data_dir : str
        Directory with ERA5 NetCDF files.
    output_dir : str
        Directory where outputs are saved.
    make_plots : bool
        If True, generate matplotlib figures.

    Returns
    -------
    tuple
        (stats_df, band_params)
        stats_df   : pd.DataFrame with per-level statistics
        band_params: dict with Monte Carlo parameters per altitude band
    """
    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "=" * 60)
    print("  VOLTA – ERA5 Wind Statistical Analysis")
    print("  IREC 2026 | Midland, Texas | June 15-20")
    print("=" * 60)

    # 1. Load data
    print("\n[1/4] Loading ERA5 pressure-level data...")
    wind_data = load_era5_winds(data_dir=data_dir)

    # 2. Compute statistics per level
    print("\n[2/4] Computing per-level statistics...")
    stats_df = compute_wind_statistics(wind_data)

    # 3. Aggregate by altitude band
    print("\n[3/4] Aggregating by altitude band...")
    band_params = compute_band_statistics(stats_df)

    # 4. Save outputs
    print("\n[4/4] Saving outputs...")

    csv_path = os.path.join(output_dir, "wind_stats.csv")
    stats_df.to_csv(csv_path, index=False, float_format="%.4f")
    print(f"  [OK] wind_stats.csv saved: {csv_path}")

    json_path = os.path.join(output_dir, "wind_params.json")
    with open(json_path, "w") as f:
        json.dump(band_params, f, indent=2)
    print(f"  [OK] wind_params.json saved: {json_path}")

    report_path = os.path.join(output_dir, "wind_summary.txt")
    generate_text_report(stats_df, band_params, report_path)

    if make_plots:
        print("\n  Generating plots...")
        plot_all(stats_df, band_params, output_dir=output_dir)

    # 5. Print quick summary
    _print_summary(stats_df, band_params)

    return stats_df, band_params


def _print_summary(stats_df, band_params):
    """Print a concise summary table to the console."""
    print("\n" + "=" * 60)
    print("  QUICK SUMMARY – Wind Speed by Altitude Band")
    print("=" * 60)
    print(f"  {'Band':<15} {'Mean':>6}  {'Std':>5}  {'P50':>5}  "
          f"{'P05':>5}  {'P95':>5}  {'%>avg':>6}")
    print("-" * 60)

    for band_label, band in band_params.items():
        b = band["components"]["speed"]
        print(
            f"  {band_label:<15} {b['mean']:>6.2f}  {b['std']:>5.2f}  "
            f"{b['p50_median']:>5.2f}  {b['p05']:>5.2f}  {b['p95']:>5.2f}  "
            f"{b['pct_above_mean']:>5.1f}%"
        )

    print("=" * 60)
    print("  Units: m/s | %> avg: % of obs with speed above historical mean")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    stats_df, band_params = run_analysis(
        data_dir=DATA_DIR,
        output_dir=OUTPUT_DIR,
        make_plots=True
    )