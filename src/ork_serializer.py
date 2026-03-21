"""
ork_serializer.py
=================
Tool to automatically extract rocket parameters from an OpenRocket
file (.ork) using the rocketserializer library.

Generates two output files:
    - parameters_<rocket_name>.json  ->  Rocket parameters
    - drag_<rocket_name>.csv         ->  Rocket drag curve

Authors: Electronics / Simulation subsystem
Team   : VOLTA

---------------------------------------------
PREREQUISITES (read completely before running)
---------------------------------------------

STEP 1 - Install Java 17
rocketserializer needs Java to open the .ork file through the
OpenRocket JAR. Without Java, nothing works.

Download Java 17 here:
    https://www.oracle.com/java/technologies/downloads/

IMPORTANT on Windows:
- During installation, check the option "Set JAVA_HOME variable"
    or "Add to PATH". This is key so the terminal can find Java.
- After installing, CLOSE and REOPEN the terminal.
- Verify it works by running in the terminal:
        java -version
    You should see something like: "java version 17.x.x ..."
    If you see an error, Java is not in the PATH -> restart the computer.

STEP 2 - Download the OpenRocket 23.09 JAR
The JAR is the packaged OpenRocket program. rocketserializer uses it
internally to read the .ork file.

Download it here (version 23.09, .jar file):
    https://openrocket.info/downloads.html?vers=23.09#content-JAR

IMPORTANT:
- The file is called "OpenRocket-23.09.jar".
- Save it in the same folder as this script (recommended), or note
    the exact path where you saved it to use it later.
- Do NOT use the OpenRocket .exe installer -- you must download the .jar.

STEP 3 - Install rocketserializer
With Java already installed and the terminal open, run:

    pip install rocketserializer

This installs rocketserializer and all its dependencies automatically
(including: numpy, rocketpy, lxml, bs4, orhelper, click, pyyaml).

Verify the installation by running:
    ork2json --help
If you see the command options, everything is fine.
If you see "command not recognized", try closing and reopening the terminal.

STEP 4 - Prepare the .ork file
Your .ork file must meet these conditions to work:
- Must be saved in ENGLISH in OpenRocket
    (File -> Preferences -> Language -> English, then save again).
- Must have AT LEAST ONE simulation run and saved inside OpenRocket
    (required to generate the drag CSV).
- Only single-stage rockets with a single motor are supported.
- Only a single nose cone is supported.
If your .ork does not meet these conditions, rocketserializer will fail.

---------------------------------------------
RECOMMENDED FOLDER STRUCTURE
---------------------------------------------
To keep the project organized, this structure is recommended.
The JAR and the .ork must be accessible from the project folder:

    rocket_project/
    |
    +-- OpenRocket-23.09.jar    <- JAR goes here (same folder as the script)
    |
    +-- ork_files/              <- Save .ork files here
    |   +-- MyRocket_v1.ork
    |
    +-- parameters/
    |   +-- rocket/             <- Generated JSON and CSV files go here
    |
    +-- ork_serializer.py       <- This file
    +-- usage_examples.py       <- Examples of how to use this code

If you place the JAR in the same folder as ork_serializer.py, the code
will find it automatically without needing to specify the path.

---------------------------------------------
QUICK USAGE EXAMPLE
---------------------------------------------
From the terminal, in the project folder:

    python ork_serializer.py

The code will ask for the required information, or you can call the
functions directly from another script:

    from ork_serializer import run_serialization

    run_serialization(
        ork_path    = "ork_files/MyRocket_v1.ork",
        jar_path    = "OpenRocket-23.09.jar",
        output_path = "parameters/rocket/"
    )

See usage_examples.py for more detailed examples.
"""

import os              # For working with file and folder paths on the operating system
import sys             # For stopping the program with sys.exit() when critical errors occur
import glob            # For searching files using patterns (e.g., find all *.ork files)
import subprocess      # For running terminal commands from Python (ork2json, ork2csv)
import importlib.util  # For checking if a Python library is installed without importing it
from pathlib import Path  # For working with file paths in an object-oriented way
import json               # For reading and writing JSON files
# =============================================================================
# BLOCK 1: Verify that rocketserializer is installed
# =============================================================================

