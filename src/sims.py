import json
import math
import numpy as np
import pandas as pd
from itertools import product
from scipy.signal import butter, filtfilt
from scipy.interpolate import interp1d
from rocketpy import Environment, Flight, Rocket, SolidMotor
from src.adjust_parameters import eval_adjust_motor_parameters

class File_simulation():
    def __init__(self, file_name, motor_name):
        self.file_name = file_name
        self.motor_name = motor_name
        self.file_status = False

        self.rocket_ready_for_simulation = False
        self.env_ready_for_simulation = False

        self.motor = None
        self.rocket = None
        self.fins = None
        self.nose_cone = None
        self.rail_buttons = None
        self.main = None
        self.drogue = None
        self.env = None

        self.single_flight_sim = None


        # -----
        _name_status = self.verify_file()
        _motor_status = self.verify_motor()

        if _name_status and _motor_status:
            print("File and motor verified")
            self.file_status = True
        else:
            raise ValueError("File or motor not verified")
                
        self.create_rocket()

    def verify_file(self):
        files_supported = ["IREC_version1", "test", "AURORA_v02"]
        if self.file_name in files_supported:
            return True
        else:
            raise ValueError(f"File name not supported, only files {files_supported} are allowed")
        
    def verify_motor(self):
        motors_supported = ["AeroTech_N2000W", "AeroTech_N2220DM", "AeroTech_N3300R", "Volta_motor_v1"]
        if self.motor_name in motors_supported:
            return True
        else:
            raise ValueError(f"Motor not supported, only motors {motors_supported} are allowed")
        
    def create_rocket(self):
        if self.file_status:
            print(f"Creating rocket for {self.file_name} with motor {self.motor_name}")
        else:
            print("File not verified. Cannot create rocket.")
            return
        
        # Abrir archivos con parametros
        # Abrir archivo con las configuraciones del cohete
        with open(f"parameters/rocket/parameters_{self.file_name}.json", "r", encoding="utf-8-sig") as f:
            rocket_data = json.load(f)

        airframe_data = rocket_data["airframe"]
        nosecone_data = rocket_data["nosecone"]
        rail_buttons_data = rocket_data["rail_buttons"]
        fins_data = rocket_data["fins"]
        parachutes_data = rocket_data["parachutes"]

        # Abrir archivo con las configuraciones del motor
        with open("parameters/motors/motors_parameters.json", "r", encoding="utf-8-sig") as f:
            _motor_data = json.load(f)
            motor_data = _motor_data[self.motor_name]


        # Ajust data
        motor_data = eval_adjust_motor_parameters(motor_data)

        # Create motor
        self.motor = SolidMotor(
            thrust_source=motor_data["thrust_source"],
            dry_mass=motor_data["dry_mass"],
            dry_inertia=motor_data["dry_inertia"],
            nozzle_radius=motor_data["nozzle_radius"],
            grain_number=motor_data["grain_number"],
            grain_density=motor_data["grain_density"],
            grain_outer_radius=motor_data["grain_outer_radius"],
            grain_initial_inner_radius=motor_data["grain_initial_inner_radius"],
            grain_initial_height=motor_data["grain_initial_height"],
            grain_separation=motor_data["grain_separation"],
            grains_center_of_mass_position=motor_data["grains_center_of_mass_position"],
            center_of_dry_mass_position=motor_data["center_of_dry_mass_position"],
            #burn_time=parameters.get("burn_time")[0], # NOTE: OPTIONAL
            #throat_radius=motor_data["throat_radius"], # NOTE: OPTIONAL
            coordinate_system_orientation=motor_data["coordinate_system_orientation"], # NOTE: OPTIONAL
            interpolation_method="linear", # NOTE: OPTIONAL
            nozzle_position=motor_data["nozzle_position"], # NOTE: OPTIONAL    
        )
        # Create rocket
        self.rocket = Rocket(
            radius= airframe_data["radius"], # m
            mass= airframe_data["mass"],   # Kg
            inertia=tuple(airframe_data["inertia"]),  # Kg.m^2 with NO MOTOR
            power_on_drag= 0.465,#airframe_data["power_on_drag"],
            power_off_drag= 0.465,#airframe_data["power_off_drag"],
            center_of_mass_without_motor=airframe_data["center_of_mass_without_motor"],
            coordinate_system_orientation=airframe_data["coordinate_system_orientation"]
        )

        self.rail_buttons = self.rocket.set_rail_buttons(
            upper_button_position= rail_buttons_data["upper_position"],
            lower_button_position= rail_buttons_data["upper_position"] + rail_buttons_data["distance"],
            angular_position=rail_buttons_data["angular_position"],
        )

        self.nose_cone = self.rocket.add_nose(
            length=nosecone_data["length"],
            kind=nosecone_data["kind"],
            position=0
        )

        self.fin_set = self.rocket.add_trapezoidal_fins(
            n= fins_data["number"],
            root_chord= fins_data["root_chord"],
            tip_chord= fins_data["tip_chord"],
            span= fins_data["span"],
            position= fins_data["position"],
            sweep_length= fins_data["sweep_length"],
            cant_angle= fins_data["cant_angle"],
            #airfoil=("../data/airfoils/NACA0012-radians.txt","radians"),
        )

        self.main = self.rocket.add_parachute(
            name=parachutes_data["main"]["name"],
            cd_s= parachutes_data["main"]["cd"]*parachutes_data["main"]["area"],
            trigger= parachutes_data["main"]["deploy_altitude"],      # ejection altitude in meters
            sampling_rate= 105,
            lag= parachutes_data["main"]["deploy_delay"]
            #noise=(0, 8.3, 0.5), # Optional
        )

        self.drogue = self.rocket.add_parachute(
            name= parachutes_data["drogue"]["name"],
            cd_s= parachutes_data["drogue"]["cd"]*parachutes_data["drogue"]["area"],
            trigger= parachutes_data["drogue"]["deploy_event"],  # ejection at apogee
            sampling_rate= 105,
            lag= parachutes_data["drogue"]["deploy_delay"]
            #noise=(0, 8.3, 0.5), # Optional
        )

        self.rocket.add_motor(self.motor, airframe_data["rocket_length"] - motor_data["offset"])

        self.rocket_ready_for_simulation = True
        print("Rocket created and ready for simulation")

    def show_rocket_info(self):
        if self.rocket_ready_for_simulation:
            self.rocket.info()
        else:
            raise ValueError("Rocket not ready for simulation.")
        
    def graph_rocket(self):
        if self.rocket_ready_for_simulation:            
            self.rocket.draw()            
        else:
            raise ValueError("Rocket not ready for simulation.")
        
    def show_motor_info(self):
        if self.motor is not None:
            self.motor.info()
        else:
            raise ValueError("Motor not defined.")
        
    def graph_motor(self):
        if self.motor is not None:
            self.motor.draw()
        else:
            raise ValueError("Motor not defined.")

    def add_enviroment(self, enviroment):
        self.env = enviroment
        if not isinstance(self.env, Environment):
            raise ValueError("Enviroment must be an instance of Environment class from RocketPy")
        
        self.env_ready_for_simulation = True

    def run_single_flight_sim(self, env, rail_length, inclination, heading):
        # Note, the heading is converted from angles 0 to 90.
        # A angle of inclination of 0 means vertical launch.

        if self.rocket_ready_for_simulation: #and self.env_ready_for_simulation:
            _rpy_inclination = 90 - inclination

            self.single_flight_sim = Flight(
                rocket=self.rocket,
                environment=env,
                rail_length=rail_length,
                inclination=_rpy_inclination,
                heading=heading
            )

            print("Single flight simulation completed")
        else:
            raise ValueError("Rocket or enviroment not ready for simulation.")

    def run_multiple_flight_sims(self, envs, envs_names, rail_lengths, inclinations, headings, elevations):
        simulation_files = {}
        keys = []
        for i, (env, rail_length, inclination, heading, elevation) in enumerate(
            product(envs, rail_lengths, inclinations, headings, elevations)):

            print(f"Runnin sim{i}")
            _rpy_inclination = 90 - inclination

            sim = Flight(
                rocket=self.rocket,
                environment=env,
                rail_length=rail_length,
                inclination=_rpy_inclination,
                heading=heading
            )

            key = f"ENV_{envs_names[0]}_RL{rail_length}_INC{inclination}_HDG{heading}_ELEV{elevation}"
            keys.append(key)
            simulation_files[key] = sim
            print(f"Simulation {i} completed")

        return simulation_files, keys

