# Objective
Someday I will update this

## csv_files
### Motors
- **AeroTech N2000W:** \
Thrust curve obtained from: https://www.thrustcurve.org/simfiles/5f4294d20002e90000000097/
*General motor info:*
    - Diameter: 0.098 m
    - Lenght: 1.046 m    
    - Propellant Weight: 7.756 kg
    - Dry Weight: 4.527 kg
    - Total Weight: 12.283 kg
    - Isp: 175 s

    *Thrust Curve Notes:* \
    Note that the Burn time specified in datasheet from thurst curve does not match the burn out time of the CSV, we are using the CSV file as it is.

    To match software requirements, an initial [0,0] was added at the begning of the CSV file.

    The first column of the file is the time in seconds [s], while the second is the thrust in newtons [N]

- **AeroTech N2220DM :** \
Thrust curve obtained from: https://www.thrustcurve.org/simfiles/5f4294d20002e900000007ed/
*General motor info:*
    - Diameter: 0.098 m
    - Lenght: 1.046 m
    - Propellant Weight: 7.183 kg
    - Dry Weight: 4.814 kg
    - Total Weight: 11.997 kg
    - Isp: N/D s

    *Thrust Curve Notes:* \
    Note that the Burn time specified in datasheet from thurst curve does not match the burn out time of the CSV, we are using the CSV file as it is. There is a really small discrepancy between values, nothing to worry about

    To match software requirements, an initial [0,0] was added at the begning of the CSV file.

    The first column of the file is the time in seconds [s], while the second is the thrust in newtons [N]

- **AeroTech N3300R :** \
Thrust curve obtained from: https://www.thrustcurve.org/simfiles/5f4294d20002e90000000884/
*General motor info:*
    - Diameter: 0.098 m
    - Lenght: 1.046 m
    - Propellant Weight: 7.512 kg
    - Dry Weight: 4.542 kg
    - Total Weight: 12.054 kg
    - Isp: N/D s

    *Thrust Curve Notes:* \
    Note that the Burn time specified in datasheet from thurst curve does not match the burn out time of the CSV, we are using the CSV file as it is. There is a really small discrepancy between values, nothing to worry about

    To match software requirements, an initial [0,0] was added at the begning of the CSV file.

    The first column of the file is the time in seconds [s], while the second is the thrust in newtons [N]

- **Volta Motor:** \
Thrust curve obtained from: Volta's Propulsion Team - Last Updated V:VOLTA_SRAD_motor1250final
*General motor info:*
    - Diameter: 0.098 m
    - Lenght: 1.046 m
    - Propellant Weight: 7.512 kg
    - Dry Weight: 4.542 kg
    - Total Weight: 12.054 kg
    - Isp: N/D s

    *Thrust Curve Notes:* \
    Note that the Burn time specified in datasheet from thurst curve does not match the burn out time of the CSV, we are using the CSV file as it is. There is a really small discrepancy between values, nothing to worry about

    To match software requirements, an initial [0,0] was added at the begning of the CSV file.

    The first column of the file is the time in seconds [s], while the second is the thrust in newtons [N]


# IMPORTANT NOTES
- Get the actual rocket inertias to change the sims
- Get the power_off_drag
- Get the actual position of R.B.
- By the moment, in IREC_VERSION1 for RPYm they were place in a radial position of 45°, a distance between them of 1m, and the position from the nose tip 1.9m
- Until an airfoil is not defined, al simulation will be made assuming a plate
- Parachuttes not updated with CDs


# Data from RPY
- Flight.x : Function
    Rocket's X coordinate (positive east) as a function of time.
- Flight.y : Function
    Rocket's Y coordinate (positive north) as a function of time.
- Flight.z : Function
    Rocket's z coordinate (positive up) as a function of time.
- Flight.vx : Function
    Velocity of the rocket's center of dry mass in the X (East) direction of
    the inertial frame as a function of time.
- Flight.vy : Function
    Velocity of the rocket's center of dry mass in the Y (North) direction of
    the inertial frame as a function of time.
- Flight.vz : Function
    Velocity of the rocket's center of dry mass in the Z (Up) direction of
    the inertial frame as a function of time.
- Flight.e0 : Function
    Rocket's Euler parameter 0 as a function of time.
- Flight.e1 : Function
    Rocket's Euler parameter 1 as a function of time.
- Flight.e2 : Function
    Rocket's Euler parameter 2 as a function of time.
- Flight.e3 : Function
    Rocket's Euler parameter 3 as a function of time.
- Flight.w1 : Function
    Angular velocity of the rocket in the x direction of the rocket's
    body frame as a function of time, in rad/s. Sometimes referred to as
    pitch rate (q).