def verify_installation():
    """
    Verifies that rocketserializer, Java, and the ork2json command are
    available and working correctly on the system.

    This function performs three checks in order:
    1. That the Python library 'rocketserializer' is installed.
    2. That Java is installed and accessible from the terminal.
    3. That the 'ork2json' command (installed by rocketserializer) works.

    If any check fails, the program stops and shows exactly what to do
    to fix the problem.

    Why check all of this?
    rocketserializer is not just a Python library: internally it uses Java
    to open the .ork file through the OpenRocket JAR. If Java is not
    installed or not in the PATH, rocketserializer will fail even if it
    is correctly installed with pip.

    Returns
    -------
    bool
        True if everything is installed and working correctly.

    Raises
    ------
    SystemExit
        If any check fails. The program stops with a clear message
        indicating what to install and how to do it.

    Example
    -------
    >>> verify_installation()
    ============================================================
    BLOCK 1: Verifying installation...
    ============================================================
    [OK] rocketserializer is installed.
    [OK] Java found: java version "17.0.x"
    [OK] ork2json command available.
    True
    """
    print("\n" + "="*60)
    print("BLOCK 1: Verifying installation...")
    print("="*60)

    # ── Check 1: Is the rocketserializer library installed? ──────────────────
    spec = importlib.util.find_spec("rocketserializer")

    if spec is None:
        print("\n[ERROR] rocketserializer is NOT installed.")
        print()
        print("  Follow these steps in order:")
        print()
        print("  STEP 1 - Install Java 17 (if you haven't already):")
        print("    https://www.oracle.com/java/technologies/downloads/")
        print("    -> On Windows: during installation, check the option")
        print("       'Set JAVA_HOME variable' or 'Add to PATH'.")
        print("    -> After installing, CLOSE and REOPEN the terminal.")
        print("    -> Verify with:  java -version")
        print()
        print("  STEP 2 - Download the OpenRocket 23.09 JAR:")
        print("    https://openrocket.info/downloads.html?vers=23.09#content-JAR")
        print("    -> Download the .jar file (NOT the .exe installer).")
        print("    -> Save it in the same folder as this script.")
        print()
        print("  STEP 3 - Install rocketserializer:")
        print("    pip install rocketserializer")
        print()
        print("  STEP 4 - Prepare your .ork file:")
        print("    -> Must be saved in ENGLISH in OpenRocket.")
        print("       (File -> Preferences -> Language -> English -> save .ork)")
        print("    -> Must have at least 1 simulation run and saved.")
        print("    -> Only supports: 1 stage, 1 motor, 1 nose cone.")
        print()
        print("  After completing all steps, run this script again.")
        sys.exit(1)

    print("  [OK] rocketserializer is installed.")

    # ── Check 2: Is Java installed and in the PATH? ───────────────────────────
    try:
        java_result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True
        )
        # java -version prints to stderr (standard Java behavior)
        version_info = java_result.stderr or java_result.stdout
        first_line = version_info.splitlines()[0] if version_info else "unknown version"
        print(f"  [OK] Java found: {first_line}")

    except FileNotFoundError:
        print("\n[ERROR] Java is NOT installed or is not in the system PATH.")
        print()
        print("  Java is required for rocketserializer to read the .ork file")
        print("  through the OpenRocket JAR.")
        print()
        print("  How to fix it:")
        print("    1. Download and install Java 17:")
        print("       https://www.oracle.com/java/technologies/downloads/")
        print("    2. On Windows: during installation, check the option")
        print("       'Set JAVA_HOME variable' or 'Add to PATH'.")
        print("    3. CLOSE and REOPEN the terminal (important).")
        print("    4. If it still fails, RESTART the computer.")
        print("    5. Verify with:  java -version")
        print()
        print("  If you already installed Java and it still does not work:")
        print("    -> Search in Windows: 'Edit the system environment variables'")
        print("    -> Under 'System variables', verify that PATH includes")
        print("       the Java bin folder, something like:")
        print("       C:\\Program Files\\Java\\jdk-17\\bin")
        sys.exit(1)

    # ── Check 3: Is the ork2json command available? ───────────────────────────
    # ork2json is the CLI command installed by rocketserializer. If it is not
    # available, the installation may be incomplete or pip scripts may not
    # be in the PATH.
    try:
        cmd_result = subprocess.run(
            ["ork2json", "--help"],
            capture_output=True,
            text=True
        )
        if cmd_result.returncode == 0:
            print("  [OK] ork2json command available.")
        else:
            raise FileNotFoundError

    except FileNotFoundError:
        print("\n[WARNING] The 'ork2json' command was not found in the PATH.")
        print()
        print("  rocketserializer is installed but its CLI commands are not")
        print("  accessible from the terminal. This sometimes happens on")
        print("  Windows when pip scripts are not in the PATH.")
        print()
        print("  How to fix it:")
        print("    Option A (easiest): close and reopen the terminal.")
        print("    Option B: reinstall rocketserializer:")
        print("      pip install --force-reinstall rocketserializer")
        print("    Option C: if you are using a virtual environment (venv/conda),")
        print("      make sure it is activated before running this script.")
        print()
        print("  The program will continue, but may fail in Block 3.")
        # No sys.exit() here because the command might still work on some systems.

    return True