# ----- Extract data from simulations -----
def extract_initial_conditions_sim_data(sim):
    print("Entro acá")
    print(sim)
    t0 = sim.time[0]

    initial_x = sim.x(t0) # m
    initial_y = sim.y(t0) # m
    initial_z = sim.z(t0) # m

    initial_vx = sim.vx(t0) # m/s
    initial_vy = sim.vy(t0) # m/s
    initial_vz = sim.vz(t0) # m/s

    initial_e0 = sim.e0(t0) # Quaternion
    initial_e1 = sim.e1(t0) # Quaternion
    initial_e2 = sim.e2(t0) # Quaternion
    initial_e3 = sim.e3(t0) # Quaternion

    initial_roll = sim.phi(t0) # Spin
    initial_yaw = sim.theta(t0) # Nutation
    initial_pitch = sim.psi(t0) # Precession

    initial_w1 = sim.w1(t0) # Spin rate
    initial_w2 = sim.w2(t0) # Nutation rate
    initial_w3 = sim.w3(t0) # Precession rate

    initial_static_margin = sim.initial_stability_margin # Calibers

    rail_length = sim.rail_length # m
    rail_inclination = sim.inclination # °
    rail_heading = sim.heading # °

    frontal_surface_wind = sim.frontal_surface_wind # m/s
    lateral_surface_wind = sim.lateral_surface_wind # m/s

    initial_conditions_data = {
        "time": t0,
        "position": (initial_x, initial_y, initial_z),
        "velocity": (initial_vx, initial_vy, initial_vz),
        "quaternion": (initial_e0, initial_e1, initial_e2, initial_e3),
        "orientation": (initial_roll, initial_yaw, initial_pitch),
        "angular_velocity": (initial_w1, initial_w2, initial_w3),
        "static_margin": initial_static_margin,
        "rail_length": rail_length,
        "rail_inclination": rail_inclination,
        "rail_heading": rail_heading,
        "frontal_surface_wind": frontal_surface_wind,
        "lateral_surface_wind": lateral_surface_wind
    }

    return initial_conditions_data

