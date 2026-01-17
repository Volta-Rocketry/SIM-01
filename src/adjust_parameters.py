import numpy as np

def calculate_dry_motor_inertia(dry_mass, radius, height):
    
    Ixx = 0.5 * dry_mass * radius**2 + (1/12) * dry_mass * height**2
    Iyy = Ixx
    Izz = dry_mass * radius**2
    return np.array([Ixx, Iyy, Izz])

def calculate_nozzle_radius(chamber_radius):
    return 0.85 * chamber_radius

def eval_adjust_motor_parameters(motor_data):
    if motor_data["dry_inertia"] == -1:
        motor_data["dry_inertia"] = motor_data["dry_inertia"] = calculate_dry_motor_inertia(motor_data["dry_mass"], motor_data["grain_outer_radius"], motor_data["grain_initial_height"]).tolist()
    else:
        motor_data["dry_inertia"] = tuple(motor_data["dry_inertia"])

    if motor_data["nozzle_radius"] == -1:
        motor_data["nozzle_radius"] = calculate_nozzle_radius(motor_data["case_radius"])
    else:
        motor_data["nozzle_radius"] = motor_data["nozzle_radius"]

    if motor_data["grain_outer_radius"] == -1:
        motor_data["grain_outer_radius"] = motor_data["case_radius"]
    else:
        motor_data["grain_outer_radius"] = motor_data["grain_outer_radius"]

    if motor_data["grain_initial_inner_radius"] == -1:
        motor_data["grain_initial_inner_radius"] = 0.5 * motor_data["grain_outer_radius"]
    else:
        motor_data["grain_initial_inner_radius"] = motor_data["grain_initial_inner_radius"]

    if motor_data["grain_initial_height"] == -1:
        motor_data["grain_initial_height"] = motor_data["case_length"]
    else:
        motor_data["grain_initial_height"] = motor_data["grain_initial_height"]

    if motor_data["grains_center_of_mass_position"] == -1:
        motor_data["grains_center_of_mass_position"] = 0.5 * motor_data["grain_initial_height"]
    else:
        motor_data["grains_center_of_mass_position"] = motor_data["grains_center_of_mass_position"]

    if motor_data["center_of_dry_mass_position"] == -1:
        motor_data["center_of_dry_mass_position"] = 0.5 * motor_data["case_length"]
    else:
        motor_data["center_of_dry_mass_position"] = motor_data["center_of_dry_mass_position"]

    return motor_data