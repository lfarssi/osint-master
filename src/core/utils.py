# ----------------------------------------------------------
# Utility Functions
# ----------------------------------------------------------
# Helper functions used across the project:
#   - save_output(): saves results as a JSON file
# ----------------------------------------------------------

import json
import os
from pathlib import Path


# Output directory is at the project root, next to src/
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"


def save_output(filename, data):
    """
    Save a dictionary as a JSON file in the output/ folder.

    Creates the output/ folder if it doesn't exist.
    Adds .json extension if not already present.
    """
    # Make sure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Add .json extension if the user didn't include it
    if not filename.endswith(".json"):
        filename = filename + ".json"

    filepath = OUTPUT_DIR / filename

    try:
        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)
        print(f"  Results saved to: {filepath}")
        return True
    except IOError as error:
        print(f"  Error saving output: {error}")
        return False