# =============================================================================
# BLOCK 2: Verify that the .ork file exists and find its path
# =============================================================================

def search_ork_in_project(search_folder="."):
    """
    Searches for .ork files inside a project folder.

    This helper function is useful when the exact location of the .ork
    file is not known. It searches recursively in the given folder and
    all its subfolders.

    Parameters
    ----------
    search_folder : str, optional
        Folder to search in. Default is the current folder (".").
        The recommended folder following the team structure is "ork_files/".

    Returns
    -------
    list of str
        List with the paths of all .ork files found.
        May be empty if none were found.

    Example
    -------
    >>> files = search_ork_in_project("ork_files/")
    >>> print(files)
    ['ork_files/MyRocket_v1.ork', 'ork_files/MyRocket_v2.ork']
    """
    pattern = os.path.join(search_folder, "**", "*.ork")
    found_files = glob.glob(pattern, recursive=True)
    return found_files


def verify_ork_file(ork_path=None, search_folder="."):
    """
    Verifies that the .ork file exists and returns its absolute path.

    There are two ways to use this function:
    1. Providing the exact file path (recommended if you already know it).
    2. Letting the code search automatically in a folder.

    If more than one .ork file is found, the code asks the user which
    one to use.

    Parameters
    ----------
    ork_path : str or None, optional
        Path to the .ork file. Can be relative or absolute.
        Example: "ork_files/MyRocket_v1.ork"
        If None, the code will search automatically in `search_folder`.

    search_folder : str, optional
        Folder to search in if `ork_path` was not provided.
        Default is the current folder (".").
        Example: "ork_files/"

    Returns
    -------
    str
        Absolute path to the verified .ork file, ready to use.

    Raises
    ------
    SystemExit
        If no .ork file is found or if the user cancels the operation.

    Example
    -------
    >>> # Option 1: providing the path directly
    >>> path = verify_ork_file(ork_path="ork_files/MyRocket_v1.ork")

    >>> # Option 2: letting the code search automatically
    >>> path = verify_ork_file(search_folder="ork_files/")
    """
    print("\n" + "="*60)
    print("BLOCK 2: Searching and verifying the .ork file...")
    print("="*60)

    # --- Case 1: The user provided the path directly ---
    if ork_path is not None:
        print(f"  Path provided: {ork_path}")

        if not os.path.exists(ork_path):
            print(f"\n[ERROR] File not found at: {ork_path}")
            print()
            print("  Possible causes:")
            print("  - The path is misspelled (check uppercase/lowercase).")
            print("  - The file is in a different folder.")
            print("  - The file does not exist yet.")
            print()
            print("  TIP: Use forward slashes '/' in the path, not '\\'.")
            print("  Correct example: 'ork_files/MyRocket_v1.ork'")
            sys.exit(1)

        if not ork_path.lower().endswith(".ork"):
            print(f"\n[WARNING] The file '{ork_path}' does not have a .ork extension.")
            print("  Make sure it is a valid OpenRocket file.")
            print("  Continuing anyway...")

        absolute_path = os.path.abspath(ork_path)
        print(f"[OK] File found: {absolute_path}")
        return absolute_path

    # --- Case 2: Search automatically in a folder ---
    print(f"  No path provided. Searching for .ork files in: '{search_folder}'")
    files = search_ork_in_project(search_folder)

    if len(files) == 0:
        print(f"\n[ERROR] No .ork file was found in '{search_folder}'")
        print()
        print("  Possible causes:")
        print("  - The .ork file is not in the project folder yet.")
        print("  - You are searching in the wrong folder.")
        print()
        print("  TIP: Save your .ork file in the 'ork_files/' folder")
        print("  inside the project, or provide the exact path like this:")
        print()
        print("      verify_ork_file(ork_path='path/to/your/rocket.ork')")
        sys.exit(1)

    if len(files) == 1:
        absolute_path = os.path.abspath(files[0])
        print(f"[OK] File found automatically: {absolute_path}")
        return absolute_path

    # --- More than one file found: ask the user ---
    print(f"\n  Found {len(files)} .ork files:")
    print()
    for i, file in enumerate(files):
        print(f"    [{i + 1}] {file}")
    print()

    while True:
        try:
            selection = input(
                f"  Which one do you want to use? Enter the number (1-{len(files)}): "
            ).strip()
            index = int(selection) - 1
            if 0 <= index < len(files):
                absolute_path = os.path.abspath(files[index])
                print(f"\n[OK] File selected: {absolute_path}")
                return absolute_path
            else:
                print(f"  [WARNING] Number out of range. Enter a number between 1 and {len(files)}.")
        except ValueError:
            print("  [WARNING] That is not a valid number. Try again.")
        except KeyboardInterrupt:
            print("\n\n  Operation cancelled by user.")
            sys.exit(0)


