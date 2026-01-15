import os
import sys
import subprocess
import json
import html2text # Import html2text for HTML to Markdown conversion

# Define the paths for scripts
CRAWL_GIAPHA_SCRIPT = "crawl_giapha.py"
CRAWL_MEMBER_DETAILS_SCRIPT = "crawl_member_details.py"
EXTRACT_GIAPHA_INFO_SCRIPT = "extract_giapha_info_ollama.py"
EXTRACT_MEMBER_INFO_SCRIPT = "extract_member_info_ollama.py"

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

def convert_html_to_md(html_file_path: str, md_file_path: str):
    """Converts an HTML file to a Markdown file."""
    print(f"Converting HTML from '{html_file_path}' to Markdown at '{md_file_path}'")
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f_html:
            html_content = f_html.read()
        
        # Configure html2text
        h = html2text.HTML2Text()
        h.unicode_snob = True # Ensures proper handling of Unicode characters
        h.body_width = 0 # Disable line wrapping
        h.ignore_images = False # Include image links
        h.ignore_tables = False # Include table formatting (might need refinement based on exact markdown parser)
        h.single_line_break = True # Preserve single line breaks

        md_content = h.handle(html_content)
        
        with open(md_file_path, 'w', encoding='utf-8') as f_md:
            f_md.write(md_content)
        print(f"Successfully converted '{html_file_path}' to '{md_file_path}'.")
        return True
    except Exception as e:
        print(f"Error converting '{html_file_path}' to Markdown: {e}")
        return False

