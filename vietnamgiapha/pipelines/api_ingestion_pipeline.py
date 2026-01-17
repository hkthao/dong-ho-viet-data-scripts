# -*- coding: utf-8 -*-
import subprocess
import logging
import argparse
import os

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_script(script_path: str, args: list = None):
    """
    Chạy một script Python và in ra output.
    """
    if args is None:
        args = []
    
    command = ["python3", "-m", script_path] + args # Sử dụng python3 -m và truyền đường dẫn module trực tiếp
    
    # Thiết lập PYTHONPATH cho subprocess
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_script_dir, "..", ".."))
    env = os.environ.copy()
    env["PYTHONPATH"] = project_root
    
    logging.info(f"Đang chạy lệnh: {' '.join(command)} với PYTHONPATH={env['PYTHONPATH']}")
    try:
        # Chạy script như một tiến trình con
        process = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8', env=env)
        logging.info(f"Script '{script_path}' hoàn tất thành công.")
        if process.stdout:
            logging.info(f"Stdout từ '{script_path}':\n{process.stdout}")
        if process.stderr:
            logging.warning(f"Stderr từ '{script_path}':\n{process.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Script '{script_path}' thất bại với mã lỗi {e.returncode}.")
        logging.error(f"Stdout từ '{script_path}':\n{e.stdout}")
        logging.error(f"Stderr từ '{script_path}':\n{e.stderr}")
        return False
    except FileNotFoundError:
        logging.error(f"Lỗi: Không tìm thấy trình thông dịch 'python' hoặc script '{script_path}'. Đảm bảo Python đã được cài đặt và nằm trong PATH.")
        return False
    except Exception as e:
        logging.error(f"Lỗi không xác định khi chạy script '{script_path}': {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Chạy pipeline tạo thành viên và cập nhật mối quan hệ cho hệ thống gia phả.")
    parser.add_argument("--folder", type=str, help="Chỉ định thư mục gia đình cần xử lý (ví dụ: '1'). Nếu không, tất cả các thư mục sẽ được xử lý.")
    parser.add_argument("--member_limit", type=int, default=0, help="Giới hạn số lượng thành viên được tạo từ mỗi thư mục. Mặc định là 0 (không giới hạn). (Chỉ áp dụng cho create_members.py)")
    parser.add_argument("--relation_limit", type=int, help="Giới hạn số lượng mối quan hệ cần cập nhật cho mục đích debug hoặc test. (Chỉ áp dụng cho update_relationships.py)")
    
    args = parser.parse_args()

    create_members_script = "vietnamgiapha.api_integration.create_members"
    update_relationships_script = "vietnamgiapha.api_integration.update_relationships"

    # Bước 1: Chạy create_members.py
    logging.info("--- Bắt đầu Bước 1: Tạo thành viên và thu thập mối quan hệ ---")
    create_members_args = []
    if args.folder:
        create_members_args.extend(["--folder", args.folder])
    if args.member_limit > 0:
        create_members_args.extend(["--member_limit", str(args.member_limit)])

    if not run_script(create_members_script, create_members_args):
        logging.error("Pipeline bị dừng do lỗi trong quá trình tạo thành viên.")
        return

    # Bước 2: Chạy update_relationships.py
    logging.info("--- Bắt đầu Bước 2: Cập nhật mối quan hệ ---")
    update_relationships_args = []
    if args.folder:
        update_relationships_args.extend(["--folder", args.folder])
    if args.relation_limit:
        update_relationships_args.extend(["--limit", str(args.relation_limit)])

    if not run_script(update_relationships_script, update_relationships_args):
        logging.error("Pipeline bị dừng do lỗi trong quá trình cập nhật mối quan hệ.")
        return

    logging.info("--- Pipeline hoàn tất thành công! ---")

if __name__ == "__main__":
    main()