# =============================================================================
# BLOCK 3: Run rocketserializer and generate JSON and CSV
# =============================================================================

def _verify_java():
    """
    Verifies that Java is installed and accessible from the terminal.

    rocketserializer needs Java to read the .ork file through the
    OpenRocket JAR.

    Returns
    -------
    bool
        True if Java is available.

    Raises
    ------
    SystemExit
        If Java is not installed or cannot be accessed from the terminal.
    """
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True
        )
        # java -version prints to stderr, not stdout
        version_info = result.stderr or result.stdout
        print(f"  [OK] Java found: {version_info.splitlines()[0]}")
        return True
    except FileNotFoundError:
        print("\n[ERROR] Java is not installed or is not in the system PATH.")
        print()
        print("  To install Java 17:")
        print("    https://www.oracle.com/java/technologies/downloads/")
        print()
        print("  After installing, close and reopen the terminal,")
        print("  then run this script again.")
        sys.exit(1)


def _verify_jar(jar_path):
    """
    Verifies that the OpenRocket JAR file exists at the given path.

    The JAR is the OpenRocket file that rocketserializer uses internally
    to read the .ork file. It must be downloaded manually.

    Parameters
    ----------
    jar_path : str
        Path to the OpenRocket .jar file.
        Example: "OpenRocket-23.09.jar"

    Returns
    -------
    str
        Absolute path to the verified JAR.

    Raises
    ------
    SystemExit
        If the JAR does not exist at the given path.
    """
    if not os.path.exists(jar_path):
        print(f"\n[ERROR] JAR file not found at: {jar_path}")
        print()
        print("  The OpenRocket JAR file is required for rocketserializer")
        print("  to read the .ork file.")
        print()
        print("  Download it here (version 23.09):")
        print("    https://openrocket.info/downloads.html?vers=23.09#content-JAR")
        print()
        print("  Then save it in the project folder and specify its path:")
        print("      jar_path='OpenRocket-23.09.jar'")
        sys.exit(1)

    absolute_path = os.path.abspath(jar_path)
    print(f"  [OK] OpenRocket JAR found: {absolute_path}")
    return absolute_path