def extract_out_of_rail_sim_data(sim):
    t_out_rail = sim.out_of_rail_time
    out_rail_vel = sim.out_of_rail_velocity
    out_rail_stability = sim.out_of_rail_stability_margin
    out_rail_angle_of_attack = sim.angle_of_attack(t_out_rail)
    out_rail_thrust_to_weight = sim.rocket.thrust_to_weight(t_out_rail)
    out_rail_reynolds = sim.reynolds_number(t_out_rail)

    out_of_rail_data = {
        "time": t_out_rail,
        "velocity": out_rail_vel,
        "stability": out_rail_stability,
        "angle_of_attack": out_rail_angle_of_attack,
        "thrust_to_weight": out_rail_thrust_to_weight,
        "reynolds": out_rail_reynolds
    }

    return out_of_rail_data 

def extract_burn_out_sim_data(sim):
    t_burn_out = sim.rocket.motor.burn_out_time
    
    burn_out_z = sim.z(t_burn_out) # ASL m
    burn_out_alt = sim.altitude(t_burn_out) # AGL m

    burn_out_speed = sim.speed(t_burn_out) # m/s
    burn_out_mach = sim.mach_number(t_burn_out) # Mach
    burn_out_accel = sim.acceleration(t_burn_out) # m/s^2
    burn_out_freestream_speed = sim.free_stream_speed(t_burn_out) # m/s

    burn_out_dynamic_pressure = sim.dynamic_pressure(t_burn_out) # Pa

    # REVISAR ACÁ COSAS RELEVANTES PARA LOS AIRBRAKES
    burn_out_data = {
        "time": t_burn_out,
        "z": burn_out_z,
        "altitude": burn_out_alt,
        "speed": burn_out_speed,
        "mach": burn_out_mach,
        "freestream_speed": burn_out_freestream_speed,
        "dynamic_pressure": burn_out_dynamic_pressure
    }
    return burn_out_data

