"""
usage_examples.py
=================
Detailed examples of how to use ork_serializer.py

This file is intended for any team member who wants to understand
how the serializer works step by step, with real cases from the project.

---------------------------------------------
HOW TO RUN THESE EXAMPLES
---------------------------------------------
1. Open a terminal in the project folder.
2. Choose the example that fits your case.
3. Comment out the examples you do not want to run (with #).
4. Run:
    python usage_examples.py

---------------------------------------------
BEFORE RUNNING ANY EXAMPLE
---------------------------------------------
Make sure you have:
- Python 3.8+
- rocketserializer installed  ->  pip install rocketserializer
- Java 17 installed           ->  https://www.oracle.com/java/technologies/downloads/
- OpenRocket JAR 23.09        ->  https://openrocket.info/downloads.html?vers=23.09#content-JAR
- Your .ork file ready
"""

from ork_serializer import (
    verify_installation,
    verify_ork_file,
    run_serialization,
    run_full_workflow
)


# =============================================================================
# EXAMPLE 1 - Simplest: fully automatic
# =============================================================================
# Use when:
#   - You only have ONE .ork file in the project folder.
#   - The OpenRocket JAR is in the same folder as this script.
#   - You do not want to deal with paths.
#
# Expected folder structure:
#   project/
#   +-- MyRocket_v1.ork          <- the .ork is here
#   +-- OpenRocket-23.09.jar     <- the JAR is here
#   +-- ork_serializer.py
#   +-- usage_examples.py
# =============================================================================

def example_1_fully_automatic():
    print("\n" + "-"*60)
    print("EXAMPLE 1: Fully automatic")
    print("-"*60)

    results = run_full_workflow(
        jar_path = "OpenRocket-23.09.jar"
        # The code searches for the .ork automatically in the current folder
    )

    print(f"\nJSON generated at: {results.get('json', 'Not generated')}")
    print(f"CSV  generated at: {results.get('csv',  'Not generated')}")


# =============================================================================
# EXAMPLE 2 - Providing the exact .ork path (recommended)
# =============================================================================
# Use when:
#   - You know exactly where your .ork file is.
#   - You have multiple .ork files and want to pick a specific one.
#   - You want reproducibility (always the same file).
#
# Folder structure:
#   project/
#   +-- ork_files/
#   |   +-- AURORA_v02.ork       <- the .ork is here
#   +-- OpenRocket-23.09.jar
#   +-- parameters/rocket/       <- generated files will be saved here
#   +-- ork_serializer.py
#   +-- usage_examples.py
# =============================================================================

def example_2_exact_path():
    print("\n" + "-"*60)
    print("EXAMPLE 2: Providing the exact .ork path")
    print("-"*60)

    results = run_full_workflow(
        ork_path    = "ork_files/AURORA_v02.ork",    # <- change this to your file
        jar_path    = "OpenRocket-23.09.jar",          # <- change if your JAR has a different name
        output_path = "parameters/rocket/"             # folder where results are saved
    )

    print(f"\nJSON generated at: {results.get('json', 'Not generated')}")
    print(f"CSV  generated at: {results.get('csv',  'Not generated')}")


# =============================================================================
# EXAMPLE 3 - Searching in a specific folder
# =============================================================================
# Use when:
#   - You have all .ork files in a folder called "ork_files/" (recommended).
#   - There may be more than one .ork and you want the code to ask which to use.
# =============================================================================

def example_3_search_in_folder():
    print("\n" + "-"*60)
    print("EXAMPLE 3: Automatic search in 'ork_files/' folder")
    print("-"*60)

    results = run_full_workflow(
        jar_path      = "OpenRocket-23.09.jar",
        search_folder = "ork_files/",        # searches for .ork files in this folder
        output_path   = "parameters/rocket/"
    )

    print(f"\nJSON generated at: {results.get('json', 'Not generated')}")
    print(f"CSV  generated at: {results.get('csv',  'Not generated')}")


# =============================================================================
# EXAMPLE 4 - Using functions separately (step by step)
# =============================================================================
# Use when:
#   - You want more control over each step.
#   - You want to verify first without running the serialization.
#   - You are developing or debugging the code.
# =============================================================================

def example_4_step_by_step():
    print("\n" + "-"*60)
    print("EXAMPLE 4: Functions used separately (step by step)")
    print("-"*60)

    # Step 1: Verify that rocketserializer is installed
    print("\n--- Step 1: Verify installation ---")
    verify_installation()

    # Step 2: Verify and get the .ork path
    print("\n--- Step 2: Verify the .ork file ---")
    ork_path = verify_ork_file(
        ork_path = "ork_files/IREC_version03.ork"   # <- change this
    )
    print(f"  File ready: {ork_path}")

    # Step 3: Run the serialization
    print("\n--- Step 3: Run serialization ---")
    files = run_serialization(
        ork_path    = ork_path,
        jar_path    = "OpenRocket-23.09.jar",
        output_path = "parameters/rocket/",
        verbose     = True    # True to see detailed progress
    )

    print(f"\nResults:")
    print(f"  JSON: {files.get('json', 'Not generated')}")
    print(f"  CSV : {files.get('csv',  'Not generated')}")


# =============================================================================
# EXAMPLE 5 - JAR in a different folder
# =============================================================================
# Use when:
#   - The OpenRocket JAR is not in the project folder.
#   - For example, you have it in your Downloads folder.
#
# NOTE: On Windows, use forward slashes '/' or double backslashes '\\':
#   "C:/Users/YourName/Downloads/OpenRocket-23.09.jar"   <- correct
#   "C:\\Users\\YourName\\Downloads\\OpenRocket-23.09.jar" <- also correct
# =============================================================================

def example_5_jar_in_different_folder():
    print("\n" + "-"*60)
    print("EXAMPLE 5: JAR in a different folder")
    print("-"*60)

    results = run_full_workflow(
        ork_path    = "ork_files/MyRocket_v1.ork",
        jar_path    = "C:/Users/YourName/Downloads/OpenRocket-23.09.jar",  # <- adjust this
        output_path = "parameters/rocket/"
    )

    print(f"\nJSON generated at: {results.get('json', 'Not generated')}")
    print(f"CSV  generated at: {results.get('csv',  'Not generated')}")


# =============================================================================
# EXAMPLE 6 - Only verify, without serializing yet
# =============================================================================
# Use when:
#   - You want to confirm everything is set up correctly before running.
#   - You are passing the script to a team member and want them to check first.
# =============================================================================

def example_6_only_verify():
    print("\n" + "-"*60)
    print("EXAMPLE 6: Only verify installation and file")
    print("-"*60)

    # Verify installation
    ok = verify_installation()
    print(f"  rocketserializer installed: {ok}")

    # Verify .ork file
    path = verify_ork_file(
        ork_path = "ork_files/MyRocket_v1.ork"
    )
    print(f"  .ork file OK: {path}")

    print("\n  Everything is ready. You can proceed with serialization.")
    print("  To serialize, use run_serialization() or run_full_workflow().")


# =============================================================================
# ENTRY POINT
# =============================================================================
# Uncomment the example you want to run and comment out the others.
# =============================================================================

if __name__ == "__main__":

    # ── Choose ONE example and uncomment it ──────────────────────────────────

    # example_1_fully_automatic()
    example_2_exact_path()        # <- This is the most recommended one to start with
    # example_3_search_in_folder()
    # example_4_step_by_step()
    # example_5_jar_in_different_folder()
    # example_6_only_verify()