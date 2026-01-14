import os
import sys
import subprocess
import json

# Define the paths for scripts
CRAWL_GIAPHA_SCRIPT = "crawl_giapha.py"
CRAWL_MEMBER_DETAILS_SCRIPT = "crawl_member_details.py"
EXTRACT_GIAPHA_INFO_SCRIPT = "extract_giapha_info.py"
EXTRACT_MEMBER_INFO_SCRIPT = "extract_member_info.py"

BASE_URL = "https://vietnamgiapha.com/" # Base URL for relative links

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
        print(e.stdout)
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

def pipeline(family_id: str):
    print(f"Starting pipeline for Family ID: {family_id}")

    # --- Define common paths ---
    output_family_dir = os.path.join("output", family_id)
    raw_data_dir = os.path.join(output_family_dir, "raw_data")
    data_dir = os.path.join(output_family_dir, "data")
    members_raw_data_dir = os.path.join(raw_data_dir, "members")
    members_data_dir = os.path.join(data_dir, "members")

    # Ensure base directories exist for output
    os.makedirs(output_family_dir, exist_ok=True)
    os.makedirs(raw_data_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(members_data_dir, exist_ok=True) # Ensure members data dir exists

    # --- Step 1.1: Crawl main family HTML pages ---
    giapha_html_path = os.path.join(raw_data_dir, "giapha.html")
    if not check_file_exists(giapha_html_path, "Main Giapha HTML"):
        if not run_command(["python3", CRAWL_GIAPHA_SCRIPT, family_id], 
                           f"Crawling main family pages for {family_id}"):
            return False

    # --- Step 1.2: Crawl individual member details HTML pages ---
    pha_he_html_path = os.path.join(raw_data_dir, "pha_he.html")
    if not check_directory_not_empty(members_raw_data_dir, "Member raw data"):
        if not run_command(["python3", CRAWL_MEMBER_DETAILS_SCRIPT, family_id, pha_he_html_path],
                           f"Crawling individual member detail pages for {family_id}"):
            return False

    # --- DEBUG: Verify contents of members_raw_data_dir ---
    print(f"\n--- DEBUG: Contents of {members_raw_data_dir} after crawling members ---")
    subprocess.run(["ls", "-l", members_raw_data_dir], check=False)
    print("--------------------------------------------------")


    # --- Step 2.1: Extract main family information ---
    giapha_info_json_path = os.path.join(data_dir, f"giapha_info_{family_id}.json")
    if not check_file_exists(giapha_info_json_path, "Main Giapha Info JSON"):
        # The extract_giapha_info.py script expects the path to giapha.html
        if not run_command(["python3", EXTRACT_GIAPHA_INFO_SCRIPT, giapha_html_path],
                           f"Extracting main family info for {family_id}"):
            return False
    
    # --- Step 2.2: Extract individual member information ---
    # We need to iterate through all crawled member HTML files
    member_html_files = [f for f in os.listdir(members_raw_data_dir) if f.endswith('.html')] 
    if not member_html_files:
        print(f"No member HTML files found in {members_raw_data_dir}. Skipping member info extraction.")
    else:
        all_members_extracted = True
        for member_html_filename in member_html_files:
            member_id = member_html_filename.replace('.html', '')
            member_html_path = os.path.join(members_raw_data_dir, member_html_filename)
            member_json_path = os.path.join(members_data_dir, f"{member_id}.json")

            # Force re-extraction by removing existing JSON file
            if os.path.exists(member_json_path):
                os.remove(member_json_path)
                print(f"Removed existing '{member_json_path}' to force re-extraction.")

            if not run_command(["python3", EXTRACT_MEMBER_INFO_SCRIPT, member_html_path, member_json_path],
                               f"Extracting info for member {member_id}"):
                all_members_extracted = False
                break

        if not all_members_extracted:
            return False

    print(f"\nPipeline completed successfully for Family ID: {family_id}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <family_id>")
        sys.exit(1)
    
    target_family_id = sys.argv[1]
    pipeline(target_family_id)