def extract_apogee_sim_data(sim):

    t_apogee = sim.apogee_time

    apogee_x = sim.x(t_apogee) # m
    apogee_y = sim.y(t_apogee) # m
    apogee_lat = sim.latitude(t_apogee) # °
    apogee_lon = sim.longitude(t_apogee) # °

    apogee_z = sim.z(t_apogee) # ASL m
    apogee_alt = sim.altitude(t_apogee) # AGL m

    apogee_freestream_speed = sim.free_stream_speed(t_apogee) # m/s

    apogee_data = {
        "time": t_apogee,
        "x": apogee_x,
        "y": apogee_y,
        "latitude": apogee_lat,
        "longitude": apogee_lon,
        "z": apogee_z,
        "altitude": apogee_alt,
        "freestream_speed": apogee_freestream_speed
    }

    return apogee_data

def extract_impact_sim_data(sim):
    # NOTE: IMPORTANT, MUST BE CONSIDERED THAT IF THE SIM ENDS AT APOGEE, THIS IS NOT VALID
    t_impact = sim.t_final

    impact_x = sim.x_impact # m
    impact_y = sim.y_impact # m
    impact_lat = sim.latitude(t_impact) # °
    impact_lon = sim.longitude(t_impact) # °

    impact_z = sim.z(t_impact) # ASL m
    impact_alt = sim.altitude(t_impact) # AGL m

    impact_speed = sim.speed(t_impact) # m/s        

    impact_data = {
        "time": t_impact,
        "x": impact_x,
        "y": impact_y,
        "latitude": impact_lat,
        "longitude": impact_lon,
        "z": impact_z,
        "altitude": impact_alt,
        "speed": impact_speed            
    }

    return impact_data

def extract_maximum_values_sim_data(sim):
        max_speed = sim.max_speed # m/s
        max_speed_time = sim.max_speed_time # s

        max_mach = sim.max_mach_number # Mach
        max_mach_time = sim.max_mach_time # s

        max_reynolds = sim.max_reynolds_number # -
        max_reynolds_time = sim.max_reynolds_number_time # s

        max_dynamic_pressure = sim.max_dynamic_pressure # Pa
        max_dynamic_pressure_time = sim.max_dynamic_pressure_time # s

        max_acceleration_power_on = sim.max_acceleration_power_on # m/s^2
        max_acceleration_power_on_time = sim.max_acceleration_power_on_time # s

        max_Gs_power_on =sim.max_acceleration_power_on / sim.env.standard_g # G
        max_Gs_power_on_time = sim.max_acceleration_power_on_time # s

        max_acceleration_power_off = sim.max_acceleration_power_off # m/s^2
        max_acceleration_power_off_time = sim.max_acceleration_power_off_time # s

        max_Gs_power_off = sim.max_acceleration_power_off / sim.env.standard_g # G
        max_Gs_power_off_time = sim.max_acceleration_power_off_time # s

        max_stability_margin = sim.max_stability_margin # calibers
        max_stability_margin_time = sim.max_stability_margin_time # s

        max_upper_rb_normal_force = sim.max_rail_button1_normal_force # N
        max_upper_rb_shear_force = sim.max_rail_button1_shear_force # N

        max_lower_rb_normal_force = sim.max_rail_button2_normal_force # N
        max_lower_rb_shear_force = sim.max_rail_button2_shear_force # N
        

        max_values_data = {
            "max_speed": max_speed,
            "max_speed_time": max_speed_time,
            "max_mach": max_mach,
            "max_mach_time": max_mach_time,
            "max_reynolds": max_reynolds,
            "max_reynolds_time": max_reynolds_time,
            "max_dynamic_pressure": max_dynamic_pressure,
            "max_dynamic_pressure_time": max_dynamic_pressure_time,
            "max_acceleration_power_on": max_acceleration_power_on,
            "max_acceleration_power_on_time": max_acceleration_power_on_time,
            "max_Gs_power_on": max_Gs_power_on,
            "max_Gs_power_on_time": max_Gs_power_on_time,
            "max_acceleration_power_off": max_acceleration_power_off,
            "max_acceleration_power_off_time": max_acceleration_power_off_time,
            "max_Gs_power_off": max_Gs_power_off,
            "max_Gs_power_off_time": max_Gs_power_off_time,
            "max_stability_margin": max_stability_margin,
            "max_stability_margin_time": max_stability_margin_time,
            "max_upper_rb_normal_force": max_upper_rb_normal_force,
            "max_upper_rb_shear_force": max_upper_rb_shear_force,
            "max_lower_rb_normal_force": max_lower_rb_normal_force,
            "max_lower_rb_shear_force": max_lower_rb_shear_force
        }

        return max_values_data

