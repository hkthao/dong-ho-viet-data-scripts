import os
import logging
from typing import Optional
import dotenv
import argparse

from vietnamgiapha.api_integration import api_services
from vietnamgiapha import data_loader

# Load environment variables
dotenv.load_dotenv()

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OUTPUT_DIR = "output"
INVALID_FAMILY_NAMES = ["TỘC -", "GIA PHẢ TỘC -"]

def main(target_folder: Optional[str] = None, member_limit: int = 0):
    logger.info("Bắt đầu quá trình tạo gia đình và thành viên.")
    
    gender_map = {
        "Nam": "Male",
        "Nữ": "Female",
    }

    member_code_to_id_map = {}

    folders_to_process = []
    if target_folder:
        folders_to_process.append(target_folder)
    else:
        try:
            entries = os.listdir(OUTPUT_DIR)
            folders_to_process = [entry for entry in entries if os.path.isdir(os.path.join(OUTPUT_DIR, entry))]
        except FileNotFoundError:
            logger.error(f"Thư mục đầu ra '{OUTPUT_DIR}' không tồn tại.")
            return

    for folder_name in folders_to_process:
        folder_path = os.path.join(OUTPUT_DIR, folder_name)
        logger.info(f"Đang xử lý thư mục: {folder_name}")

        # Kiểm tra xem thư mục 'members' có file nào không
        members_folder_path = os.path.join(folder_path, "data", "members")
        if not os.path.isdir(members_folder_path):
            logger.warning(f"Thư mục 'members' không tồn tại trong {folder_path}. Bỏ qua việc tạo gia đình này.")
            continue
        
        member_files = [f for f in os.listdir(members_folder_path) if f.endswith(".json")]
        if not member_files:
            logger.warning(f"Thư mục 'members' trong {folder_path} không chứa file thành viên nào. Bỏ qua việc tạo gia đình này.")
            continue

        family_data = data_loader.load_family_data(folder_path)
        if not family_data:
            logger.error(f"Không thể tải family.json từ thư mục {folder_name}. Bỏ qua.")
            continue
        
        family_name = family_data.get("name")
        if not family_name or family_name.strip() == "" or family_name.strip() in INVALID_FAMILY_NAMES:
            logger.warning(f"Tên gia đình không hợp lệ trong {folder_name}. Bỏ qua.")
            continue

        # Bước 1 & 2: Tạo hoặc lấy Family ID
        family_code = f"GPVN-{folder_name}"
        existing_family_id = api_services.get_family_by_code(family_code)
        logger.debug(f"Kết quả kiểm tra gia đình hiện có cho mã '{family_code}': ID = {existing_family_id}")
        
        family_id = None
        family_payload = {
            "name": family_name,
            "code": family_code,
            "description": family_data.get("description"),
            "address": family_data.get("address"),
            "visibility": family_data.get("visibility", "Public"),
            "genealogyRecord": family_data.get("genealogyRecord"),
            "progenitorName": family_data.get("progenitorName"),
            "familyCovenant": family_data.get("familyCovenant"),
            "contactInfo": family_data.get("contactInfo")
        }

        if existing_family_id:
            family_id = existing_family_id
            logger.info(f"Gia đình '{family_code}' đã tồn tại, ID: {family_id}. Đang cập nhật thông tin.")
            family_payload["id"] = family_id # Add the ID to the payload for update
            if not api_services.update_family_api_call(family_id, family_payload):
                logger.error(f"Không thể cập nhật thông tin cho gia đình '{family_code}'. Bỏ qua.")
                continue
        else:
            family_id = api_services.create_family_api_call(family_payload)
        
        if not family_id:
            logger.error(f"Không thể tạo hoặc cập nhật gia đình '{family_code}'. Bỏ qua.")
            continue

        # --- Xử lý thành viên ---
        members_folder_path = os.path.join(folder_path, "data", "members")
        if not os.path.isdir(members_folder_path):
            logger.warning(f"Thư mục 'members' không tồn tại trong {folder_path}")
            continue

        member_count = 0
        for member_json_filename in sorted(os.listdir(members_folder_path)):
            if not member_json_filename.endswith(".json"):
                continue

            if member_limit > 0 and member_count >= member_limit:
                break
            
            member_json_file_path = os.path.join(members_folder_path, member_json_filename)
            member_data = data_loader.load_member_data(member_json_file_path)
            
            if not member_data: continue

            member_code = member_data.get("code")
            first_name = member_data.get("firstName")
            last_name = member_data.get("lastName")

            # Làm sạch dữ liệu tên
            if first_name == "..": first_name = None
            if last_name == "..": last_name = None

            if not member_code or not first_name or not last_name:
                logger.error(f"Thành viên {member_json_filename} thiếu thông tin bắt buộc. Bỏ qua.")
                continue

            # --- 1. Xử lý Vợ/Chồng trước ---
            spouses_data = member_data.get("spouses", [])
            for spouse_data in spouses_data:
                s_code = spouse_data.get("code")
                if not s_code: continue

                if s_code not in member_code_to_id_map:
                    # Kiểm tra API nếu map cục bộ chưa có
                    existing_s_id = api_services.get_member_by_code(family_id, s_code)
                    if existing_s_id:
                        member_code_to_id_map[s_code] = existing_s_id
                    else:
                        # Tạo vợ/chồng mới
                        s_fn = spouse_data.get("firstName")
                        s_ln = spouse_data.get("lastName")
                        if s_fn == "..": s_fn = None
                        if s_ln == "..": s_ln = None
                        
                        if s_fn and s_ln:
                            s_payload = {
                                "lastName": s_ln,
                                "firstName": s_fn,
                                "code": s_code,
                                "gender": gender_map.get(spouse_data.get("gender"), "Other"),
                                "familyId": family_id,
                                "isRoot": False
                            }
                            new_s_id = api_services.create_member_api_call(family_id, s_payload)
                            if new_s_id:
                                member_code_to_id_map[s_code] = new_s_id

            # --- 2. Xử lý thành viên chính ---
            if member_code in member_code_to_id_map:
                logger.info(f"Thành viên '{member_code}' đã tồn tại.")
                member_count += 1
                continue

            existing_id = api_services.get_member_by_code(family_id, member_code)
            if existing_id:
                member_code_to_id_map[member_code] = existing_id
                member_count += 1
                continue

            # Tạo Payload thành viên chính
            member_payload = {
                "lastName": last_name,
                "firstName": first_name,
                "code": member_code,
                "nickname": member_data.get("nickname"),
                "gender": gender_map.get(member_data.get("gender"), "Other"),
                "familyId": family_id,
                "isRoot": member_code.endswith("-1"),
                "isDeceased": member_data.get("isDeceased", False),
                "biography": member_data.get("biography"),
                "fatherId": None, "motherId": None, "husbandId": None, "wifeId": None # Lượt 1 để None
            }

            created_id = api_services.create_member_api_call(family_id, member_payload)
            if created_id:
                member_code_to_id_map[member_code] = created_id
                member_count += 1
        
        # Sau khi xử lý tất cả thành viên, gọi API sửa lỗi quan hệ và tính toán lại thống kê
        logger.info(f"Hoàn tất xử lý thành viên cho gia đình '{family_code}'. Đang gọi API sửa lỗi quan hệ và tính toán lại thống kê.")
        
        if api_services.fix_family_relationships_api_call(family_id):
            logger.info(f"API sửa lỗi quan hệ cho gia đình '{family_code}' đã gọi thành công.")
        else:
            logger.error(f"API sửa lỗi quan hệ cho gia đình '{family_code}' thất bại.")

        if api_services.recalculate_family_stats_api_call(family_id):
            logger.info(f"API tính toán lại thống kê cho gia đình '{family_code}' đã gọi thành công.")
        else:
            logger.error(f"API tính toán lại thống kê cho gia đình '{family_code}' thất bại.")

    logger.info("Hoàn tất quá trình.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str)
    parser.add_argument("--member_limit", type=int, default=0)
    args = parser.parse_args()
    main(target_folder=args.folder, member_limit=args.member_limit)