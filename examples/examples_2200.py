import src.sims as sims
import pandas as pd

# %%
file_name = "IREC_version1"
motor_name = "AeroTech_N2220DM"

file = sims.File_simulation(file_name, motor_name)

# %%
file.graph_motor()
file.show_motor_info()

# %%
file.graph_rocket()
file.show_rocket_info()

# %%
lat = 40.4168
lon = -3.7038
elev = 667  # Elevation in meters

env1 = sims.generate_cte_wind_cte_angle(lat=lat, lon=lon, elev=elev, angle=180, speed=5)
env2 = sims.generate_cte_wind_cte_angle(lat=lat, lon=lon, elev=elev, angle=180, speed=10)
env3 = sims.generate_cte_wind_cte_angle(lat=lat, lon=lon, elev=elev, angle=180, speed=15)
env4 = sims.generate_cte_wind_cte_angle(lat=lat, lon=lon, elev=elev, angle=180, speed=20)

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

df = sims.compare_usual_important_data(multiple_files, keys)

# %%
pd.set_option('display.float_format', lambda x: f'{x:.3f}')
df

# %%
multiple_files[keys[0]].plots.trajectory_3d()

# %%
env1.info()

# %%