- Flight.w2 : Function
    Angular velocity of the rocket in the y direction of the rocket's
    body frame as a function of time, in rad/s. Sometimes referred to as
    yaw rate (r).
- Flight.w3 : Function
    Angular velocity of the rocket in the z direction of the rocket's
    body frame as a function of time, in rad/s. Sometimes referred to as roll rate (p).
- Flight.latitude: Function
    Rocket's latitude coordinates (positive North) as a function of time. The Equator has a latitude equal to 0, by convention.
- Flight.longitude: Function
    Rocket's longitude coordinates (positive East) as a function of time.
    Greenwich meridian has a longitude equal to 0, by convention.
- Flight.wind_velocity_x : Function
        Wind velocity X (East) experienced by the rocket as a function of time.
- Flight.wind_velocity_y : Function
    Wind velocity Y (North) experienced by the rocket as a function of time.
- Flight.density : Function
    Air density experienced by the rocket as a function of time.
- Flight.pressure : Function
    Air pressure experienced by the rocket as a function of time.
- Flight.dynamic_viscosity : Function
    Air dynamic viscosity experienced by the rocket as a function of time.
- Flight.speed_of_sound : Function
    Speed of Sound in air experienced by the rocket as a function of time.
- Flight.ax : Function
    Acceleration of the rocket's center of dry mass along the X (East) axis in the inertial frame as a function of time.
- Flight.ay : Function
    Acceleration of the rocket's center of dry mass along the Y (North) axis in the inertial frame as a function of time.
- Flight.az : Function
    Acceleration of the rocket's center of dry mass along the Z (Up) axis in the inertial frame as a function of time.
- Flight.alpha1 : Function
    Angular acceleration of the rocket in the x direction of the rocket's body frame as a function of time, in rad/s. Sometimes referred to as
    yaw acceleration.
- Flight.alpha2 : Function
    Angular acceleration of the rocket in the y direction of the rocket's body frame as a function of time, in rad/s. Sometimes referred to as
    yaw acceleration.
- Flight.alpha3 : Function
    Angular acceleration of the rocket in the z direction of the rocket's body frame as a function of time, in rad/s. Sometimes referred to as
    roll acceleration.
- Flight.speed : Function
    Rocket velocity magnitude in m/s relative to ground as a function of time.
- Flight.horizontal_speed : Function
    Rocket's velocity magnitude in the horizontal (North-East) plane in m/s as a function of time.
- Flight.acceleration : Function
    Rocket acceleration magnitude in m/s² relative to ground as a function of time.
- Flight.attitude_vector_x : Function
    Rocket's attitude vector, or the vector that points in the rocket's axis of symmetry, component in the X direction (East) as a function of time.
- Flight.attitude_vector_y : Function
    Rocket's attitude vector, or the vector that points in the rocket's axis of symmetry, component in the Y direction (East) as a function of time.
- Flight.attitude_vector_z : Function
    Rocket's attitude vector, or the vector that points in the rocket's axis of symmetry, component in the Z direction (East) as a function of time.
- Flight.attitude_angle : Function
    Rocket's attitude angle, or the angle that the rocket's axis of symmetry makes with the horizontal (North-East) plane. Measured in degrees and expressed as a function
    of time.
- Flight.lateral_attitude_angle : Function
    Rocket's lateral attitude angle, or the angle that the rocket's axis of symmetry makes with plane defined by the launch rail direction and the Z (up) axis.Measured in degrees and expressed as a function
    of time.
- Flight.phi : Function
    Rocket's Spin Euler Angle, φ, according to the 3-2-3 rotation
    system nomenclature (NASA Standard Aerospace). Measured in degrees and
    expressed as a function of time.
- Flight.theta : Function
    Rocket's Nutation Euler Angle, θ, according to the 3-2-3 rotation
    system nomenclature (NASA Standard Aerospace). Measured in degrees and
    expressed as a function of time.
- Flight.psi : Function
    Rocket's Precession Euler Angle, ψ, according to the 3-2-3 rotation
    system nomenclature (NASA Standard Aerospace). Measured in degrees and
    expressed as a function of time.
- Flight.R1 : Function
    Aerodynamic force acting along the x-axis of the rocket's body frame
    as a function of time. Expressed in Newtons (N).
- Flight.R2 : Function
    Aerodynamic force acting along the y-axis of the rocket's body frame
    as a function of time. Expressed in Newtons (N).
- Flight.R3 : Function
    Aerodynamic force acting along the z-axis of the rocket's body frame
    as a function of time. Expressed in Newtons (N).
- Flight.M1 : Function
    Aerodynamic moment acting along the x-axis of the rocket's body
    frame as a function of time. Expressed in Newtons (N).
- Flight.M2 : Function
    Aerodynamic moment acting along the y-axis of the rocket's body
    frame as a function of time. Expressed in Newtons (N).
