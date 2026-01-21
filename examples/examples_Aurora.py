import src.sims as sims
import pandas as pd
from rocketpy import Environment

# %%
file_name = "AURORA_v02"
motor_name = "Volta_motor_v1"

file = sims.File_simulation(file_name, motor_name)

# %%
file.graph_motor()
file.show_motor_info()

# %%
file.graph_rocket()
file.show_rocket_info()

# %% [markdown]
# # Site 1

# %%
lat = 12.2830555556
lon = -71.9100000000
elev = 13  # Elevation in meters

env0 = sims.generate_cte_wind_cte_angle(lat=lat, lon=lon, elev=elev, angle=90, speed=0)
env1 = sims.generate_cte_wind_cte_angle(lat=lat, lon=lon, elev=elev, angle=90, speed=5)
env2 = sims.generate_cte_wind_cte_angle(lat=lat, lon=lon, elev=elev, angle=90, speed=10)
env3 = sims.generate_cte_wind_cte_angle(lat=lat, lon=lon, elev=elev, angle=90, speed=15)
env4 = sims.generate_cte_wind_cte_angle(lat=lat, lon=lon, elev=elev, angle=90, speed=20)

env5 = Environment(
    date=(2019, 8, 10, 15),
    latitude= lat,
    longitude= lon,
    elevation= elev,
)

envs = [env2]
env_names = ["normal"]
rail_lengths = [5.2] # Longitud del riel en metros
inclinations = [3] # Inclinación del riel en grados
headings = [0, 90, 270, 45] # Rumbo del riel en grados
elevations = [elev] 


multiple_files, keys = file.run_multiple_flight_sims(envs=envs, envs_names=env_names,
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
for i, key in enumerate(keys):
    print(f"--- Simulation {i}: {key} ---")
    multiple_files[keys[i]].plots.trajectory_3d()

# %%
for i, key in enumerate(keys):
    print(f"--- Simulation {i}: {key} ---")
    multiple_files[keys[i]].prints.impact_conditions()

# %% [markdown]
# # Site 2

# %%
lat = 3.2316666667
lon = -75.1691666667
elev = 436  # Elevation in meters

env0 = sims.generate_cte_wind_cte_angle(lat=lat, lon=lon, elev=elev, angle=90, speed=0)
env1 = sims.generate_cte_wind_cte_angle(lat=lat, lon=lon, elev=elev, angle=90, speed=5)
env2 = sims.generate_cte_wind_cte_angle(lat=lat, lon=lon, elev=elev, angle=90, speed=10)
env3 = sims.generate_cte_wind_cte_angle(lat=lat, lon=lon, elev=elev, angle=90, speed=15)
env4 = sims.generate_cte_wind_cte_angle(lat=lat, lon=lon, elev=elev, angle=90, speed=20)

env5 = Environment(
    date=(2019, 8, 10, 15),
    latitude= lat,
    longitude= lon,
    elevation= elev,
)

envs = [env2]
env_names = ["normal"]
rail_lengths = [5.2] # Longitud del riel en metros
inclinations = [3] # Inclinación del riel en grados
headings = [0, 90, 270, 45] # Rumbo del riel en grados
elevations = [elev] 


multiple_files, keys = file.run_multiple_flight_sims(envs=envs, envs_names=env_names,
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
for i, key in enumerate(keys):
    print(f"--- Simulation {i}: {key} ---")
    multiple_files[keys[i]].plots.trajectory_3d()

# %%
for i, key in enumerate(keys):
    print(f"--- Simulation {i}: {key} ---")
    multiple_files[keys[i]].prints.impact_conditions()

# %%
for i, key in enumerate(keys):
    print(f"--- Simulation {i}: {key} ---")
    multiple_files[keys[i]].info()