def extract_usual_important_sim_data(sim):
    initial_static_margin = sim.initial_stability_margin # Calibers
    
    frontal_surface_wind = sim.frontal_surface_wind # m/s
    lateral_surface_wind = sim.lateral_surface_wind # m/s

    t_out_rail = sim.out_of_rail_time
    out_rail_vel = sim.out_of_rail_velocity
    out_rail_stability = sim.out_of_rail_stability_margin
    out_rail_angle_of_attack = sim.angle_of_attack(t_out_rail)
    out_rail_thrust_to_weight = sim.rocket.thrust_to_weight(t_out_rail)

    t_burn_out = sim.rocket.motor.burn_out_time
    burn_out_dynamic_pressure = sim.dynamic_pressure(t_burn_out)
    burn_out_accel = sim.acceleration(t_burn_out) # m/s^2

    t_apogee = sim.apogee_time
    apogee_alt = sim.altitude(t_apogee) # AGL m

    max_speed = sim.max_speed # m/s
    max_speed_time = sim.max_speed_time # s

    max_mach = sim.max_mach_number # Mach
    max_mach_time = sim.max_mach_number_time # s    

    max_dynamic_pressure = sim.max_dynamic_pressure # Pa
    max_dynamic_pressure_time = sim.max_dynamic_pressure_time # s

    max_acceleration_power_on = sim.max_acceleration_power_on # m/s^2
    max_acceleration_power_on_time = sim.max_acceleration_power_on_time # s

    max_Gs_power_on =sim.max_acceleration_power_on / sim.env.standard_g # G
    max_Gs_power_on_time = sim.max_acceleration_power_on_time # s

    max_acceleration_power_off = sim.max_acceleration_power_off # m/s^2
    max_acceleration_power_off_time = sim.max_acceleration_power_off_time # s

    max_Gs_power_off = sim.max_acceleration_power_off / sim.env.standard_g # G
    max_Gs_power_off_time = sim.max_acceleration_power_off_time # s

    max_stability_margin = sim.max_stability_margin # calibers    

    t_impact = sim.t_final
    impact_speed = sim.speed(t_impact) # m/s

    impact_x = sim.x_impact # m
    impact_y = sim.y_impact # m
    impact_lat = sim.latitude(t_impact) # °
    impact_lon = sim.longitude(t_impact) # °

    impact_radius = math.sqrt(impact_x**2 + impact_y**2) # m


    usual_important_data = {
        "initial_static_margin [calibers]": initial_static_margin,
        "frontal_surface_wind [m/s]": frontal_surface_wind,
        "lateral_surface_wind [m/s]": lateral_surface_wind,
        "out_rail_vel [m/s]": out_rail_vel,
        "out_rail_stability [calibers]": out_rail_stability,
        "out_rail_angle_of_attack [deg]": out_rail_angle_of_attack,
        "out_rail_thrust_to_weight [ratio]": out_rail_thrust_to_weight,
        "burn_out_dynamic_pressure [Pa]": burn_out_dynamic_pressure,
        "burn_out_time [s]": t_burn_out,
        "burn_out_accel [m/s²]": burn_out_accel,
        "apogee_alt [m]": apogee_alt,
        "apogee_time [s]": t_apogee,
        "max_speed [m/s]": max_speed,
        "max_speed_time [s]": max_speed_time,
        "max_mach [-]": max_mach,
        "max_mach_time [s]": max_mach_time,
        "max_dynamic_pressure [Pa]": max_dynamic_pressure,
        "max_dynamic_pressure_time [s]": max_dynamic_pressure_time,
        "max_acceleration_power_on [m/s²]": max_acceleration_power_on,
        "max_acceleration_power_on_time [s]": max_acceleration_power_on_time,
        "max_Gs_power_on [G]": max_Gs_power_on,
        "max_Gs_power_on_time [s]": max_Gs_power_on_time,
        "max_acceleration_power_off [m/s²]": max_acceleration_power_off,
        "max_acceleration_power_off_time [s]": max_acceleration_power_off_time,
        "max_Gs_power_off [G]": max_Gs_power_off,
        "max_Gs_power_off_time [s]": max_Gs_power_off_time,
        "max_stability_margin [calibers]": max_stability_margin,
        "impact_speed [m/s]": impact_speed,
        "impact_time [s]": t_impact,
        "impact_x [m]": impact_x,
        "impact_y [m]": impact_y,
        "impact_lat [°]": impact_lat,
        "impact_lon [°]": impact_lon,
        "impact_radius [m]": impact_radius
    }


    return usual_important_data

