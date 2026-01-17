import os
import sys
import logging
import argparse

from .api_ingestion_pipeline import run_script

# Cấu hình logging cho pipeline chính
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main_pipeline(family_id: str, force: bool = False):


    logging.info(f"--- Bắt đầu pipeline chính cho Family ID: {family_id} (Force: {force}) ---")





    crawl_module_path = "vietnamgiapha.pipelines.crawl_pipeline"


    extract_rulebase_module_path = "vietnamgiapha.pipelines.extract_pipeline_rulebase"


    api_ingestion_module_path = "vietnamgiapha.pipelines.api_ingestion_pipeline"





    # Bước 1: Chạy pipeline thu thập dữ liệu (crawling)


    logging.info(f"Bắt đầu Bước 1: Thu thập dữ liệu cho Family ID: {family_id}")


    crawl_args = [family_id]


    if force:


        crawl_args.append("--force")


    if not run_script(crawl_module_path, crawl_args):
        logging.error(f"Pipeline chính thất bại trong quá trình thu thập dữ liệu cho Family ID: {family_id}")
        return False

    # Bước 2: Chạy pipeline trích xuất dữ liệu dựa trên quy tắc
    logging.info(f"Bắt đầu Bước 2: Trích xuất dữ liệu dựa trên quy tắc cho Family ID: {family_id}")
    extract_rulebase_args = ["--output_base_dir", "output", "--family_id", family_id, "--force"] # Added --force as per README example
    if not run_script(extract_rulebase_module_path, extract_rulebase_args):
        logging.error(f"Pipeline chính thất bại trong quá trình trích xuất dữ liệu dựa trên quy tắc cho Family ID: {family_id}")
        return False

    # Bước 3: Chạy pipeline nhập liệu API
    logging.info(f"Bắt đầu Bước 3: Nhập liệu API cho Family ID: {family_id}")
    api_ingestion_args = ["--folder", family_id]
    if not run_script(api_ingestion_module_path, api_ingestion_args):
        logging.error(f"Pipeline chính thất bại trong quá trình nhập liệu API cho Family ID: {family_id}")
        return False


    logging.info(f"--- Pipeline chính hoàn tất thành công cho Family ID: {family_id} ---")
    return True

def run_pipeline_for_range(start_id: int, end_id: int, force: bool = False):
    failed_ids = []
    log_file_path = "failed_crawls.txt" # This file is mentioned in README for failed crawls, let's keep it.

    # Ensure log file is clear for new run
    if os.path.exists(log_file_path):
        os.remove(log_file_path)

    for i in range(start_id, end_id + 1):
        family_id = str(i)
        logging.info(f"--- Đang xử lý Family ID: {family_id} (Force: {force}) ---")
        try:
            success = main_pipeline(family_id, force) # Call synchronous main_pipeline
            if not success:
                failed_ids.append(family_id)
                with open(log_file_path, "a", encoding='utf-8') as f:
                    f.write(f"{family_id}\n")
                logging.warning(f"Failed to process Family ID: {family_id}. Added to {log_file_path}")
        except Exception as e:
            failed_ids.append(family_id)
            with open(log_file_path, "a", encoding='utf-8') as f:
                f.write(f"{family_id} (Error: {e})\n")
            logging.error(f"An error occurred while processing Family ID: {family_id}: {e}. Added to {log_file_path}")
        logging.info(f"--- Đã hoàn tất xử lý Family ID: {family_id} ---\n")

    if failed_ids:
        logging.error(f"\n--- Tóm tắt: Thất bại khi xử lý {len(failed_ids)} Family ID ---")
        logging.error(f"Các ID thất bại: {', '.join(failed_ids)}")
        logging.error(f"Chi tiết được ghi vào {log_file_path}")
    else:
        logging.info("\n--- Tóm tắt: Tất cả Family ID đã được xử lý thành công ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Điều phối toàn bộ quy trình (thu thập, trích xuất, nhập liệu API).")
    parser.add_argument("family_id_or_start_id", type=str, help="ID của gia đình hoặc ID bắt đầu cho dải.")
    parser.add_argument("end_id", nargs='?', type=int, help="ID kết thúc cho dải ID gia đình (nếu cung cấp start_id).")
    parser.add_argument("--force", action="store_true", help="Buộc thu thập/trích xuất/nhập liệu lại dữ liệu ngay cả khi file đã tồn tại.")
    
    args = parser.parse_args()

    if args.end_id is None: # Single family ID
        main_pipeline(args.family_id_or_start_id, args.force)
    else: # Range of family IDs
        try:
            start_id = int(args.family_id_or_start_id)
            end_id = args.end_id
            if start_id > end_id:
                logging.error("Lỗi: start_id không thể lớn hơn end_id.")
                sys.exit(1)
            run_pipeline_for_range(start_id, end_id, args.force)
        except ValueError:
            logging.error("Lỗi: start_id và end_id phải là số nguyên.")
            logging.error("Cách dùng: python main_pipeline.py <family_id> [--force]")
            logging.error("       python main_pipeline.py <start_id> <end_id> [--force]")
            sys.exit(1)
