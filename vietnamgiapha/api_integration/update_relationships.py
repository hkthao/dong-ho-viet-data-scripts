# -*- coding: utf-8 -*-
import os
import json
import requests
import logging
from typing import Optional
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Cấu hình API
BASE_URL = "http://localhost:8080/api" # Thay đổi nếu API của bạn chạy ở địa chỉ khác
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "") # Lấy từ biến môi trường, mặc định là chuỗi rỗng

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

OUTPUT_DIR = "output"

def main(target_folder: Optional[str] = None, limit: Optional[int] = None):
    logging.info("Bắt đầu quá trình cập nhật mối quan hệ thành viên.")
    
    folders_to_process = []
    if target_folder:
        folders_to_process.append(target_folder)
    else:
        folders_to_process = os.listdir(OUTPUT_DIR)

    for folder_name in folders_to_process:
        folder_path = os.path.join(OUTPUT_DIR, folder_name)
        if os.path.isdir(folder_path):
            logging.info(f"Đang xử lý thư mục: {folder_name}")

            data_folder_path = os.path.join(folder_path, "data")
            relationships_file = os.path.join(data_folder_path, "_relationships_to_update.json")
            member_map_file = os.path.join(data_folder_path, "_member_code_map.json")

            pending_relationship_updates = []
            member_code_to_api_id_map = {}

            if not os.path.exists(relationships_file):
                logging.warning(f"Không tìm thấy file mối quan hệ trung gian '{relationships_file}' cho thư mục '{folder_name}'. Bỏ qua cập nhật mối quan hệ.")
                continue
            if not os.path.exists(member_map_file):
                logging.warning(f"Không tìm thấy file ánh xạ thành viên trung gian '{member_map_file}' cho thư mục '{folder_name}'. Bỏ qua cập nhật mối quan hệ.")
                continue

            try:
                with open(relationships_file, 'r', encoding='utf-8') as f:
                    pending_relationship_updates = json.load(f)
                with open(member_map_file, 'r', encoding='utf-8') as f:
                    member_code_to_api_id_map = json.load(f)
                
                logging.info(f"Đã tải {len(pending_relationship_updates)} mối quan hệ và {len(member_code_to_api_id_map)} ánh xạ thành viên từ thư mục '{folder_name}'.")

                if limit is not None:
                    logging.info(f"Giới hạn số lượng mối quan hệ cần cập nhật: {limit}.")
                    pending_relationship_updates = pending_relationship_updates[:limit]

            except json.JSONDecodeError as e:
                logging.error(f"Lỗi đọc file JSON trung gian trong thư mục {folder_name}: {e}. Bỏ qua cập nhật mối quan hệ.")
                continue
            except Exception as e:
                logging.error(f"Lỗi không xác định khi tải dữ liệu trung gian cho thư mục {folder_name}: {e}. Bỏ qua cập nhật mối quan hệ.")
                continue

            logging.info(f"Bắt đầu cập nhật mối quan hệ cho các thành viên trong thư mục {folder_name}.")
            logging.info(f"Có {len(pending_relationship_updates)} mối quan hệ đang chờ cập nhật.")
            for rel_data in pending_relationship_updates:
                logging.debug(f"Đang xử lý rel_data: {json.dumps(rel_data, indent=2)}")
                member_api_id = rel_data["member_api_id"]
                member_code = rel_data["member_code"]
                update_payload = {}
                # Resolve fatherId
                father_code = rel_data.get("father_code")
                if father_code and father_code.strip() != "" and father_code != "null":
                    father_api_id = member_code_to_api_id_map.get(father_code)
                    if father_api_id:
                        update_payload["fatherId"] = father_api_id
                    else:
                        logging.warning(f"Không tìm thấy API ID cho cha có mã '{father_code}' của thành viên '{member_code}'.")
                
                # Resolve motherId
                mother_code = rel_data.get("mother_code")
                if mother_code and mother_code.strip() != "" and mother_code != "null":
                    mother_api_id = member_code_to_api_id_map.get(mother_code)
                    if mother_api_id:
                        update_payload["motherId"] = mother_api_id
                    else:
                        logging.warning(f"Không tìm thấy API ID cho mẹ có mã '{mother_code}' của thành viên '{member_code}'.")

                # Resolve husbandId / wifeId (spouses)
                if rel_data.get("spouse_codes"):
                    assigned_primary_spouse = False 
                    for spouse_code_to_resolve in rel_data["spouse_codes"]:
                        if spouse_code_to_resolve and spouse_code_to_resolve.strip() != "" and spouse_code_to_resolve != "null":
                            spouse_api_id = member_code_to_api_id_map.get(spouse_code_to_resolve)
                            if spouse_api_id:
                                if not assigned_primary_spouse: 
                                    if rel_data.get("gender") == "Male":
                                        update_payload["wifeId"] = spouse_api_id
                                        assigned_primary_spouse = True
                                    elif rel_data.get("gender") == "Female":
                                        update_payload["husbandId"] = spouse_api_id
                                        assigned_primary_spouse = True
                                    else:
                                        logging.warning(f"Không thể xác định giới tính của thành viên '{member_code}' để liên kết vợ/chồng '{spouse_code_to_resolve}'.")
                                else:
                                    logging.warning(f"Thành viên '{member_code}' có nhiều vợ/chồng được định nghĩa. Chỉ vợ/chồng đầu tiên ('{spouse_code_to_resolve}' được tìm thấy) được gán làm vợ/chồng chính do giới hạn của API. Các vợ/chồng khác sẽ được bỏ qua trong việc gán vào trường husbandId/wifeId của thành viên này.")
                            else:
                                logging.warning(f"Không tìm thấy API ID cho vợ/chồng có mã '{spouse_code_to_resolve}' của thành viên '{member_code}'.")


                if len(update_payload) > 0: 
                    logging.debug(f"Đang gửi update_payload cho thành viên '{member_code}' (ID: {member_api_id}): {json.dumps(update_payload, indent=2)}")
                    try:
                        response = requests.put(f"{BASE_URL}/member/{member_api_id}", headers=HEADERS, json=update_payload)
                        response.raise_for_status()
                        try:
                            result = response.json()
                            if result.get("succeeded"):
                                logging.info(f"Cập nhật mối quan hệ cho thành viên '{member_code}' thành công.")
                            else:
                                logging.error(f"Cập nhật mối quan hệ cho thành viên '{member_code}' thất bại: {result.get('errors')}")
                        except json.JSONDecodeError:
                            logging.error(f"Phản hồi API không phải JSON hợp lệ khi cập nhật mối quan hệ cho thành viên '{member_code}': {response.text}")
                    except requests.exceptions.HTTPError as http_err:
                        logging.error(f"Lỗi HTTP khi cập nhật mối quan hệ cho thành viên '{member_code}': {http_err}. Phản hồi: {response.text}")
                    except requests.exceptions.RequestException as req_err:
                        logging.error(f"Lỗi kết nối khi cập nhật mối quan hệ cho thành viên '{member_code}': {req_err}")

    logging.info("Hoàn tất quá trình cập nhật mối quan hệ thành viên.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cập nhật mối quan hệ thành viên từ dữ liệu trung gian đã lưu.")
    parser.add_argument("--folder", type=str, help="Chỉ định thư mục gia đình cần xử lý (ví dụ: '1'). Nếu không, tất cả các thư mục sẽ được xử lý.")
    parser.add_argument("--limit", type=int, help="Giới hạn số lượng mối quan hệ cần cập nhật cho mục đích debug hoặc test.")
    args = parser.parse_args()
    main(target_folder=args.folder, limit=args.limit)