def pipeline(family_id: str):
    print(f"Starting pipeline for Family ID: {family_id}")

    # --- Define common paths ---
    output_family_dir = os.path.join("output", family_id)
    
    raw_html_dir = os.path.join(output_family_dir, "raw_html")
    markdown_dir = os.path.join(output_family_dir, "markdown")
    data_dir = os.path.join(output_family_dir, "data")
    
    members_raw_html_dir = os.path.join(raw_html_dir, "members")
    members_markdown_dir = os.path.join(markdown_dir, "members")
    members_data_dir = os.path.join(data_dir, "members")

    # Ensure all necessary directories exist
    os.makedirs(output_family_dir, exist_ok=True)
    os.makedirs(raw_html_dir, exist_ok=True)
    os.makedirs(markdown_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(members_raw_html_dir, exist_ok=True)
    os.makedirs(members_markdown_dir, exist_ok=True)
    os.makedirs(members_data_dir, exist_ok=True)

    # --- Step 1.1: Crawl main family HTML pages ---
    giapha_html_path = os.path.join(raw_html_dir, "giapha.html")
    giapha_md_path = os.path.join(markdown_dir, "giapha.md")

    pha_he_html_path = os.path.join(raw_html_dir, "pha_he.html")
    pha_he_md_path = os.path.join(markdown_dir, "pha_he.md")

    pha_ky_gia_su_html_path = os.path.join(raw_html_dir, "pha_ky_gia_su.html")
    pha_ky_gia_su_md_path = os.path.join(markdown_dir, "pha_ky_gia_su.md")

    thuy_to_html_path = os.path.join(raw_html_dir, "thuy_to.html")
    thuy_to_md_path = os.path.join(markdown_dir, "thuy_to.md")

    toc_uoc_html_path = os.path.join(raw_html_dir, "toc_uoc.html")
    toc_uoc_md_path = os.path.join(markdown_dir, "toc_uoc.md")

    if not check_file_exists(giapha_html_path, "Main Giapha HTML"):
        # CRAWL_GIAPHA_SCRIPT now expects the full path for giapha.html and the base dir for other files
        if not run_command(["python3", CRAWL_GIAPHA_SCRIPT, family_id, giapha_html_path, raw_html_dir], 
                           f"Crawling main family pages for {family_id}"):
            return False
    
    if not check_file_exists(giapha_md_path, "Main Giapha Markdown"):
        if not convert_html_to_md(giapha_html_path, giapha_md_path):
            return False

    if not check_file_exists(pha_he_md_path, "Pha He Markdown"):
        if not convert_html_to_md(pha_he_html_path, pha_he_md_path):
            return False

    if not check_file_exists(pha_ky_gia_su_md_path, "Pha Ky Gia Su Markdown"):
        if not convert_html_to_md(pha_ky_gia_su_html_path, pha_ky_gia_su_md_path):
            return False

    if not check_file_exists(thuy_to_md_path, "Thuy To Markdown"):
        if not convert_html_to_md(thuy_to_html_path, thuy_to_md_path):
            return False

    if not check_file_exists(toc_uoc_md_path, "Toc Uoc Markdown"):
        if not convert_html_to_md(toc_uoc_html_path, toc_uoc_md_path):
            return False

    # ... (previous code) ...

    # --- Step 1.2: Crawl individual member details HTML pages ---
    # The crawl_member_details.py script should output directly to members_raw_html_dir
    pha_he_html_path = os.path.join(raw_html_dir, "pha_he.html") # Path to pha_he.html for parsing links
    if not check_directory_not_empty(members_raw_html_dir, "Member raw HTML data"):
        if not run_command(["python3", CRAWL_MEMBER_DETAILS_SCRIPT, family_id, members_raw_html_dir, pha_he_html_path],
                           f"Crawling individual member detail pages for {family_id} using {pha_he_html_path}"):
            return False
    # ... (rest of the code) ...

    # --- Step 1.3: Convert individual member HTML pages to Markdown ---
    member_html_files = [f for f in os.listdir(members_raw_html_dir) if f.endswith('.html')] 
    if not member_html_files:
        print(f"No member HTML files found in {members_raw_html_dir}. Skipping member Markdown conversion.")
    else:
        all_members_converted = True
        for member_html_filename in member_html_files:
            member_id = member_html_filename.replace('.html', '')
            member_html_path = os.path.join(members_raw_html_dir, member_html_filename)
            member_md_path = os.path.join(members_markdown_dir, f"{member_id}.md")

            if not check_file_exists(member_md_path, f"Member {member_id} Markdown"):
                if not convert_html_to_md(member_html_path, member_md_path):
                    all_members_converted = False
                    break
        if not all_members_converted:
            return False



    # --- Step 2.1: Extract main family information from Markdown ---
    giapha_info_json_path = os.path.join(data_dir, f"giapha_info_{family_id}.json")
    if not check_file_exists(giapha_info_json_path, "Main Giapha Info JSON"):
        # The extract_giapha_info.py script now expects the path to giapha.md
        if not run_command(["python3", EXTRACT_GIAPHA_INFO_SCRIPT, giapha_md_path, giapha_info_json_path, os.getenv("OLLAMA_MODEL", "llama3:8b"), pha_ky_gia_su_html_path, thuy_to_html_path, toc_uoc_html_path],
                           f"Extracting main family info for {family_id}"):
            return False
    
    # --- Step 2.2: Extract individual member information from Markdown ---
    member_md_files = [f for f in os.listdir(members_markdown_dir) if f.endswith('.md')] 
    if not member_md_files:
        print(f"No member Markdown files found in {members_markdown_dir}. Skipping member info extraction.")
    else:
        all_members_extracted = True
        for member_md_filename in member_md_files:
            member_id = member_md_filename.replace('.md', '')
            member_md_path = os.path.join(members_markdown_dir, member_md_filename)
            member_json_path = os.path.join(members_data_dir, f"{member_id}.json")

            # Force re-extraction by removing existing JSON file (if desired)
            # if os.path.exists(member_json_path):
            #     os.remove(member_json_path)
            #     print(f"Removed existing '{member_json_path}' to force re-extraction.")

            if not check_file_exists(member_json_path, f"Member {member_id} Info JSON"):
                if not run_command(["python3", EXTRACT_MEMBER_INFO_SCRIPT, member_md_path, member_json_path],
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