def compare_usual_important_data(sims, names):
    

    data = {}

    for key, sim in sims.items():
        try:
            # Extrae los datos relevantes
            results = extract_usual_important_sim_data(sim)
            data[key] = results
        except Exception as e:
            print(f"Error en simulación '{key}': {e}")
            continue

    # Crea DataFrame con variables como filas y simulaciones como columnas
    df = pd.DataFrame(data)

    if len(names) == len(df.columns):
        df.rename(columns=dict(zip(df.columns, names)), inplace=True)
    else:
        print("Advertencia: número de nombres no coincide con número de simulaciones.")

    df.index.name = "Variable"
    return df

# --- Funciones para generar modelos atmosfericos de viento y velocidad de python
def generate_cte_wind_cte_angle(lat, lon, elev, angle, speed):
    # Generates an enviroment using the same wind and angle at all altitudes
    # Angles are: 0° = Norte, 90° = Este, 180° = Sur, 270° = Oeste
    wind_u = -speed*math.sin(math.radians(angle))
    wind_v = -speed*math.cos(math.radians(angle))

    env = Environment(
        latitude=lat,
        longitude=lon,
        elevation=elev
    )
    env.set_atmospheric_model("custom_atmosphere",
                            pressure=None,
                            temperature=None,
                            wind_u=[(0, wind_u), (10000, wind_u)],
                            wind_v=[(0, wind_v), (10000, wind_v)]
                            )
    
    return env

def generate_cte_wind_cte_angle_per_height(lat, lon, elev, heights, angles, speeds):
    # Generates an enviroment using the same wind and angle at all altitudes
    # Angles are: 0° = Norte, 90° = Este, 180° = Sur, 270° = Oeste

    
    if len(heights) != len(angles) or len(heights) != len(speeds):
        raise ValueError("Heights, angles and speeds must have the same length")

    wind_u = []
    wind_v = []

    for i in range(len(heights)):
        wind_u.append((heights[i], -speeds[i]*math.sin(math.radians(angles[i]))))
        wind_v.append((heights[i], -speeds[i]*math.cos(math.radians(angles[i]))))

    env = Environment(
        latitude=lat,
        longitude=lon,
        elevation=elev
    )

    env.set_atmospheric_model("custom_atmosphere",
                            pressure=None,
                            temperature=None,
                            wind_u=wind_u,
                            wind_v=wind_v
                            )
    
    return env

