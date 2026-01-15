import os
import sys

from utils import run_command, check_file_exists
from crawl_member_details import crawl_member_details

# Define the paths for scripts
CRAWL_GIAPHA_SCRIPT = "vietnamgiapha/crawl_giapha.py"

def crawl_pipeline(family_id: str):
    print(f"Starting crawling pipeline for Family ID: {family_id}")

    # --- Define common paths ---
    output_family_dir = os.path.join("output", family_id)
    raw_html_dir = os.path.join(output_family_dir, "raw_html")
    members_raw_html_dir = os.path.join(raw_html_dir, "members")

    # Ensure all necessary directories exist
    os.makedirs(output_family_dir, exist_ok=True)
    os.makedirs(raw_html_dir, exist_ok=True)
    os.makedirs(members_raw_html_dir, exist_ok=True)

    # --- Step 1.1: Crawl main family HTML pages ---
    giapha_html_path = os.path.join(raw_html_dir, "giapha.html")
    pha_he_html_path = os.path.join(raw_html_dir, "pha_he.html")
    #pha_ky_gia_su_html_path = os.path.join(raw_html_dir, "pha_ky_gia_su.html")
    #thuy_to_html_path = os.path.join(raw_html_dir, "thuy_to.html")
    #toc_uoc_html_path = os.path.join(raw_html_dir, "toc_uoc.html")

    if not check_file_exists(giapha_html_path, "Main Giapha HTML"):
        # CRAWL_GIAPHA_SCRIPT now expects the full path for giapha.html and the base dir for other files
        if not run_command(["python3", CRAWL_GIAPHA_SCRIPT, family_id, giapha_html_path, raw_html_dir], 
                           f"Crawling main family pages for {family_id}"):
            return False
    
    # --- Step 1.2: Crawl individual member details HTML pages ---
    # The crawl_member_details.py script now handles individual file existence checks
    # and directly awaits its execution to avoid subprocess issues.
    if not crawl_member_details(family_id, members_raw_html_dir, pha_he_html_path):
        return False

    print(f"\nCrawling pipeline completed successfully for Family ID: {family_id}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crawl_pipeline.py <family_id>")
        sys.exit(1)
    
    target_family_id = sys.argv[1]
    crawl_pipeline(target_family_id)