def run_serialization(ork_path, jar_path, output_path="parameters/rocket/", verbose=False):
    """
    Runs rocketserializer on the .ork file and generates the parameter
    file (JSON) and the drag file (CSV).

    This is the core block of the process. It calls the two CLI commands
    installed by rocketserializer:
    - ork2json: generates the rocket parameter file in JSON format.
    - ork2csv:  generates the rocket drag curve in CSV format.

    The generated files are saved in `output_path` with names based on
    the original .ork file name.

    Parameters
    ----------
    ork_path : str
        Path to the rocket .ork file. Can be relative or absolute.
        Example: "ork_files/MyRocket_v1.ork"

    jar_path : str
        Path to the OpenRocket JAR file (version 23.09).
        Example: "OpenRocket-23.09.jar"
        Download at: https://openrocket.info/downloads.html?vers=23.09#content-JAR

    output_path : str, optional
        Folder where the generated files will be saved.
        Default: "parameters/rocket/"
        Created automatically if it does not exist.

    verbose : bool, optional
        If True, shows detailed progress from the serializer.
        Default: False (silent mode).

    Returns
    -------
    dict
        Dictionary with the paths of the generated files:
        {
            "json": "path/to/parameters_MyRocket_v1.json",
            "csv":  "path/to/drag_MyRocket_v1.csv"
        }

    Raises
    ------
    SystemExit
        If Java is not installed, the JAR does not exist, or if
        rocketserializer fails during execution.

    Example
    -------
    >>> results = run_serialization(
    ...     ork_path    = "ork_files/MyRocket_v1.ork",
    ...     jar_path    = "OpenRocket-23.09.jar",
    ...     output_path = "parameters/rocket/",
    ...     verbose     = False
    ... )
    >>> print(results["json"])
    'parameters/rocket/parameters_MyRocket_v1.json'
    >>> print(results["csv"])
    'parameters/rocket/drag_MyRocket_v1.csv'

    Notes
    -----
    - rocketserializer may take between 10 and 60 seconds depending on
    the size of the rocket and the speed of the computer. This is normal.
    - If the rocket has unsupported features (e.g., complex custom fins),
    rocketserializer may fail. In that case, check the rocketserializer
    documentation at: https://github.com/RocketPy-Team/RocketSerializer
    """
    print("\n" + "="*60)
    print("BLOCK 3: Running rocketserializer...")
    print("="*60)

    # Verify Java
    print("\n  Verifying Java...")
    _verify_java()

    # Verify JAR
    print("\n  Verifying OpenRocket JAR file...")
    jar_abs = _verify_jar(jar_path)

    # Create output folder if it does not exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        print(f"\n  [INFO] Output folder created: {output_path}")
    else:
        print(f"\n  [OK] Output folder exists: {output_path}")

    ork_abs     = os.path.abspath(ork_path)
    output_abs  = os.path.abspath(output_path)

    verbose_flag = "True" if verbose else "False"

    # -------------------------------------------------------------------------
    # Step 3.1: Run ork2json — generates both the parameter JSON and drag CSV
    # -------------------------------------------------------------------------
    # ork2json generates two output files in a single run:
    #   - parameters.json  -> rocket parameters
    #   - drag_curve.csv   -> drag curve data
    print(f"\n  Running ork2json (generates JSON and CSV in one step)...")
    print(f"    .ork file    : {ork_abs}")
    print(f"    Output folder: {output_abs}")
    print(f"    (This may take between 10 and 60 seconds, please wait...)")

    json_command = [
        "ork2json",
        "--filepath", ork_abs,
        "--output",   output_abs,
        "--ork_jar",  jar_abs,
        "--verbose",  verbose_flag
    ]

    try:
        json_result = subprocess.run(
            json_command,
            capture_output=True,
            text=True
        )

        if json_result.returncode != 0:
            print("\n[ERROR] ork2json failed during execution.")
            print()
            print("  Error message:")
            print(f"  {json_result.stderr}")
            print()
            print("  Possible causes:")
            print("  - The .ork file has components not supported by rocketserializer.")
            print("  - The JAR version does not match the .ork version.")
            print("  - The .ork file is corrupted or incomplete.")
            print("  - The .ork file is not saved in English.")
            print("    -> In OpenRocket: File -> Preferences -> Language -> English")
            print("       Then save the .ork and run this script again.")
            print("  - The rocket has more than one stage or more than one motor.")
            print("    -> rocketserializer only supports single-stage rockets")
            print("       with a single motor.")
            print()
            print("  Check the rocketserializer documentation at:")
            print("  https://github.com/RocketPy-Team/RocketSerializer")
            sys.exit(1)

        if verbose:
            print(json_result.stdout)

        print(f"  [OK] JSON and CSV generated successfully.")

    except FileNotFoundError:
        print("\n[ERROR] The 'ork2json' command was not found.")
        print()
        print("  This means rocketserializer is not installed correctly")
        print("  or the installation did not complete properly.")
        print()
        print("  Try reinstalling it:")
        print("      pip install --force-reinstall rocketserializer")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # Build the paths of the generated files
    # -------------------------------------------------------------------------
    # rocketserializer always generates files with these fixed names,
    # regardless of the .ork file name.
    json_path = os.path.join(output_abs, "parameters.json")
    csv_path  = os.path.join(output_abs, "drag_curve.csv")

    # Verify that the files were actually generated
    generated_files = {}

    if os.path.exists(json_path):
        generated_files["json"] = json_path
        print(f"\n  JSON file: {json_path}")
    else:
        print(f"\n[WARNING] Expected JSON not found at: {json_path}")
        print("  Check the output folder manually.")
        # Search for any JSON generated in the output folder
        found_jsons = glob.glob(os.path.join(output_abs, "*.json"))
        if found_jsons:
            generated_files["json"] = found_jsons[0]
            print(f"  Alternative JSON found: {found_jsons[0]}")

    if os.path.exists(csv_path):
        generated_files["csv"] = csv_path
        print(f"  CSV file : {csv_path}")
    else:
        print(f"\n[WARNING] Expected CSV not found at: {csv_path}")
        print("  Check the output folder manually.")
        found_csvs = glob.glob(os.path.join(output_abs, "*.csv"))
        if found_csvs:
            generated_files["csv"] = found_csvs[0]
            print(f"  Alternative CSV found: {found_csvs[0]}")

    return generated_files

