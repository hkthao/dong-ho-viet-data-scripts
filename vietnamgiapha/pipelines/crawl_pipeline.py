import asyncio
import os
import sys
import argparse # Import argparse

from ..utils.utils import run_command, check_file_exists
from ..crawling.crawl_member_details import crawl_member_details

# Define the paths for scripts
CRAWL_GIAPHA_SCRIPT = "vietnamgiapha/crawling/crawl_giapha.py"

async def crawl_pipeline(family_id: str, force: bool = False):
    print(f"Starting crawling pipeline for Family ID: {family_id} (Force: {force})")

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

    if not force and not check_file_exists(giapha_html_path, "Main Giapha HTML"):
        # CRAWL_GIAPHA_SCRIPT now expects the full path for giapha.html and the base dir for other files
        crawl_giapha_args = ["python3", CRAWL_GIAPHA_SCRIPT, family_id, giapha_html_path, raw_html_dir]
        if force:
            crawl_giapha_args.append("--force")
        if not await run_command(crawl_giapha_args, f"Crawling main family pages for {family_id}"):
            return False
    elif force:
        print(f"Force crawling giapha.html for Family ID: {family_id}")
        crawl_giapha_args = ["python3", CRAWL_GIAPHA_SCRIPT, family_id, giapha_html_path, raw_html_dir]
        crawl_giapha_args.append("--force")
        if not await run_command(crawl_giapha_args, f"Crawling main family pages for {family_id}"):
            return False
    else:
        print(f"Skipping giapha.html crawling for Family ID: {family_id} as file exists and force is not true.")
    
    # --- Step 1.2: Crawl individual member details HTML pages ---
    # The crawl_member_details.py script now handles individual file existence checks
    # and directly awaits its execution to avoid subprocess issues.
    if not await crawl_member_details(family_id, members_raw_html_dir, pha_he_html_path, force):
        return False

    print(f"\nCrawling pipeline completed successfully for Family ID: {family_id}")
    return True

async def run_crawl_pipeline_for_range(start_id: int, end_id: int, force: bool = False):
    failed_crawls = []

    for i in range(start_id, end_id + 1):
        family_id = str(i)
        print(f"--- Đang xử lý Family ID: {family_id} để thu thập dữ liệu ---")
        try:
            success = await crawl_pipeline(family_id, force)
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
    parser = argparse.ArgumentParser(description="Quản lý quy trình thu thập dữ liệu HTML.")
    parser.add_argument("family_id_or_start_id", type=str, help="ID của gia đình hoặc ID bắt đầu cho dải.")
    parser.add_argument("end_id", nargs='?', type=int, help="ID kết thúc cho dải ID gia đình (nếu cung cấp start_id).")
    parser.add_argument("--force", action="store_true", help="Buộc thu thập lại dữ liệu ngay cả khi file đã tồn tại.")
    
    args = parser.parse_args()

    if args.end_id is None: # Single family ID
        asyncio.run(crawl_pipeline(args.family_id_or_start_id, args.force))
    else: # Range of family IDs
        try:
            start_id = int(args.family_id_or_start_id)
            end_id = args.end_id
            if start_id > end_id:
                print("Lỗi: start_id không được lớn hơn end_id.")
                sys.exit(1)
            asyncio.run(run_crawl_pipeline_for_range(start_id, end_id, args.force))
        except ValueError:
            print("Lỗi: start_id và end_id phải là số nguyên.")
            print("Cách dùng: python crawl_pipeline.py <family_id> [--force]")
            print("       python crawl_pipeline.py <start_id> <end_id> [--force]")
            sys.exit(1)

