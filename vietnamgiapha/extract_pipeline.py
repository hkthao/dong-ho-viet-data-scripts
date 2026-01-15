import os
import sys
import asyncio

from utils import run_command, check_file_exists, check_directory_not_empty

# Define the paths for scripts
EXTRACT_GIAPHA_INFO_SCRIPT = "vietnamgiapha/extract_giapha_info_ollama.py"
EXTRACT_MEMBER_INFO_SCRIPT = "vietnamgiapha/extract_member_info_ollama.py"

async def extract_pipeline(family_id: str, limit: int = None):
    print(f"Starting extraction pipeline for Family ID: {family_id}")

    # --- Define common paths ---
    output_family_dir = os.path.join("output", family_id)
    raw_html_dir = os.path.join(output_family_dir, "raw_html")
    data_dir = os.path.join(output_family_dir, "data")
    members_raw_html_dir = os.path.join(raw_html_dir, "members")
    members_data_dir = os.path.join(data_dir, "members")

    # Ensure all necessary directories exist (these should already exist from crawling)
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(members_data_dir, exist_ok=True)

    # --- Step 2.1: Extract main family information from HTML ---
    giapha_html_path = os.path.join(raw_html_dir, "giapha.html")
    giapha_info_json_path = os.path.join(data_dir, f"giapha_info_{family_id}.json")
    pha_ky_gia_su_html_path = os.path.join(raw_html_dir, "pha_ky_gia_su.html")
    thuy_to_html_path = os.path.join(raw_html_dir, "thuy_to.html")
    toc_uoc_html_path = os.path.join(raw_html_dir, "toc_uoc.html")

    if not check_file_exists(giapha_info_json_path, "Main Giapha Info JSON"):
        # The extract_giapha_info.py script now expects the path to giapha.html
        if not await run_command(["python3", EXTRACT_GIAPHA_INFO_SCRIPT, giapha_html_path, giapha_info_json_path, os.getenv("OLLAMA_MODEL", "llama3:8b"), pha_ky_gia_su_html_path, thuy_to_html_path, toc_uoc_html_path],
                           f"Extracting main family info for {family_id}"):
            return False
    
    # --- Step 2.2: Extract individual member information from HTML ---
    member_html_files = [f for f in os.listdir(members_raw_html_dir) if f.endswith('.html')] 
    if not member_html_files:
        print(f"No member HTML files found in {members_raw_html_dir}. Skipping member info extraction.")
    else:
        # Apply limit if provided
        if limit is not None:
            member_html_files = member_html_files[:limit]
            print(f"Limiting member extraction to {limit} files.")

        tasks = []
        for member_html_filename in member_html_files:
            member_id = member_html_filename.replace('.html', '')
            member_html_path = os.path.join(members_raw_html_dir, member_html_filename)
            member_json_path = os.path.join(members_data_dir, f"{member_id}.json")

            if not check_file_exists(member_json_path, f"Member {member_id} Info JSON"):
                task = run_command(["python3", EXTRACT_MEMBER_INFO_SCRIPT, member_html_path, member_json_path, family_id],
                                   f"Extracting info for member {member_id}")
                tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"Error processing member {member_html_files[i].replace('.html', '')}: {result}", file=sys.stderr)
                    return False # Return False if any task raised an exception
                elif not result:
                    print(f"Extraction failed for member {member_html_files[i].replace('.html', '')}", file=sys.stderr)
                    return False # Return False if any task explicitly returned False
        else:
            print("All member JSON files already exist or no members to process.")

    print(f"\nExtraction pipeline completed successfully for Family ID: {family_id}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_pipeline.py <family_id> [limit]")
        sys.exit(1)
    
    target_family_id = sys.argv[1]
    extraction_limit = None
    if len(sys.argv) > 2:
        try:
            extraction_limit = int(sys.argv[2])
            if extraction_limit < 1:
                print("Error: limit must be a positive integer.")
                sys.exit(1)
        except ValueError:
            print("Error: limit must be an integer.")
            print("Usage: python extract_pipeline.py <family_id> [limit]")
            sys.exit(1)

    asyncio.run(extract_pipeline(target_family_id, extraction_limit))