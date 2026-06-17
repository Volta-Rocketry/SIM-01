from src.sims import File_simulation
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from rocketpy import Flight, MonteCarlo, Environment, Function
from rocketpy.stochastic import (
    StochasticEnvironment,
    StochasticFlight,
    StochasticRocket,
    StochasticSolidMotor,
    StochasticNoseCone,
    StochasticParachute,
    StochasticTrapezoidalFins,
)

import datetime
import requests
import numpy as np
import pandas as pd


def run_montecarlo_test(
    rocket_file,
    motor_name,
    cg_true,
    cp_true,
    mass_true,
    n_simulations,
):
    print("RUNNING MONTECARLO TEST")

    # =========================================================
    # 1. ROCKET BASE
    # =========================================================
    sim = File_simulation(
        rocket_file,
        motor_name,
        cg_true,
        cp_true,
        mass_true,
    )

    # =========================================================
    # 2. DRAG
    # =========================================================
    drag_multiplier = 1.0

    original_power_off = sim.rocket.power_off_drag
    original_power_on = sim.rocket.power_on_drag

    sim.rocket.power_off_drag = Function(
        lambda mach: original_power_off.get_value_opt(mach) * drag_multiplier,
        inputs="Mach",
        outputs="Cd",
    )

    sim.rocket.power_on_drag = Function(
        lambda mach: original_power_on.get_value_opt(mach) * drag_multiplier,
        inputs="Mach",
        outputs="Cd",
    )

    # =========================================================
    # 3. ENVIRONMENT
    # =========================================================
    # GFS via NOMADS/OpenDAP fue dado de baja en febrero 2026.
    # Se usa Open-Meteo (gratuito, sin API key) que internamente
    # corre el mismo modelo GFS de NOAA con perfil de viento
    # real por niveles de presión (superficie → ~26 km ASL).

    _LAT       = 31.03641
    _LON       = -103.53957
    _ELEVATION = 890
    _DAYS_AHEAD = 0          # lanzamiento en ~2 días
    _HOUR_UTC   = 12         # 13:00 UTC = 07:00 CDT (UTC-6)

    # Niveles de presión a consultar (hPa).
    # Cubren desde superficie hasta ~26 km; ~700 hPa ≈ 3000 m ASL.
    _PRESSURE_LEVELS = [
        1000, 975, 950, 925, 900, 875, 850,
        800,  750, 700, 650, 600, 550, 500,
        450,  400, 350, 300, 250, 200,
    ]

    _target_date = (
        datetime.datetime.utcnow() + datetime.timedelta(days=_DAYS_AHEAD)
    )
    _date_str = _target_date.strftime("%Y-%m-%d")

    def _pressure_to_altitude_isa(p_hpa):
        # Convierte presion (hPa) a altura ASL (m) via formula ISA.
        # Precision suficiente para perfil de viento en simulacion.
        P0, T0, L, g, R = 1013.25, 288.15, 0.0065, 9.80665, 287.05
        p = p_hpa
        if p >= 226.32:           # troposfera (0 - 11 km)
            return (T0 / L) * (1.0 - (p / P0) ** (R * L / g))
        else:                     # estratosfera baja (11 - 20 km)
            return 11000.0 + (R * 216.65 / g) * np.log(226.32 / p)

    # Nombres correctos de Open-Meteo: windspeed_{p}hPa / winddirection_{p}hPa
    # (formato sin guion bajo entre wind y speed/direction).
    # Se usa /v1/forecast con forecast_days=3 para cubrir 2 dias adelante.
    # NO se usan start_date/end_date juntos con forecast_days (causa 400).
    _hourly_vars = []
    for _p in _PRESSURE_LEVELS:
        _hourly_vars.append(f"windspeed_{_p}hPa")
        _hourly_vars.append(f"winddirection_{_p}hPa")

    _resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude":        _LAT,
            "longitude":       _LON,
            "hourly":          ",".join(_hourly_vars),
            "wind_speed_unit": "ms",
            "timezone":        "UTC",
            "forecast_days":   3,
        },
        timeout=30,
    )
    _resp.raise_for_status()
    _hourly = _resp.json()["hourly"]

    # Seleccionar índice de hora más cercana al lanzamiento
    _times = _hourly["time"]
    _target_time_str = f"{_date_str}T{_HOUR_UTC:02d}:00"
    if _target_time_str in _times:
        _t_idx = _times.index(_target_time_str)
    else:
        _t_idx = min(
            range(len(_times)),
            key=lambda i: abs(int(_times[i][11:13]) - _HOUR_UTC),
        )
    print(f"Forecast cargado para: {_times[_t_idx]} UTC")

    # Construir perfil de viento por altura ISA
    _heights_list  = []
    _wind_u_list   = []
    _wind_v_list   = []

    for _p in _PRESSURE_LEVELS:
        _spd = _hourly[f"windspeed_{_p}hPa"][_t_idx]
        _dir = _hourly[f"winddirection_{_p}hPa"][_t_idx]
        if None in (_spd, _dir):
            continue
        _gh  = _pressure_to_altitude_isa(_p)
        _rad = np.deg2rad(float(_dir))
        _heights_list.append(_gh)
        _wind_u_list.append(-float(_spd) * np.sin(_rad))   # componente Este
        _wind_v_list.append(-float(_spd) * np.cos(_rad))   # componente Norte

    # Ordenar ascendentemente por altura
    _sort_idx      = np.argsort(_heights_list)
    _heights_arr   = np.array(_heights_list)[_sort_idx]
    _wind_u_arr    = np.array(_wind_u_list)[_sort_idx]
    _wind_v_arr    = np.array(_wind_v_list)[_sort_idx]

    # ── Diagnóstico de perfil de viento ──────────────────────────────────
    _SEP = "─" * 68
    print()
    print(_SEP)
    print(f"  PERFIL DE VIENTO GFS  |  {_times[_t_idx]} UTC  |  {_date_str}")
    print(f"  Sitio: lat={_LAT}  lon={_LON}  elev={_ELEVATION} m ASL")
    print(_SEP)
    print(f"  {'Presión':>8}  {'Alt ASL':>8}  {'Alt AGL':>8}  {'Spd':>6}  {'Dir':>6}  {'U(E)':>7}  {'V(N)':>7}")
    print(f"  {'(hPa)':>8}  {'(m)':>8}  {'(m)':>8}  {'(m/s)':>6}  {'(°)':>6}  {'(m/s)':>7}  {'(m/s)':>7}")
    print("  " + "·" * 66)

    for _i, (_p, _h, _u, _v) in enumerate(zip(
        [_PRESSURE_LEVELS[_j] for _j in _sort_idx],
        _heights_arr, _wind_u_arr, _wind_v_arr
    )):
        _spd_i = float(np.sqrt(_u**2 + _v**2))
        _dir_i = float(np.degrees(np.arctan2(-_u, -_v)) % 360)
        _agl_i = _h - _ELEVATION
        _marker = " ◄ APOGEO OBJ." if abs(_h - (_ELEVATION + 3048)) < 200 else ""
        print(
            f"  {_p:>8.0f}  {_h:>8.0f}  {_agl_i:>8.0f}  "
            f"{_spd_i:>6.1f}  {_dir_i:>6.1f}  {_u:>7.2f}  {_v:>7.2f}{_marker}"
        )

    print(_SEP)

    # Resumen en niveles clave para el vuelo
    _key_agls = [0, 500, 1000, 1500, 2000, 2500, 3048, 4000, 5000]
    print()
    print(f"  RESUMEN EN ALTURAS CLAVE (AGL desde {_ELEVATION} m ASL)")
    print(f"  {'AGL (m)':>8}  {'ASL (m)':>8}  {'Spd (m/s)':>10}  {'Spd (km/h)':>11}  {'Dir (°)':>8}  {'Descripción':}")
    print("  " + "·" * 70)
    for _agl_target in _key_agls:
        _asl_target = _agl_target + _ELEVATION
        _k = int(np.argmin(np.abs(_heights_arr - _asl_target)))
        _spd_k = float(np.sqrt(_wind_u_arr[_k]**2 + _wind_v_arr[_k]**2))
        _dir_k = float(np.degrees(np.arctan2(-_wind_u_arr[_k], -_wind_v_arr[_k])) % 360)
        _desc = {
            0:    "Superficie (riel)",
            500:  "Baja capa límite",
            1000: "Capa límite superior",
            1500: "Transición",
            2000: "Fase subsónica",
            2500: "Cerca de apogeo",
            3048: "OBJETIVO 10k ft",
            4000: "Post-apogeo",
            5000: "Referencia alta",
        }.get(_agl_target, "")
        print(
            f"  {_agl_target:>8}  {_asl_target:>8}  {_spd_k:>10.2f}  "
            f"{_spd_k*3.6:>11.2f}  {_dir_k:>8.1f}  {_desc}"
        )
    print(_SEP)
    print()

    avg_env = Environment(
        latitude=_LAT,
        longitude=_LON,
        elevation=_ELEVATION,
    )

    avg_env.set_date(
        (_target_date.year, _target_date.month, _target_date.day, _HOUR_UTC),
        timezone="UTC",
    )

    avg_env.set_atmospheric_model(type="standard_atmosphere")

    avg_env.process_custom_atmosphere(
        wind_u=list(zip(_heights_arr.tolist(), _wind_u_arr.tolist())),
        wind_v=list(zip(_heights_arr.tolist(), _wind_v_arr.tolist())),
    )

    # =========================================================
    # 4. BASE FLIGHT
    # =========================================================
    base_flight = Flight(
        rocket=sim.rocket,
        environment=avg_env,
        rail_length=5.2,
        inclination=84,
        heading=90,
    )

    # =========================================================
    # 5. STOCHASTIC ENVIRONMENT
    # =========================================================
    stochastic_env = StochasticEnvironment(
        environment=avg_env,
        ensemble_member=None,
        wind_velocity_x_factor=(1, 0.10, "normal"),
        wind_velocity_y_factor=(1, 0.15, "normal"),
    )

    # =========================================================
    # 6. STOCHASTIC MOTOR
    # =========================================================
    total_impulse_nominal = sim.motor.total_impulse

    stochastic_motor = StochasticSolidMotor(
        solid_motor=sim.motor,
        total_impulse=(total_impulse_nominal, 0.02 * total_impulse_nominal, "normal"),
        burn_start_time=(0, 0.01, "normal"),
    )

    # =========================================================
    # 7. STOCHASTIC ROCKET
    # =========================================================
    stochastic_rocket = StochasticRocket(
        rocket=sim.rocket,
        mass=(sim.rocket.mass, 0.005 * sim.rocket.mass, "normal"),
    )

    stochastic_rocket.add_motor(stochastic_motor, position=0.001)

    stochastic_nose = StochasticNoseCone(
        nosecone=sim.nose_cone,
        length=0.002,
    )
    stochastic_rocket.add_nose(stochastic_nose, position=(0, 0.001))

    stochastic_fins = StochasticTrapezoidalFins(
        trapezoidal_fins=sim.fin_set,
        span=0.001,
    )
    stochastic_rocket.add_trapezoidal_fins(
        stochastic_fins,
        position=(0.001, "normal"),
    )

    stochastic_main = StochasticParachute(
        parachute=sim.main,
        cd_s=0.02,
    )
    stochastic_rocket.add_parachute(stochastic_main)

    stochastic_drogue = StochasticParachute(
        parachute=sim.drogue,
        cd_s=0.02,
    )
    stochastic_rocket.add_parachute(stochastic_drogue)

    # =========================================================
    # 8. STOCHASTIC FLIGHT
    # =========================================================
    stochastic_flight = StochasticFlight(
        flight=base_flight,
        inclination=(84, 1),
        heading=(90, 2),
    )

    # =========================================================
    # 9. CUSTOM OUTPUT COLUMNS
    # =========================================================
    # RocketPy exporta apogee por defecto, pero aquí guardamos
    # dos referencias para evitar ambigüedad:
    # - apogee_altitude_agl: valor directo del vuelo
    # - apogee_altitude_asl: ajustado con la elevación del sitio

    # =========================================================
    # EXPORTAR VECTOR DE ESTADO COMPLETO EN APOGEO
    # =========================================================

    # ---------------------------------------------------------
    # POSICIÓN INERCIAL
    # ---------------------------------------------------------

    def get_apogee_x(flight):
        return flight.x(flight.apogee_time)


    def get_apogee_y(flight):
        return flight.y(flight.apogee_time)


    def get_apogee_z(flight):
        return flight.z(flight.apogee_time)


    # ---------------------------------------------------------
    # VELOCIDADES INERCIALES
    # ---------------------------------------------------------

    def get_apogee_vx(flight):
        return flight.vx(flight.apogee_time)


    def get_apogee_vy(flight):
        return flight.vy(flight.apogee_time)


    def get_apogee_vz(flight):
        return flight.vz(flight.apogee_time)


    # ---------------------------------------------------------
    # EULER ANGLES
    # ---------------------------------------------------------
    # phi   -> roll
    # theta -> pitch
    # psi   -> yaw
    # ---------------------------------------------------------

    def get_apogee_phi(flight):
        return flight.phi(flight.apogee_time)


    def get_apogee_theta(flight):
        return flight.theta(flight.apogee_time)


    def get_apogee_psi(flight):
        return flight.psi(flight.apogee_time)


    # ---------------------------------------------------------
    # BODY ANGULAR RATES
    # ---------------------------------------------------------
    # w1 w2 w3
    # ---------------------------------------------------------

    def get_apogee_wx(flight):
        return flight.w1(flight.apogee_time)


    def get_apogee_wy(flight):
        return flight.w2(flight.apogee_time)


    def get_apogee_wz(flight):
        return flight.w3(flight.apogee_time)


    # ---------------------------------------------------------
    # VIENTO EN APOGEO
    # ---------------------------------------------------------

    def get_apogee_wind_u(flight):

        altitude = flight.altitude(flight.apogee_time)

        return flight.env.wind_velocity_x(altitude)


    def get_apogee_wind_v(flight):

        altitude = flight.altitude(flight.apogee_time)

        return flight.env.wind_velocity_y(altitude)


    # ---------------------------------------------------------
    # CG EN APOGEO
    # ---------------------------------------------------------

    def get_apogee_cg(flight):

        return flight.rocket.center_of_mass(
            flight.apogee_time
        )


    # ---------------------------------------------------------
    # ALTITUDES
    # ---------------------------------------------------------

    def get_apogee_altitude_asl(flight):
        return flight.apogee

    def get_apogee_altitude_agl(flight):
        return flight.altitude(flight.apogee_time)


    # =========================================================
    # DATA COLLECTOR COMPLETO
    # =========================================================

    custom_data_collector = {

        # -----------------------------------------------------
        # ALTITUDES
        # -----------------------------------------------------

        "apogee_altitude_agl":
            get_apogee_altitude_agl,

        "apogee_altitude_asl":
            get_apogee_altitude_asl,

        # -----------------------------------------------------
        # POSICIÓN
        # -----------------------------------------------------

        "state_apogee_x":
            get_apogee_x,

        "state_apogee_y":
            get_apogee_y,

        "state_apogee_z":
            get_apogee_z,

        # -----------------------------------------------------
        # VELOCIDADES
        # -----------------------------------------------------

        "state_apogee_vx":
            get_apogee_vx,

        "state_apogee_vy":
            get_apogee_vy,

        "state_apogee_vz":
            get_apogee_vz,

        # -----------------------------------------------------
        # EULER ANGLES
        # -----------------------------------------------------

        "apogee_phi":
            get_apogee_phi,

        "apogee_theta":
            get_apogee_theta,

        "apogee_psi":
            get_apogee_psi,

        # -----------------------------------------------------
        # BODY RATES
        # -----------------------------------------------------

        "apogee_wx":
            get_apogee_wx,

        "apogee_wy":
            get_apogee_wy,

        "apogee_wz":
            get_apogee_wz,

        # -----------------------------------------------------
        # VIENTO
        # -----------------------------------------------------

        "wind_u_apogee":
            get_apogee_wind_u,

        "wind_v_apogee":
            get_apogee_wind_v,

        # -----------------------------------------------------
        # CG
        # -----------------------------------------------------

        "cg_apogee":
            get_apogee_cg,
    }
    # =========================================================
    # 10. MONTECARLO
    # =========================================================
    mc = MonteCarlo(
        filename="test_mc",
        environment=stochastic_env,
        rocket=stochastic_rocket,
        flight=stochastic_flight,
        data_collector=custom_data_collector,
    )

    mc.simulate(
        number_of_simulations=n_simulations,
        append=False,
    )

    # =========================================================
    # 11. SUMMARY
    # =========================================================

    outputs_df = pd.DataFrame(mc.outputs_log)

    summary = {

        # -----------------------------------------------------
        # APOGEE
        # -----------------------------------------------------

        "apogee_mean":
            outputs_df["apogee"].mean(),

        "apogee_std":
            outputs_df["apogee"].std(ddof=1),

        "apogee_altitude_agl_mean":
            outputs_df["apogee_altitude_agl"].mean(),

        "apogee_altitude_agl_std":
            outputs_df["apogee_altitude_agl"].std(ddof=1),

        "apogee_altitude_asl_mean":
            outputs_df["apogee_altitude_asl"].mean(),

        "apogee_altitude_asl_std":
            outputs_df["apogee_altitude_asl"].std(ddof=1),

        "apogee_time_mean":
            outputs_df["apogee_time"].mean(),

        "apogee_time_std":
            outputs_df["apogee_time"].std(ddof=1),

        # -----------------------------------------------------
        # MACH
        # -----------------------------------------------------

        "max_mach_mean":
            outputs_df["max_mach_number"].mean(),

        "max_mach_std":
            outputs_df["max_mach_number"].std(ddof=1),

        # -----------------------------------------------------
        # RAIL
        # -----------------------------------------------------

        "out_of_rail_velocity_mean":
            outputs_df["out_of_rail_velocity"].mean(),

        "out_of_rail_velocity_std":
            outputs_df["out_of_rail_velocity"].std(ddof=1),

        # -----------------------------------------------------
        # IMPACT
        # -----------------------------------------------------

        "x_impact_mean":
            outputs_df["x_impact"].mean(),

        "y_impact_mean":
            outputs_df["y_impact"].mean(),

        # -----------------------------------------------------
        # POSITION
        # -----------------------------------------------------

        "state_apogee_x_mean":
            outputs_df["state_apogee_x"].mean(),

        "state_apogee_x_std":
            outputs_df["state_apogee_x"].std(ddof=1),

        "state_apogee_y_mean":
            outputs_df["state_apogee_y"].mean(),

        "state_apogee_y_std":
            outputs_df["state_apogee_y"].std(ddof=1),

        "state_apogee_z_mean":
            outputs_df["state_apogee_z"].mean(),

        "state_apogee_z_std":
            outputs_df["state_apogee_z"].std(ddof=1),

        # -----------------------------------------------------
        # VELOCITIES
        # -----------------------------------------------------

        "state_apogee_vx_mean":
            outputs_df["state_apogee_vx"].mean(),

        "state_apogee_vx_std":
            outputs_df["state_apogee_vx"].std(ddof=1),

        "state_apogee_vy_mean":
            outputs_df["state_apogee_vy"].mean(),

        "state_apogee_vy_std":
            outputs_df["state_apogee_vy"].std(ddof=1),

        "state_apogee_vz_mean":
            outputs_df["state_apogee_vz"].mean(),

        "state_apogee_vz_std":
            outputs_df["state_apogee_vz"].std(ddof=1),

        # -----------------------------------------------------
        # EULER ANGLES
        # -----------------------------------------------------

        "apogee_phi_mean":
            outputs_df["apogee_phi"].mean(),

        "apogee_phi_std":
            outputs_df["apogee_phi"].std(ddof=1),

        "apogee_theta_mean":
            outputs_df["apogee_theta"].mean(),

        "apogee_theta_std":
            outputs_df["apogee_theta"].std(ddof=1),

        "apogee_psi_mean":
            outputs_df["apogee_psi"].mean(),

        "apogee_psi_std":
            outputs_df["apogee_psi"].std(ddof=1),

        # -----------------------------------------------------
        # BODY RATES
        # -----------------------------------------------------

        "apogee_wx_mean":
            outputs_df["apogee_wx"].mean(),

        "apogee_wx_std":
            outputs_df["apogee_wx"].std(ddof=1),

        "apogee_wy_mean":
            outputs_df["apogee_wy"].mean(),

        "apogee_wy_std":
            outputs_df["apogee_wy"].std(ddof=1),

        "apogee_wz_mean":
            outputs_df["apogee_wz"].mean(),

        "apogee_wz_std":
            outputs_df["apogee_wz"].std(ddof=1),

        # -----------------------------------------------------
        # WIND
        # -----------------------------------------------------

        "wind_u_apogee_mean":
            outputs_df["wind_u_apogee"].mean(),

        "wind_u_apogee_std":
            outputs_df["wind_u_apogee"].std(ddof=1),

        "wind_v_apogee_mean":
            outputs_df["wind_v_apogee"].mean(),

        "wind_v_apogee_std":
            outputs_df["wind_v_apogee"].std(ddof=1),

        # -----------------------------------------------------
        # CG
        # -----------------------------------------------------

        "cg_apogee_mean":
            outputs_df["cg_apogee"].mean(),

        "cg_apogee_std":
            outputs_df["cg_apogee"].std(ddof=1),
    }

    summary_df = pd.DataFrame([summary])

    summary_df.to_csv(
        "test_mc_summary.csv",
        index=False
    )

    # =========================================================
    # 12. GRÁFICAS
    # =========================================================

    import matplotlib.patches as mpatches
    from matplotlib.patches import Ellipse
    from matplotlib.lines import Line2D

    # Paleta consistente
    C0, C1, C2, C3, C4 = "#1C8DBB", "#E84C4C", "#2ECC71", "#F39C12", "#283747"
    SAVE_KW = dict(dpi=150, bbox_inches="tight")

    # ── A. Vuelo de referencia: Altitud y Mach vs tiempo ─────────────────
    # base_flight.z(t) = coordenada vertical inercial = AGL directamente.
    # base_flight.time incluye tiempos pre-lanzamiento (negativos); se
    # filtra desde t=0 para mostrar solo el vuelo real.
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

    t_raw  = base_flight.time
    t      = [ti for ti in t_raw if ti >= 0]
    alt    = [base_flight.altitude(ti)           for ti in t]   # AGL en metros
    mach   = [base_flight.mach_number(ti) for ti in t]

    axes[0].plot(t, alt,  color=C0, linewidth=2)
    axes[0].axhline(3048, color=C2, linestyle="--", linewidth=1.2,
                    label="Target apogee 10k ft (3048 m)")
    axes[0].set_ylabel("Altitude AGL (m)", fontsize=9)
    axes[0].set_title("Reference Flight — Altitude & Mach vs Time", fontsize=10, fontweight="bold")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(t, mach, color=C1, linewidth=2)
    axes[1].axhline(1.0, color=C3, linestyle="--", linewidth=1.2, label="Mach 1")
    axes[1].set_ylabel("Mach Number", fontsize=9)
    axes[1].set_xlabel("Time (s)", fontsize=9)
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig("plot_altitude_mach_vs_time.png", **SAVE_KW)
    plt.close(fig)

    # ── B. Mach vs Drag (Cd) ─────────────────────────────────────────────
    mach_vals = sorted(set(round(base_flight.mach_number(ti), 3) for ti in t))
    cd_off = [base_flight.rocket.power_off_drag(m) for m in mach_vals]
    cd_on  = [base_flight.rocket.power_on_drag(m)  for m in mach_vals]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(mach_vals, cd_off, color=C0, linewidth=2, label="Power-off (coast)")
    ax.plot(mach_vals, cd_on,  color=C1, linewidth=2, label="Power-on (burn)")
    ax.axvline(1.0, color=C3, linestyle="--", linewidth=1, label="Mach 1")
    ax.set_xlabel("Mach Number", fontsize=9)
    ax.set_ylabel("Drag Coefficient Cd", fontsize=9)
    ax.set_title("Aerodynamic Drag — Mach vs Cd", fontsize=10, fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig("plot_mach_vs_drag.png", **SAVE_KW)
    plt.close(fig)

    # ── C. Histogramas MonteCarlo (4 variables clave) ─────────────────────
    mc_vars = {
        "apogee_altitude_agl":   ("Apogee Altitude AGL", "m",   C0, True),
        "out_of_rail_velocity":  ("Out-of-Rail Velocity", "m/s", C1, True),
        "max_mach_number":       ("Maximum Mach Number",  "",    C2, False),
        "x_impact":              ("X Impact (East)",      "m",   C4, False),
    }
    # Filtrar las que realmente existen en outputs_df
    mc_vars = {k: v for k, v in mc_vars.items() if k in outputs_df.columns}

    if mc_vars:
        fig, axes = plt.subplots(2, 2, figsize=(11, 8))
        axes = axes.flatten()

        for ax, (col, (label, unit, color, show_target)) in zip(axes, mc_vars.items()):
            data = outputs_df[col].dropna()
            n_bins = max(5, int(len(data)**0.5))
            ax.hist(data, bins=n_bins, color=color, edgecolor="white",
                    linewidth=0.5, alpha=0.85)

            mu   = data.mean()
            sig  = data.std(ddof=1)
            xlab = f"{label} ({unit})" if unit else label

            ax.axvline(mu,        color="black",  linewidth=2.0, label=f"Mean = {mu:.1f}")
            ax.axvline(mu + sig,  color="gray",   linewidth=1.2, linestyle="--",
                       label=f"±1σ = {sig:.1f}")
            ax.axvline(mu - sig,  color="gray",   linewidth=1.2, linestyle="--")

            if show_target and col == "apogee_altitude_agl":
                ax.axvline(3048, color=C2, linewidth=1.5, linestyle=":",
                           label="Target 3048 m")

            ax.set_xlabel(xlab, fontsize=8)
            ax.set_ylabel("Occurrences", fontsize=8)
            ax.set_title(label, fontsize=9, fontweight="bold")
            ax.legend(fontsize=7)
            ax.grid(True, alpha=0.25, axis="y")

        # Ocultar ejes sobrantes si hay menos de 4 variables
        for ax in axes[len(mc_vars):]:
            ax.set_visible(False)

        fig.suptitle("Monte Carlo — Key Output Distributions", fontsize=11, fontweight="bold")
        fig.tight_layout()
        fig.savefig("plot_mc_histograms.png", **SAVE_KW)
        plt.close(fig)

    # ── D. Landing Dispersion Map ─────────────────────────────────────────
    if "x_impact" in outputs_df.columns and "y_impact" in outputs_df.columns:
        x_land = outputs_df["x_impact"].dropna().values
        y_land = outputs_df["y_impact"].dropna().values

        distances = np.sqrt(x_land**2 + y_land**2)
        r_max = distances.max()
        r_95  = np.percentile(distances, 95)
        r_68  = np.percentile(distances, 68)

        cx, cy   = x_land.mean(), y_land.mean()
        std_x    = x_land.std()
        std_y    = y_land.std()

        # Posición LCO/RSO (coordenadas relativas al pad del ESRA site)
        _R      = 6371000.0
        _LAT0   = 31.047292;  _LON0 = -103.527281
        _LAT_S  = 31.037589;  _LON_S = -103.537530
        SPEC_CX = (_LON_S - _LON0) * np.pi/180 * _R * np.cos(_LAT0 * np.pi/180)
        SPEC_CY = (_LAT_S - _LAT0) * np.pi/180 * _R
        SPEC_R  = 50.0
        DIST_PAD_SPEC = np.sqrt(SPEC_CX**2 + SPEC_CY**2)

        COL_RMAX = C4
        COL_R95  = C0
        COL_SPEC = C3
        COL_E95  = C1
        COL_E68  = C2

        fig, ax = plt.subplots(figsize=(8, 7.5))

        # LCO/RSO zone
        ax.add_patch(plt.Circle((SPEC_CX, SPEC_CY), SPEC_R,
            edgecolor=COL_SPEC, facecolor=COL_SPEC, alpha=0.25, zorder=1))
        ax.add_patch(plt.Circle((SPEC_CX, SPEC_CY), SPEC_R,
            edgecolor=COL_SPEC, facecolor="none", linewidth=2, zorder=2))
        ax.annotate("LCO/RSO &\nSpectator Zone",
            xy=(SPEC_CX, SPEC_CY),
            xytext=(SPEC_CX + 300, SPEC_CY - 400),
            ha="center", va="top", fontsize=7, fontweight="bold", color=COL_SPEC, zorder=10,
            arrowprops=dict(arrowstyle="-|>", color=COL_SPEC, lw=1.0))

        # Radius circles from pad
        ax.add_patch(plt.Circle((0,0), r_max, edgecolor=COL_RMAX, facecolor="none",
            linestyle="--", linewidth=1.6, zorder=3))
        ax.add_patch(plt.Circle((0,0), r_95, edgecolor=COL_R95, facecolor="none",
            linestyle="-.", linewidth=1.4, zorder=3))

        # Dispersion ellipses
        ax.add_patch(Ellipse(xy=(cx,cy), width=2*2.45*std_x, height=2*2.45*std_y,
            edgecolor=COL_E95, facecolor=COL_E95, alpha=0.12, linewidth=0, zorder=4))
        ax.add_patch(Ellipse(xy=(cx,cy), width=2*2.45*std_x, height=2*2.45*std_y,
            edgecolor=COL_E95, facecolor="none", linewidth=2.0, zorder=4))
        ax.add_patch(Ellipse(xy=(cx,cy), width=2*1.18*std_x, height=2*1.18*std_y,
            edgecolor=COL_E68, facecolor=COL_E68, alpha=0.18, linewidth=0, zorder=5))
        ax.add_patch(Ellipse(xy=(cx,cy), width=2*1.18*std_x, height=2*1.18*std_y,
            edgecolor=COL_E68, facecolor="none", linewidth=2.0, zorder=5))

        # Landing points
        ax.scatter(x_land, y_land, color=C0, s=18, alpha=0.55, zorder=6,
                   linewidths=0, label="Landing points")

        # Launch site
        ax.scatter(0, 0, color="black", s=200, marker="^", zorder=11)
        ax.annotate("Launch Site", xy=(0,0), xytext=(-80, 120),
            textcoords="offset points", fontsize=7, fontweight="bold",
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.0), zorder=12)

        # Centroid
        ax.scatter(cx, cy, color="black", s=90, marker="+", zorder=12, linewidths=2.5)
        ax.annotate(f"Centroid\n({cx:.0f} m E, {cy:.0f} m N)",
            xy=(cx,cy), xytext=(-80, 80), textcoords="offset points", fontsize=7,
            arrowprops=dict(arrowstyle="-", color="black", lw=0.8), zorder=12)

        # Pad ↔ LCO/RSO arrow
        ax.annotate("", xy=(SPEC_CX, SPEC_CY), xytext=(0, 0),
            arrowprops=dict(arrowstyle="<->", color="crimson", lw=1.6), zorder=13)
        angle = np.degrees(np.arctan2(SPEC_CY, SPEC_CX))
        if angle < -90 or angle > 90:
            angle += 180
        ax.text(SPEC_CX / 2, SPEC_CY / 2, f" {DIST_PAD_SPEC:.0f} m",
            ha="center", va="bottom", fontsize=7, color="crimson", fontweight="bold",
            rotation=angle, zorder=14)

        # Stats box
        ax.annotate(
            f"$r_{{68}}$ = {r_68:.0f} m\n$r_{{95}}$ = {r_95:.0f} m\n"
            f"$r_{{max}}$ = {r_max:.0f} m",
            xy=(0.97, 0.97), xycoords="axes fraction", ha="right", va="top", fontsize=7,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                      edgecolor="gray", alpha=0.9), zorder=13)

        # North arrow
        ax.annotate("", xy=(0.04, 0.97), xytext=(0.04, 0.91),
            xycoords="axes fraction",
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.5), zorder=13)
        ax.text(0.04, 0.975, "N", transform=ax.transAxes,
            ha="center", va="bottom", fontsize=11, fontweight="bold", zorder=13)

        # Legend
        legend_handles = [
            mpatches.Patch(color=C0,     alpha=0.8,  label="Landing points"),
            mpatches.Patch(color=COL_SPEC, alpha=0.4, label="LCO/RSO & Spectator Zone"),
            mpatches.Patch(color=COL_E95, alpha=0.4, label=f"~95% Ellipse"),
            mpatches.Patch(color=COL_E68, alpha=0.4, label=f"~68% Ellipse"),
            Line2D([0],[0], color=COL_RMAX, linestyle="--", linewidth=1.6,
                   label=f"Max radius = {r_max:.0f} m"),
            Line2D([0],[0], color=COL_R95, linestyle="-.", linewidth=1.4,
                   label=f"95% radius = {r_95:.0f} m"),
            Line2D([0],[0], color="black", marker="^", linestyle="None",
                   markersize=8, label="Launch Site"),
        ]
        ax.legend(handles=legend_handles, loc="lower right", fontsize=7,
                  framealpha=0.9, edgecolor="gray")

        ax.set_xlabel("Distance East (m)", fontsize=9)
        ax.set_ylabel("Distance North (m)", fontsize=9)
        ax.set_title(
            f"Landing Dispersion — IREC 2026\n"
            f"n = {len(x_land)} simulations",
            fontsize=10, fontweight="bold")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3, linewidth=0.5)
        fig.tight_layout()
        fig.savefig("plot_landing_dispersion.png", **SAVE_KW)
        plt.close(fig)

    print("\nGráficas guardadas:")
    print("  · plot_altitude_mach_vs_time.png")
    print("  · plot_mach_vs_drag.png")
    print("  · plot_mc_histograms.png")
    print("  · plot_landing_dispersion.png")

    print("\nMonteCarlo terminado")



if __name__ == "__main__":
    run_montecarlo_test(
        rocket_file="IREC_version_08",
        cg_true=1.99,
        cp_true=2.48,
        mass_true=24.944,
        motor_name="AeroTech_N3300R",
        n_simulations=1000,
    )