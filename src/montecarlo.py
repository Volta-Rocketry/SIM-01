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
    # Mantengo tu configuración base y le agrego un perfil de viento
    # más realista con variación con la altura.
    avg_env = Environment(
        latitude=32.990254,
        longitude=-106.974998,
        elevation=890,
    )

    avg_env.set_atmospheric_model(
        type="standard_atmosphere"
    )

    # Viento promedio derivado del análisis histórico:
    # - cerca del suelo: ~4.6 m/s
    # - en altura/apogeo: ~11.5 m/s
    # - componente norte pequeña al inicio y casi nula al subir
    # - componente este dominante en altura
    heights = np.array([
        0,
        100,
        500,
        1000,
        2000,
        3000,
        5000,
        8000,
        10000,
        15000,
    ], dtype=float)

    # X = Este, Y = Norte
    wind_u = np.array([   # componente Este
        3.8,
        4.0,
        4.5,
        5.0,
        5.5,
        6.0,
        7.5,
        9.0,
        10.0,
        11.5,
    ], dtype=float)

    wind_v = np.array([   # componente Norte
        1.8,
        1.6,
        1.3,
        1.0,
        0.7,
        0.5,
        0.3,
        0.15,
        0.08,
        0.00,
    ], dtype=float)

    avg_env.process_custom_atmosphere(
        wind_u=list(zip(heights, wind_u)),
        wind_v=list(zip(heights, wind_v)),
    )

    # =========================================================
    # 4. BASE FLIGHT
    # =========================================================
    base_flight = Flight(
        rocket=sim.rocket,
        environment=avg_env,
        rail_length=5.2,
        inclination=90,
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
        inclination=(90, 0.5),
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

    print("\nMonteCarlo terminado")



if __name__ == "__main__":
    run_montecarlo_test(
        rocket_file="IREC_version_06(2)",
        cg_true=1.98,
        cp_true=2.48,
        mass_true=27.363,
        motor_name="AeroTech_N3300R",
        n_simulations=20,
    )
