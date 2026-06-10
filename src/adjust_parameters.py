import numpy as np

def calculate_dry_motor_inertia(dry_mass, radius, height):
    """
    Compute the three principal moments of inertia of the dry motor casing
    modeled as a thin-walled hollow cylinder about its center of mass.

    The dry motor is assumed to be a thin shell where structural mass is
    concentrated at the outer radius. The transverse moments combine the
    hollow cylinder term with the slender rod contribution from the axial
    extent of the casing.

    Physical model:
        Ixx = 0.5 * dry_mass * radius² + (1/12) * dry_mass * height²
        Iyy = Ixx
        Izz = dry_mass * radius²

    :param dry_mass: Total dry mass of the motor excluding propellant, in kg.
    :param radius: Outer radius of the motor case in meters. Used as the
                representative structural radius under the thin-shell
                assumption.
    :param height: Total axial length of the motor case in meters.
    :return: numpy.ndarray of shape (3,) containing [Ixx, Iyy, Izz] in
            kg·m². Ixx and Iyy are the transverse moments of inertia.
            Izz is the axial spin moment of inertia.
    """
    
    Ixx = 0.5 * dry_mass * radius**2 + (1/12) * dry_mass * height**2
    Iyy = Ixx
    Izz = dry_mass * radius**2
    return np.array([Ixx, Iyy, Izz])

def calculate_nozzle_radius(chamber_radius):
    """
    Estimate the nozzle throat radius from the combustion chamber radius
    using a fixed contraction ratio of 0.85.

    This approximation corresponds to a throat-to-chamber area ratio of
    approximately 0.723 (0.85²), consistent with typical contraction ratios
    for solid motors in the high-power rocketry range.

    This function must only be called when the nozzle throat radius is not
    available from the motor datasheet or manufacturer specification. When
    a measured value exists, it must be set explicitly in the motor JSON
    configuration and this estimate must not be used.

    :param chamber_radius: Internal radius of the motor combustion chamber
                        (case bore radius) in meters.
    :return: Estimated nozzle throat radius in meters.
    """
    return 0.85 * chamber_radius

def eval_adjust_motor_parameters(motor_data):
    """
    Resolve all sentinel values in a motor parameter dictionary and return
    a fully populated parameter set ready for use in the RocketPy
    SolidMotor constructor.

    Parameters marked with -1 in the motor JSON configuration are computed
    from available geometric and mass data using physical models. Parameters
    with explicit values are used as-is. The sentinel value -1 must never
    represent a legitimate physical quantity — all motor parameters are
    strictly positive.

    Resolution is applied in fixed order. Some computed parameters depend
    on others resolved earlier in the same call: grain_initial_inner_radius
    depends on grain_outer_radius, which may itself have been resolved from
    case_radius in the same call. This order must not be changed.

    The following fallback assumptions are applied when sentinel values
    are encountered:

        dry_inertia                    -> computed via calculate_dry_motor_inertia
                                        using dry_mass, grain_outer_radius,
                                        and grain_initial_height.
        nozzle_radius                  -> estimated via calculate_nozzle_radius
                                        using case_radius.
        grain_outer_radius             -> set equal to case_radius.
        grain_initial_inner_radius     -> set to 50% of grain_outer_radius
                                        (neutral-burning approximation).
        grain_initial_height           -> set equal to case_length.
        grains_center_of_mass_position -> set to 50% of grain_initial_height
                                        (uniform density assumption).
        center_of_dry_mass_position    -> set to 50% of case_length
                                        (uniform casing mass assumption).

    This function mutates motor_data in place before returning it. If the
    original dictionary must be preserved, a deep copy should be made
    before calling this function.

    :param motor_data: Dictionary loaded from parameters/motors/
                    motors_parameters.json for a specific motor entry.
                    Must contain case_radius and case_length as explicit
                    values. All other parameters may be explicit or -1.
    :return: The resolved motor_data dictionary with all -1 sentinel values
            replaced by computed quantities. dry_inertia is returned as a
            list. All other parameters are returned as float.
    """
    
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