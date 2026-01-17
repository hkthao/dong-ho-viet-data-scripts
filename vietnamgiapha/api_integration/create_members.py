import os
import json
import logging
from typing import Optional
import dotenv

from vietnamgiapha.api_integration import api_services
from vietnamgiapha import data_loader

# Load environment variables from .env file
dotenv.load_dotenv()

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OUTPUT_DIR = "output"

# Danh sách các tên gia đình không hợp lệ hoặc giữ chỗ cần bỏ qua
INVALID_FAMILY_NAMES = ["TỘC -","GIA PHẢ TỘC -"]



def main(target_folder: Optional[str] = None, member_limit: int = 0):
    logger.info("Bắt đầu quá trình tạo gia đình và thành viên.")
    
    folders_to_process = []
    if target_folder:
        folders_to_process.append(target_folder)
    else:
        # Lấy danh sách các thư mục con trong OUTPUT_DIR
        try:
            entries = os.listdir(OUTPUT_DIR)
            folders_to_process = [entry for entry in entries if os.path.isdir(os.path.join(OUTPUT_DIR, entry))]
        except FileNotFoundError:
            logger.error(f"Thư mục đầu ra '{OUTPUT_DIR}' không tồn tại.")
            return

    for folder_name in folders_to_process:
        folder_path = os.path.join(OUTPUT_DIR, folder_name)
        if os.path.isdir(folder_path):
            logger.info(f"Đang xử lý thư mục: {folder_name}")

            # Đọc dữ liệu gia đình từ file family.json nếu có
            family_data = data_loader.load_family_data(folder_path)
            if not family_data:
                logger.error(f"Không thể tải family.json từ thư mục {folder_name}. Bỏ qua thư mục này.")
                continue
            
            family_name = family_data.get("name")
            if not family_name or family_name.strip() == "" or family_name.strip() in INVALID_FAMILY_NAMES:
                logger.warning(f"File family.json không tồn tại, trường 'name' trống hoặc chứa tên không hợp lệ ('{family_name}') trong thư mục {folder_name}. Bỏ qua thư mục này.")
                continue

            # Bước 1: Kiểm tra xem gia đình đã tồn tại chưa
            family_code = f"GPVN-{folder_name}"
            existing_family_id = api_services.get_family_by_code(family_code)
            if existing_family_id:
                family_id = existing_family_id
                logger.info(f"Gia đình với mã '{family_code}' đã tồn tại, ID: {family_id}. Bỏ qua tạo mới.")
            else:
                # Bước 2: Nếu chưa tồn tại, tiến hành tạo mới
                family_payload = {
                    "name": family_data.get("name", f"Gia đình {folder_name}"),
                    "code": family_code,
                    "description": family_data.get("description"),
                    "address": family_data.get("address"),
                    "genealogyRecord": family_data.get("genealogyRecord"),
                    "progenitorName": family_data.get("progenitorName"),
                    "familyCovenant": family_data.get("familyCovenant"),
                    "contactInfo": family_data.get("contactInfo"),
                    "avatarBase64": family_data.get("avatarBase64"),
                    "visibility": family_data.get("visibility", "Private"),
                    "managerIds": family_data.get("managerIds", []),
                    "viewerIds": family_data.get("viewerIds", []),
                    "locationId": family_data.get("locationId") if family_data.get("locationId") else None
                }
                family_id = api_services.create_family_api_call(family_payload)
            
            if not family_id:
                logger.error(f"Không thể tạo gia đình cho thư mục {folder_name}. Bỏ qua các thành viên trong thư mục này.")
                continue

            # --- Xử lý từng file thành viên ---
            logger.info(f"Đang xử lý từng file thành viên trong thư mục {folder_name}.")
            
            members_folder_path = os.path.join(folder_path, "data", "members")
            if os.path.isdir(members_folder_path):
                logger.debug(f"Files found in members folder: {os.listdir(members_folder_path)}")
                member_count = 0
                # Ánh xạ giới tính từ tiếng Việt sang tiếng Anh
                gender_map = {
                    "Nam": "Male",
                    "Nữ": "Female",
                    "Chân": "Other"
                }

                for member_json_filename in sorted(os.listdir(members_folder_path)):
                    if member_json_filename.endswith(".json"):
                        if member_limit > 0 and member_count >= member_limit:
                            logger.info(f"Đã đạt giới hạn {member_limit} thành viên. Dừng xử lý các thành viên còn lại.")
                            break
                        
                        member_json_file_path = os.path.join(members_folder_path, member_json_filename)

                        member_data = data_loader.load_member_data(member_json_file_path)
                        if not member_data:
                            logger.error(f"Không thể tải member.json từ '{member_json_file_path}'. Bỏ qua thành viên này.")
                            continue

                        logger.info(f"Đang xử lý thành viên từ file JSON: {member_json_filename}")

                        member_code = member_data.get("code")
                        if not member_code:
                            logger.error(f"Thành viên từ file '{member_json_filename}' thiếu 'code'. Bỏ qua.")
                            continue

                        # Kiểm tra các trường bắt buộc và làm sạch dữ liệu
                        first_name = member_data.get("firstName")
                        last_name = member_data.get("lastName")

                        if first_name == "..":
                            first_name = None
                        if last_name == "..":
                            last_name = None
                        
                        if not first_name or not last_name:
                            logger.error(f"Thành viên '{member_code}' thiếu 'firstName' hoặc 'lastName' bắt buộc (hoặc giá trị không hợp lệ). Bỏ qua thành viên này.")
                            continue

                        # Kiểm tra xem thành viên đã tồn tại chưa
                        existing_member_id = api_services.get_member_by_code(family_id, member_code)
                        if existing_member_id:
                            logger.info(f"Thành viên '{member_code}' đã tồn tại, ID: {existing_member_id}. Bỏ qua tạo mới.")
                            member_count += 1
                            continue

                        # Bỏ qua children và siblings như yêu cầu mới
                        member_data.pop("children", None)
                        member_data.pop("siblings", None)

                        member_gender = member_data.get("gender")
                        processed_gender = gender_map.get(member_gender, member_gender) # Giữ nguyên nếu không tìm thấy trong map

                        member_payload = {
                            "lastName": last_name,
                            "firstName": first_name,
                            "id": None, # Thêm trường ID với giá trị null khi tạo mới
                            "code": member_code,
                            "nickname": member_data.get("nickname") or None,
                            "dateOfBirth": member_data.get("dateOfBirth") or None,
                            "dateOfDeath": member_data.get("dateOfDeath") or None,
                            "placeOfBirth": member_data.get("placeOfBirth") or None,
                            "placeOfDeath": member_data.get("placeOfDeath") or None,
                            "phone": member_data.get("phone") or None,
                            "email": member_data.get("email") or None,
                            "address": member_data.get("address") or None,
                            "gender": processed_gender or None,
                            "avatarUrl": member_data.get("avatarUrl") or None,
                            "avatarBase64": member_data.get("avatarBase64") or None,
                            "occupation": member_data.get("occupation") or None,
                            "biography": member_data.get("biography") or None,
                            "familyId": family_id, 
                            "isRoot": member_code.endswith("-1"), # Set isRoot to True if member_code ends with "-1"
                            "isDeceased": member_data.get("isDeceased", False),
                            "order": member_data.get("order", 0),
                            "birthLocationId": member_data.get("birthLocationId") or None,
                            "deathLocationId": member_data.get("deathLocationId") or None,
                            "residenceLocationId": member_data.get("residenceLocationId") or None,
                            "fatherId": None, # Luôn là None trong lượt tạo đầu tiên
                            "motherId": None, # Luôn là None trong lượt tạo đầu tiên
                            "husbandId": None, # Luôn là None trong lượt tạo đầu tiên
                            "wifeId": None     # Luôn là None trong lượt tạo đầu tiên
                        }

                        created_member_id = api_services.create_member_api_call(family_id, member_payload)
                        if created_member_id:
                            member_count += 1
            else:
                logger.warning(f"Thư mục 'members' không tồn tại trong {folder_path}/data. Bỏ qua xử lý các file thành viên.")
            
        else:
            logger.debug(f"Bỏ qua '{folder_name}' vì nó không phải là thư mục.")

    logger.info("Hoàn tất quá trình tạo gia đình và thành viên.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tạo gia đình và thành viên vào API, lưu dữ liệu mối quan hệ trung gian.")
    parser.add_argument("--folder", type=str, help="Chỉ định thư mục gia đình cần xử lý (ví dụ: '1'). Nếu không, tất cả các thư mục sẽ được xử lý.")
    parser.add_argument("--member_limit", type=int, default=0, help="Giới hạn số lượng thành viên được tạo từ mỗi thư mục. Mặc định là 0 (không giới hạn).")
    args = parser.parse_args()
    main(target_folder=args.folder, member_limit=args.member_limit)
