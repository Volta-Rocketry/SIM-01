import sims
import numpy as np
from rocketpy import Environment

lat=31.0525
lon=-103.54467
elev=891

alts = [0,300,500,800,1000,1300,1500, 2000, 2500,3000]
angles = np.ones(len(alts))*120
vels = [15, 12, 10, 13, 15, 12, 10, 8, 7, 7d]

env6 = sims.generate_variable_wind_profile(lat=lat, lon=lon, elev=elev, heights_ref=alts, angles_ref=angles, speeds_ref=vels)
env6.info()
""" 

file_name = "IREC_version1"
motor_name = "AeroTech_N3300R"

file = sims.File_simulation(file_name, motor_name)
file.graph_motor()
file.show_motor_info()
file.graph_rocket()
file.show_rocket_info()


env = Environment(
    date=(2019, 8, 10, 21),
    latitude=-23.363611,
    longitude=-48.011389,
    elevation=668,
)

envaaa = sims.generate_cte_wind_cte_angle(angle=281, speed=10.19)


file.run_single_flight_sim(env= envaaa,
    rail_length=5.7,
    inclination=5.3,    
    heading=53
)

#file.single_flight_sim.plots.trajectory_3d()

#print(file.extract_initial_conditions_sim_data(file.single_flight_sim))

env1 = sims.generate_cte_wind_cte_angle(angle=0, speed=5)
env2 = sims.generate_cte_wind_cte_angle(angle=90, speed=5)
env3 = sims.generate_cte_wind_cte_angle(angle=180, speed=5)
env4 = sims.generate_cte_wind_cte_angle(angle=270, speed=5)

envs = [env1, env2, env3, env4]
envs_names = ['0 deg', '90 deg', '180 deg', '270 deg']
rail_lengths = [5.7]
inclinations = [0]
headings = [0]
elevations = [0]


multiple_files, keys = file.run_multiple_flight_sims(envs=envs, envs_names=envs_names,
    rail_lengths=rail_lengths,
    inclinations=inclinations,
    headings=headings,
    elevations=elevations
)

print(keys[0])

df = sims.compare_usual_important_data(multiple_files, keys)
print(df) """
""" 
for key in keys:
    multiple_files[key].plots.trajectory_3d()
    print(sims.extract_initial_conditions_sim_data(multiple_files[key]))
 """




""" env = sims.generate_cte_wind_cte_angle(angle=281, speed=10.19)
#env.plots.atmospheric_model()


alts = [0, 20000, 40000]
vels = [5, 10, 2]
angles = [0, 90, 270]

env2 = sims.generate_cte_wind_cte_angle_per_height(alts, angles, vels)
#env2.plots.atmospheric_model()

env3 = sims.generate_nsy_wind_cte_angle(angle=281, speed=10.19, turbulence=0.1, deviation=2)
#env3.plots.atmospheric_model()

env4 = sims.generate_cte_wind_nsy_angle(angle=281, speed=10.19, turbulence=0.5, deviation=2)
#env4.plots.atmospheric_model()

env5 = sims.generate_nsy_wind_nsy_angle(angle=281, speed=10.19, speed_turbulence=0.1, speed_deviation=2, angle_turbulence=0.5, angle_deviation=2)
#env5.plots.atmospheric_model()

env6 = sims.generate_variable_wind_profile(alts, angles, vels)
env6.plots.atmospheric_model()

 """

# Generador de modelos atmosfericos
# Asumiendo angulo constante, velocidad constante en la altura
# Asumiendo angulo y velocidad discretizado a alturas especificas
# Genernado una curva de ruido de velocidad con un punto central
# Generando una curva de ruido de viento con un punto central por alturas