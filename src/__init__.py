# Core sims classes
from .sims import File_simulation

# --- Data extraction utilities ---
from .sims import (
    extract_initial_conditions_sim_data,
    extract_out_of_rail_sim_data,
    extract_burn_out_sim_data,
    extract_apogee_sim_data,
    extract_impact_sim_data,
    extract_maximum_values_sim_data,
    extract_usual_important_sim_data,
    compare_usual_important_data,
)

# --- Environment / wind model generators ---
from .sims import (
    generate_cte_wind_cte_angle,
    generate_cte_wind_cte_angle_per_height,
    generate_nsy_wind_cte_angle,
    generate_cte_wind_nsy_angle,
    generate_nsy_wind_nsy_angle,
    generate_variable_wind_profile,
)

# --- Plotting / post-processing helpers ---
from .sims import (
    extract_map_data,
    extract_rb_ind,
)

# --- Motor parameter adjustment utilities ---
from .adjust_parameters import (
    calculate_dry_motor_inertia,
    calculate_nozzle_radius,
    eval_adjust_motor_parameters,
)

__all__ = [
    # Core
    "File_simulation",

    # Extraction
    "extract_initial_conditions_sim_data",
    "extract_out_of_rail_sim_data",
    "extract_burn_out_sim_data",
    "extract_apogee_sim_data",
    "extract_impact_sim_data",
    "extract_maximum_values_sim_data",
    "extract_usual_important_sim_data",
    "compare_usual_important_data",

    # Wind models
    "generate_cte_wind_cte_angle",
    "generate_cte_wind_cte_angle_per_height",
    "generate_nsy_wind_cte_angle",
    "generate_cte_wind_nsy_angle",
    "generate_nsy_wind_nsy_angle",
    "generate_variable_wind_profile",

    # Plot helpers
    "extract_map_data",
    "extract_rb_ind",

    # Motor parameter adjustment
    "calculate_dry_motor_inertia",
    "calculate_nozzle_radius",
    "eval_adjust_motor_parameters",
]