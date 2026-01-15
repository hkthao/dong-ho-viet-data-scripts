import asyncio
import os
import sys

from utils import run_command, check_file_exists
from crawl_member_details import crawl_member_details

# Define the paths for scripts
CRAWL_GIAPHA_SCRIPT = "vietnamgiapha/crawl_giapha.py"

async def crawl_pipeline(family_id: str):
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
        if not await run_command(["python3", CRAWL_GIAPHA_SCRIPT, family_id, giapha_html_path, raw_html_dir], 
                           f"Crawling main family pages for {family_id}"):
            return False
    
    # --- Step 1.2: Crawl individual member details HTML pages ---
    # The crawl_member_details.py script now handles individual file existence checks
    # and directly awaits its execution to avoid subprocess issues.
    if not await crawl_member_details(family_id, members_raw_html_dir, pha_he_html_path):
        return False

    print(f"\nCrawling pipeline completed successfully for Family ID: {family_id}")
    return True

async def run_crawl_pipeline_for_range(start_id: int, end_id: int):
    failed_crawls = []

    for i in range(start_id, end_id + 1):
        family_id = str(i)
        print(f"--- Đang xử lý Family ID: {family_id} để thu thập dữ liệu ---")
        try:
            success = await crawl_pipeline(family_id)
            if not success:
                failed_crawls.append(family_id)
                print(f"Thất bại khi thu thập dữ liệu Family ID: {family_id}")
        except Exception as e:
            failed_crawls.append(family_id)
            print(f"Có lỗi xảy ra khi thu thập dữ liệu Family ID: {family_id}: {e}")
        print(f"--- Đã hoàn tất xử lý Family ID: {family_id} để thu thập dữ liệu ---\n")

    if failed_crawls:
        print(f"\n--- Tóm tắt: Thất bại khi thu thập dữ liệu {len(failed_crawls)} Family ID ---")
        print(f"Các Family ID thất bại: {', '.join(failed_crawls)}")
        return False
    else:
        print("\n--- Tóm tắt: Tất cả Family ID đã được thu thập dữ liệu thành công ---")
        return True

if __name__ == "__main__":
    if len(sys.argv) == 2:
        target_family_id = sys.argv[1]
        asyncio.run(crawl_pipeline(target_family_id))
    elif len(sys.argv) == 3:
        try:
            start_id = int(sys.argv[1])
            end_id = int(sys.argv[2])
            if start_id > end_id:
                print("Lỗi: start_id không được lớn hơn end_id.")
                sys.exit(1)
            asyncio.run(run_crawl_pipeline_for_range(start_id, end_id))
        except ValueError:
            print("Lỗi: start_id và end_id phải là số nguyên.")
            print("Cách dùng: python crawl_pipeline.py <family_id>")
            print("       python crawl_pipeline.py <start_id> <end_id>")
            sys.exit(1)
    else:
        print("Cách dùng: python crawl_pipeline.py <family_id>")
        print("       python crawl_pipeline.py <start_id> <end_id>")
        sys.exit(1)