def generate_nsy_wind_cte_angle(lat, lon, elev, angle, speed, turbulence, deviation):
    cutoff = 0.05
    heights = np.arange(0, 80000, 10)
    
    # Ruido blanco
    n = np.random.randn(len(heights))
    
    # Filtro pasa bajos (frecuencia normalizada)
    b, a = butter(2, cutoff)
    n_filtered = filtfilt(b, a, n)

    # Normalizar y aplicar turbulencia
    n_filtered /= np.std(n_filtered)
    wind = speed + deviation * turbulence * n_filtered

    # Proyecciones u y v (convención meteorológica)
    u = -wind * math.sin(math.radians(angle))
    v = -wind * math.cos(math.radians(angle))

    wind_u = np.column_stack((heights, u))
    wind_v = np.column_stack((heights, v))

    env = Environment(
        latitude=lat,
        longitude=lon,
        elevation=elev
    )

    env.set_atmospheric_model("custom_atmosphere",
                            pressure=None,
                            temperature=None,
                            wind_u=wind_u,
                            wind_v=wind_v
                            )
    
    return env

def generate_cte_wind_nsy_angle(lat, lon, elev, angle, speed, turbulence, deviation):
    cutoff = 0.05
    heights = np.arange(0, 80000, 10)
    
    # Ruido blanco
    n = np.random.randn(len(heights))
    
    # Filtro pasa bajos (frecuencia normalizada)
    b, a = butter(2, cutoff)
    n_filtered = filtfilt(b, a, n)

    # Normalizar y aplicar turbulencia angular
    n_filtered /= np.std(n_filtered)
    _angle = angle + deviation * turbulence * n_filtered

    # Proyecciones u y v (convención meteorológica)
    u = -speed * np.sin(np.radians(_angle))
    v = -speed * np.cos(np.radians(_angle))

    # Armar pares (altura, valor)
    wind_u = np.column_stack((heights, u))
    wind_v = np.column_stack((heights, v))

    # Crear ambiente
    env = Environment(
        latitude=lat,
        longitude=lon,
        elevation=elev
    )

    env.set_atmospheric_model(
        "custom_atmosphere",
        pressure=None,
        temperature=None,
        wind_u=wind_u,
        wind_v=wind_v
    )
    
    return env

def generate_nsy_wind_nsy_angle(lat, lon, elev, angle, speed, speed_turbulence, speed_deviation, angle_turbulence, angle_deviation):
    cutoff = 0.05
    heights = np.arange(0, 80000, 10)
    
    # Ruido blanco
    n_speed = np.random.randn(len(heights))
    n_angle = np.random.randn(len(heights))
    
    # Filtro pasa bajos (frecuencia normalizada)
    b, a = butter(2, cutoff)
    n_speed_filtered = filtfilt(b, a, n_speed)
    n_angle_filtered = filtfilt(b, a, n_angle)

    # Normalizar y aplicar turbulencia
    n_speed_filtered /= np.std(n_speed_filtered)
    n_angle_filtered /= np.std(n_angle_filtered)

    wind = speed + speed_deviation * speed_turbulence * n_speed_filtered
    angle_wind = angle + angle_deviation * angle_turbulence * n_angle_filtered

    # Proyecciones u y v (convención meteorológica)
    u = -wind * np.sin(np.radians(angle_wind))
    v = -wind * np.cos(np.radians(angle_wind))

    wind_u = np.column_stack((heights, u))
    wind_v = np.column_stack((heights, v))

    env = Environment(
        latitude=lat,
        longitude=lon,
        elevation=elev
    )

    env.set_atmospheric_model("custom_atmosphere",
                            pressure=None,
                            temperature=None,
                            wind_u=wind_u,
                            wind_v=wind_v
                            )
    
    return env