# =============================================================================
# BLOCK 4: Rename, standardize, validate and register the generated files
# =============================================================================

def rename_files(ork_file):
    """
    Rename the generated JSON and drag CSV files based on the .ork file name.

    This function takes the name of an OpenRocket (.ork) file and renames the
    generated 'parameters.json' and 'drag_curve.csv' files accordingly. It also
    ensures that no existing files are overwritten by appending a counter if needed.
    Additionally, it removes any existing thrust source file.

    Parameters
    ----------
    ork_file : str or Path
        Path to the .ork file used as reference for naming.

    Returns
    -------
    tuple(Path, Path)
        Paths to the renamed JSON and CSV files.

    Example
    -------
    >>> json_file, csv_file = rename_files("ork_files/AURORA_v02.ork")
    >>> print(json_file)
    PosixPath('parameters/rocket/AURORA_v02_OPR.json')
    """
    ork_file = Path(ork_file)

    json_base = ork_file.stem + "_OPR"
    csv_base  = "drag_curve_" + ork_file.stem

    json_original = Path("parameters/rocket/parameters.json")
    csv_original  = Path("parameters/rocket/drag_curve.csv")
    thrust_file   = Path("parameters/rocket/thrust_source.csv")

    # Remove the thrust source file if it exists (not needed)
    if thrust_file.exists():
        thrust_file.unlink()

    def get_unique_name(path, name, suffix):
        # If a file with that name already exists, append a counter
        new_path = path.with_name(name + suffix)
        counter = 1
        while new_path.exists():
            new_path = path.with_name(f"{name}({counter}){suffix}")
            counter += 1
        return new_path

    json_new = get_unique_name(json_original, json_base, ".json")
    csv_new  = get_unique_name(csv_original, csv_base, ".csv")

    json_original.rename(json_new)
    if csv_original.exists():
        csv_original.rename(csv_new)

    return json_new, csv_new


def verify_file(path):
    """
    Verify that a file exists at the specified path.

    Parameters
    ----------
    path : Path
        Path to the file to be checked.

    Returns
    -------
    bool
        True if the file exists, False otherwise.

    Example
    -------
    >>> verify_file(Path("parameters/rocket/AURORA_v02_OPR.json"))
    True
    """
    return path.exists()


def standardize_file(route):
    """
    Standardize the structure of a RocketPy JSON file.

    This function reformats the JSON file generated by the serializer to match
    a predefined structure. It renames keys, removes unnecessary fields, and
    restructures nested data such as fins and parachutes.

    Parameters
    ----------
    route : Path
        Path to the JSON file to be standardized.

    Returns
    -------
    dict
        The modified data dictionary after standardization.

    Example
    -------
    >>> data = standardize_file(Path("parameters/rocket/AURORA_v02_OPR.json"))
    >>> print(list(data.keys()))
    ['fins', 'nosecone', 'airframe', 'parachutes', ...]
    """
    with open(route, "r") as f:
        data = json.load(f)

    # FINS: normalize fin key name (e.g. "trapezoidalfins" -> "fins")
    for key in list(data.keys()):
        if key.endswith("fins"):
            data["fins"] = data.pop(key, None)

    # If fins are stored under a "0" key, unwrap them
    if "fins" in data and "0" in data["fins"]:
        data["fins"] = data["fins"]["0"]

    # PARACHUTES: rename first parachute entry to "main"
    if "parachutes" in data:
        parachutes = data["parachutes"]
        for key in list(parachutes.keys()):
            parachutes["main"] = parachutes.pop(key)
            break

    # Remove fields not used by the simulation code
    data.pop("motors", None)
    data["nosecone"]  = data.pop("nosecones", None)
    data["airframe"]  = data.pop("rocket", None)
    data.pop("id", None)
    data.pop("stored_results", None)
    data.pop("flight", None)
    data.pop("environment", None)
    data.pop("tails", None)

    with open(route, "w") as f:
        json.dump(data, f, indent=4)

    return data


