import os
import subprocess
import sys

def run_command(command_parts: list, description: str):
    """Executes a shell command and prints its output."""
    print(f"\n--- {description} ---")
    try:
        result = subprocess.run(command_parts, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Stderr:\n", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during {description}:")
        print(e.stderr)
        return False
    except FileNotFoundError:
        print(f"Error: Command not found. Ensure {command_parts[0]} is in PATH or correctly specified.")
        return False

def check_file_exists(filepath: str, description: str):
    """Checks if a file exists and prints a message."""
    if os.path.exists(filepath):
        print(f"'{description}' already exists at {filepath}. Skipping step.")
        return True
    return False

def check_directory_not_empty(dirpath: str, description: str):
    """Checks if a directory exists and is not empty."""
    if os.path.exists(dirpath) and os.listdir(dirpath):
        print(f"'{description}' directory already exists and is not empty at {dirpath}. Skipping step.")
        return True
    return False