def generate_variable_wind_profile(lat, lon, elev, heights_ref, angles_ref, speeds_ref,
                                   speed_turbulence=0.1, speed_deviation=2,
                                   angle_turbulence=0.0, angle_deviation=0,
                                   max_altitude=80000, dz=10):
    """
    Genera un perfil de viento escalonado (por tramos constantes) con turbulencia.

    heights_ref: lista de alturas base [m]
    angles_ref: ángulos base [°] (convención meteorológica)
    speeds_ref: velocidades base [m/s]
    *_turbulence: intensidad relativa (0.1 = 10%)
    *_deviation: desviación absoluta del ruido
    max_altitude: altura máxima del perfil
    dz: resolución vertical [m]
    """

    # Validación
    if len(heights_ref) != len(angles_ref) or len(heights_ref) != len(speeds_ref):
        raise ValueError("Heights, angles and speeds must have the same length")

    # Dominio de altura
    heights = np.arange(0, max_altitude + dz, dz)
    wind = np.zeros_like(heights, dtype=float)
    angle_wind = np.zeros_like(heights, dtype=float)

    # Generador de ruido común
    cutoff = 0.05
    b, a = butter(2, cutoff)

    for i in range(len(heights_ref) - 1):
        h_low = heights_ref[i]
        h_high = heights_ref[i + 1]

        # Selección del tramo
        mask = (heights >= h_low) & (heights < h_high)

        # Ruido blanco y filtrado por tramo
        n_speed = np.random.randn(np.count_nonzero(mask))
        n_angle = np.random.randn(np.count_nonzero(mask))

        n_speed_filtered = filtfilt(b, a, n_speed)
        n_angle_filtered = filtfilt(b, a, n_angle)

        # Normalización
        n_speed_filtered /= np.std(n_speed_filtered)
        n_angle_filtered /= np.std(n_angle_filtered)

        # Perfil constante + turbulencia
        wind[mask] = speeds_ref[i] + speed_deviation * speed_turbulence * n_speed_filtered
        angle_wind[mask] = angles_ref[i] + angle_deviation * angle_turbulence * n_angle_filtered

    # Último tramo (por encima del último punto)
    mask_last = heights >= heights_ref[-1]
    n_speed = np.random.randn(np.count_nonzero(mask_last))
    n_angle = np.random.randn(np.count_nonzero(mask_last))

    n_speed_filtered = filtfilt(b, a, n_speed)
    n_angle_filtered = filtfilt(b, a, n_angle)

    n_speed_filtered /= np.std(n_speed_filtered)
    n_angle_filtered /= np.std(n_angle_filtered)

    wind[mask_last] = speeds_ref[-1] + speed_deviation * speed_turbulence * n_speed_filtered
    angle_wind[mask_last] = angles_ref[-1] + angle_deviation * angle_turbulence * n_angle_filtered

    # Componentes U y V (convención meteorológica)
    u = -wind * np.sin(np.radians(angle_wind))
    v = -wind * np.cos(np.radians(angle_wind))

    # Formato (altura, valor)
    wind_u = np.column_stack((heights, u))
    wind_v = np.column_stack((heights, v))

    # Crear entorno RocketPy
    env = Environment(
        latitude=lat,
        longitude=lon,
        elevation=elev
    )

    env.set_atmospheric_model("custom_atmosphere",
                              pressure=None,
                              temperature=None,
                              wind_u=wind_u,
                              wind_v=wind_v)

    return env

# ------ Funciones para gráficar
def extract_map_data(sim):
    latitudes = sim.latitude_array
    longitudes = sim.longitude_array

    return latitudes, longitudes


def extract_rb_ind(sim):
    rb1_normal_force = sim.rail_button1_normal_force.source[:,1]
    rb1_shear_force = sim.rail_button1_shear_force.source[:,1]
    rb2_normal_force = sim.rail_button2_normal_force.source[:,1]
    rb2_shear_force = sim.rail_button2_shear_force.source[:,1]

    t = sim.rail_button1_normal_force.source[:,0]

    return t, rb1_normal_force, rb1_shear_force, rb2_normal_force, rb2_shear_force