def verify_format(data):
    """
    Validate that the JSON data meets the minimum required format.

    This function checks whether essential keys are present and contain
    valid (non-None) data. These keys are required by the simulation
    code in src/.

    Parameters
    ----------
    data : dict
        Dictionary containing the JSON data.

    Returns
    -------
    bool
        True if the data meets the required format, False otherwise.

    Example
    -------
    >>> verify_format({"fins": {...}, "nosecone": {...}, "airframe": {...}, "parachutes": {...}})
    True
    """
    required_keys = ["fins", "nosecone", "airframe", "parachutes"]
    return all(key in data and data[key] is not None for key in required_keys)


def update_supported_list(json_path):
    """
    Update the list of supported rocket configurations.

    This function adds the name of the processed JSON file to a text file
    (parameters/supported.txt) containing all registered configurations,
    avoiding duplicates.

    Parameters
    ----------
    json_path : Path
        Path to the JSON file to be recorded.

    Returns
    -------
    None

    Example
    -------
    >>> update_supported_list(Path("parameters/rocket/AURORA_v02_OPR.json"))
    # Adds "AURORA_v02_OPR.json" to parameters/supported.txt
    """
    txt_path = Path("parameters/supported.txt")
    name = json_path.name

    if txt_path.exists():
        with open(txt_path, "r") as f:
            lines = f.read().splitlines()
    else:
        lines = []

    if name not in lines:
        lines.append(name)

    with open(txt_path, "w") as f:
        for line in lines:
            f.write(line + "\n")

# =============================================================================
# MAIN FUNCTION: Runs the complete workflow
# =============================================================================

