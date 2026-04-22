from src.sims import File_simulation

from rocketpy import Flight, MonteCarlo, Environment
from rocketpy.stochastic import (
    StochasticEnvironment,
    StochasticFlight,
    StochasticRocket,
    StochasticSolidMotor,
    StochasticNoseCone,
    StochasticParachute,
    StochasticTrapezoidalFins,
)

from environment.environment_builder import EnvironmentBuilder

import numpy as np


def run_montecarlo_test(
    rocket_file,
    motor_name,
    n_simulations
):
    print("RUNNING MONTECARLO TEST")

    # ---------------------------
    # 1. ROCKET BASE
    # ---------------------------
    sim = File_simulation(rocket_file, motor_name)

    # ---------------------------
    # 2. ENVIRONMENTS ERA5 (VARIOS)
    # ---------------------------
    builder = EnvironmentBuilder()

    envs, labels = builder.build_historical_environments(
        years=[2022, 2023, 2024],
        days=[15, 16, 17],
        utc_hours=[12, 15, 18]
    )

    print(f"Usando {len(envs)} environments para promedio")

    # ---------------------------
    # 3. PROMEDIO DE VIENTO (CON INTERPOLACIÓN)
    # ---------------------------
    heights = envs[0].wind_velocity_x.source[:, 0]

    u_interp_all = []
    v_interp_all = []

    for env in envs:
        h_env = env.wind_velocity_x.source[:, 0]
        u_env = env.wind_velocity_x.source[:, 1]
        v_env = env.wind_velocity_y.source[:, 1]

        u_interp = np.interp(heights, h_env, u_env)
        v_interp = np.interp(heights, h_env, v_env)

        u_interp_all.append(u_interp)
        v_interp_all.append(v_interp)

    u_mean = np.mean(u_interp_all, axis=0)
    v_mean = np.mean(v_interp_all, axis=0)

    assert heights.shape == u_mean.shape == v_mean.shape, "Dimensiones inconsistentes"

    # ---------------------------
    # 4. CREAR ENVIRONMENT PROMEDIO
    # ---------------------------
    base_env = envs[0]

    avg_env = Environment(
        latitude=base_env.latitude,
        longitude=base_env.longitude,
        elevation=base_env.elevation
    )

    wind_u_profile = list(zip(heights, u_mean))
    wind_v_profile = list(zip(heights, v_mean))

    avg_env.set_atmospheric_model(
        type="custom_atmosphere",
        pressure=None,
        temperature=None,
        wind_u=wind_u_profile,
        wind_v=wind_v_profile,
    )

    # ---------------------------
    # 5. STOCHASTIC ENVIRONMENT
    # ---------------------------
    stochastic_env = StochasticEnvironment(
        environment=avg_env,
        ensemble_member=None,
    )

    # ---------------------------
    # 6. MOTOR ESTOCÁSTICO
    # ---------------------------
    total_impulse_nominal = sim.motor.total_impulse

    stochastic_motor = StochasticSolidMotor(
        solid_motor=sim.motor,
        total_impulse=(total_impulse_nominal, 0.05 * total_impulse_nominal, "normal"),
        burn_start_time=(0, 0.05, "normal"),
    )

    # ---------------------------
    # 7. ROCKET ESTOCÁSTICO
    # ---------------------------
    stochastic_rocket = StochasticRocket(
        rocket=sim.rocket,
        mass=(sim.rocket.mass, 0.02 * sim.rocket.mass, "normal"),
    )

    stochastic_rocket.add_motor(stochastic_motor, position=0.001)

    stochastic_nose = StochasticNoseCone(
        nosecone=sim.nose_cone,
        length=0.01,
    )
    stochastic_rocket.add_nose(stochastic_nose, position=(0, 0.001))

    stochastic_fins = StochasticTrapezoidalFins(
        trapezoidal_fins=sim.fin_set,
        span=0.005,
    )
    stochastic_rocket.add_trapezoidal_fins(
        stochastic_fins,
        position=(0.001, "normal")
    )

    stochastic_main = StochasticParachute(
        parachute=sim.main,
        cd_s=0.1,
    )
    stochastic_rocket.add_parachute(stochastic_main)

    stochastic_drogue = StochasticParachute(
        parachute=sim.drogue,
        cd_s=0.1,
    )
    stochastic_rocket.add_parachute(stochastic_drogue)

    # ---------------------------
    # 8. FLIGHT ESTOCÁSTICO
    # ---------------------------
    base_flight = Flight(
        rocket=sim.rocket,
        environment=avg_env,
        rail_length=5.18,
        inclination=5,
        heading=90
    )

    stochastic_flight = StochasticFlight(
        flight=base_flight,
        inclination=(85, 1),
        heading=(0, 2)
    )

    # ---------------------------
    # 9. MONTECARLO
    # ---------------------------
    mc = MonteCarlo(
        filename="test_mc",
        environment=stochastic_env,
        rocket=stochastic_rocket,
        flight=stochastic_flight,
    )

    mc.simulate(
        number_of_simulations=n_simulations,
        append=False
    )

    print("MonteCarlo terminado")


if __name__ == "__main__":
    run_montecarlo_test(
        rocket_file="IREC_version04",
        motor_name="AeroTech_N3300R",
        n_simulations=20
    )