- Flight.M3 : Function
    Aerodynamic moment acting along the z-axis of the rocket's body
    frame as a function of time. Expressed in Newtons (N).
- Flight.net_thrust : Function
    Rocket's engine net thrust as a function of time in Newton.
    This is the actual thrust force experienced by the rocket.
    It may be corrected with the atmospheric pressure if a reference
    pressure is defined.
- Flight.aerodynamic_lift : Function
    Resultant force perpendicular to rockets axis due to
    aerodynamic effects as a function of time. Units in N.
    Expressed as a function of time. Can be called or accessed
    as array.
- Flight.aerodynamic_drag : Function
    Resultant force aligned with the rockets axis due to
    aerodynamic effects as a function of time. Units in N.
    Expressed as a function of time. Can be called or accessed
    as array.
- Flight.aerodynamic_bending_moment : Function
    Resultant moment perpendicular to rocket's axis due to
    aerodynamic effects as a function of time. Units in N m.
    Expressed as a function of time. Can be called or accessed
    as array.
- Flight.aerodynamic_spin_moment : Function
    Resultant moment aligned with the rockets axis due to
    aerodynamic effects as a function of time. Units in N m.
    Expressed as a function of time. Can be called or accessed
    as array.
- Flight.rail_button1_normal_force : Function
    Upper rail button normal force in N as a function
    of time.
- Flight.rail_button1_shear_force : Function
    Upper rail button shear force in N as a function
    of time.
- Flight.rail_button2_normal_force : Function
        Lower rail button normal force in N as a function
        of time.
- Flight.rail_button2_shear_force : Function
        Lower rail button shear force in N as a function
        of time.        
- Flight.rotational_energy : Function
    Rocket's rotational kinetic energy as a function of time.
    Units in J.
- Flight.translational_energy : Function
    Rocket's translational kinetic energy as a function of time.
    Units in J.
- Flight.kinetic_energy : Function
    Rocket's total kinetic energy as a function of time.
    Units in J.
- Flight.potential_energy : Function
    Rocket's gravitational potential energy as a function of
    time. Units in J.
- Flight.total_energy : Function
    Rocket's total mechanical energy as a function of time.
    Units in J.
- Flight.thrust_power : Function
    Rocket's engine thrust power output as a function
    of time in Watts.
- Flight.drag_power : Function
    Aerodynamic drag power output as a function
    of time in Watts.
- Flight.attitude_frequency_response : Function
    Fourier Frequency Analysis of the rocket's attitude angle.
    Expressed as the absolute value of the magnitude as a function
    of frequency in Hz.
- Flight.omega1_frequency_response : Function
    Fourier Frequency Analysis of the rocket's angular velocity omega 1.
    Expressed as the absolute value of the magnitude as a function
    of frequency in Hz.
- Flight.omega2_frequency_response : Function
    Fourier Frequency Analysis of the rocket's angular velocity omega 2.
    Expressed as the absolute value of the magnitude as a function
    of frequency in Hz.
- Flight.omega3_frequency_response : Function
    Fourier Frequency Analysis of the rocket's angular velocity omega 3.
    Expressed as the absolute value of the magnitude as a function
    of frequency in Hz.
- Flight.static_margin : Function
    Rocket's static margin during flight in calibers.
- Flight.stability_margin : Function
        Rocket's stability margin during flight, in calibers.
- Flight.stream_velocity_x : Function
    Freestream velocity x (East) component, in m/s, as a function of
    time.
- Flight.stream_velocity_y : Function
    Freestream velocity y (North) component, in m/s, as a function of
    time.
- Flight.stream_velocity_z : Function
    Freestream velocity z (up) component, in m/s, as a function of
    time.
- Flight.free_stream_speed : Function
    Freestream velocity magnitude, in m/s, as a function of time.
- Flight.apogee_freestream_speed : float
    Freestream speed of the rocket at apogee in m/s.
- Flight.mach_number : Function
    Rocket's Mach number defined as its freestream speed
    divided by the speed of sound at its altitude. Expressed
    as a function of time.
- Flight.reynolds_number : Function
        Rocket's Reynolds number, using its diameter as reference
        length and free_stream_speed as reference velocity. Expressed
        as a function of time.
- Flight.dynamic_pressure : Function
        Dynamic pressure experienced by the rocket in Pa as a function
        of time, defined by 0.5*rho*V^2, where rho is air density and V
        is the freestream speed.
- Flight.total_pressure : Function
        Total pressure experienced by the rocket in Pa as a function
        of time.
-Flight.angle_of_attack : Function
        Rocket's angle of attack in degrees as a function of time.
        Defined as the minimum angle between the attitude vector and
        the freestream velocity vector. Can be called or accessed as
        array.    