def run_full_workflow(ork_path=None, jar_path=None,
                    output_path="parameters/rocket/",
                    search_folder=".", verbose=False):
    """
    Runs the complete workflow: verification, file search, and serialization.
    This is the main function that coordinates the 3 blocks.

    Follows the workflow defined in the team diagram:
        Block 1 -> Block 2 -> Block 3

    Parameters
    ----------
    ork_path : str or None, optional
        Path to the .ork file. If None, the code searches automatically
        in `search_folder`.
        Example: "ork_files/MyRocket_v1.ork"

    jar_path : str or None, optional
        Path to the OpenRocket JAR file. If None, the code searches
        for the JAR automatically in the current folder.
        Example: "OpenRocket-23.09.jar"

    output_path : str, optional
        Folder where the generated JSON and CSV files will be saved.
        Default: "parameters/rocket/"

    search_folder : str, optional
        Folder to search for the .ork if `ork_path` was not provided.
        Default: "." (current folder).
        Recommended: "ork_files/"

    verbose : bool, optional
        If True, shows detailed progress from the serializer.
        Default: False.

    Returns
    -------
    dict
        Dictionary with the paths of the generated files:
        {
            "json": "path/to/parameters_MyRocket.json",
            "csv":  "path/to/drag_MyRocket.csv"
        }

    Example
    -------
    >>> # Simplest usage (the code finds the .ork automatically)
    >>> results = run_full_workflow(
    ...     jar_path="OpenRocket-23.09.jar"
    ... )

    >>> # Usage with exact .ork path
    >>> results = run_full_workflow(
    ...     ork_path    = "ork_files/AURORA_v02.ork",
    ...     jar_path    = "OpenRocket-23.09.jar",
    ...     output_path = "parameters/rocket/"
    ... )
    """
    
    print("\n" + "="*60)
    print("  ROCKET SERIALIZER - Complete workflow")
    print("="*60)
    print("\n  This script converts your OpenRocket .ork file into")
    print("  JSON and CSV files ready to use in the simulations.")
    print()

    # ── Block 1: Verify installation ─────────────────────────────────────────
    verify_installation()

    # ── Block 2: Verify and find the .ork file ───────────────────────────────
    verified_ork = verify_ork_file(
        ork_path=ork_path,
        search_folder=search_folder
    )

    # If no JAR was provided, search for one in the current folder
    if jar_path is None:
        found_jars = glob.glob("*.jar")
        if len(found_jars) == 1:
            jar_path = found_jars[0]
            print(f"\n  [INFO] JAR found automatically: {jar_path}")
        elif len(found_jars) > 1:
            print(f"\n  [WARNING] Multiple .jar files found:")
            for i, jar in enumerate(found_jars):
                print(f"    [{i+1}] {jar}")
            print()
            while True:
                try:
                    sel = input(f"  Which one is the OpenRocket JAR? (1-{len(found_jars)}): ").strip()
                    idx = int(sel) - 1
                    if 0 <= idx < len(found_jars):
                        jar_path = found_jars[idx]
                        break
                    else:
                        print("  Number out of range.")
                except ValueError:
                    print("  Enter a valid number.")
        else:
            print("\n[ERROR] OpenRocket JAR file not found.")
            print()
            print("  Download it here (version 23.09):")
            print("    https://openrocket.info/downloads.html?vers=23.09#content-JAR")
            print()
            print("  Then specify it when calling the function:")
            print("      run_full_workflow(jar_path='OpenRocket-23.09.jar')")
            sys.exit(1)

    # ── Block 3: Run serialization ────────────────────────────────────────────
    files = run_serialization(
        ork_path=verified_ork,
        jar_path=jar_path,
        output_path=output_path,
        verbose=verbose
    )

    # ── Block 4: Rename, standardize, validate and register ──────────────────
    print("\n" + "="*60)
    print("BLOCK 4: Processing generated files...")
    print("="*60)

    # Rename files based on the .ork name
    json_file, csv_file = rename_files(verified_ork)
    print(f"\n  [OK] Files renamed:")
    print(f"    JSON : {json_file}")
    print(f"    CSV  : {csv_file}")

    # Verify the renamed JSON exists
    if not verify_file(json_file):
        raise ValueError("The JSON was not saved correctly")

    # Standardize the JSON structure
    data = standardize_file(json_file)
    print(f"\n  [OK] JSON standardized.")

    # Validate minimum required format
    if not verify_format(data):
        raise ValueError("The file does not conform to the standard format")
    print(f"  [OK] Format verified.")

    # Register the file in the supported list
    update_supported_list(json_file)
    print(f"  [OK] Registered in supported.txt.")

    # ── Final summary ─────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("  PROCESS COMPLETED SUCCESSFULLY")
    print("="*60)
    print()
    print("  Final files:")
    print(f"    Parameter JSON : {json_file}")
    print(f"    Drag CSV       : {csv_file}")
    print()
    print("  These files are ready to be used in the simulation code (src/).")
    print("="*60 + "\n")

    return {
        "json":     json_file,
        "csv":      csv_file,
        "ork_path": verified_ork
    }


# =============================================================================
# ENTRY POINT: when run directly from the terminal
# python ork_serializer.py
# =============================================================================

if __name__ == "__main__":
    """
    Interactive mode: if you run this script directly from the terminal
    without arguments, it will ask for the required information step by step.

    Usage from terminal:
        python ork_serializer.py

    You can also import the functions in another script:
        from ork_serializer import run_full_workflow
    """
    print("\n  Running in interactive mode.")
    print("  If you prefer to specify the paths directly, import the")
    print("  functions in your script. See usage_examples.py for details.")
    print()

    # Ask for .ork path
    ork_input = input(
        "  Path to .ork file (press Enter to search automatically): "
    ).strip()

    if ork_input == "":
        folder = input(
            "  Which folder to search in? (press Enter to use current folder): "
        ).strip()
        folder = folder if folder != "" else "."
        ork_input = None
    else:
        folder = "."

    # Ask for JAR path
    jar_input = input(
        "  Path to OpenRocket JAR (press Enter to search automatically): "
    ).strip()
    jar_input = jar_input if jar_input != "" else None

    # Ask for output folder
    output_input = input(
        "  Output folder (press Enter to use 'parameters/rocket/'): "
    ).strip()
    output_input = output_input if output_input != "" else "parameters/rocket/"

    # Run
    run_full_workflow(
        ork_path=ork_input,
        jar_path=jar_input,
        output_path=output_input,
        search_folder=folder,
        verbose=False
    )
    
    