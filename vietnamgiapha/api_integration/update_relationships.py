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



def infer_mother_code_from_father_data(father_code: str, current_folder_name: str) -> Optional[str]:
    """
    Suy luận mã của mẹ từ dữ liệu của cha, dựa trên vợ/chồng của cha trong file JSON cục bộ.
    """
    if not father_code or father_code.strip() == "" or father_code == "null":
        return None

    try:
        # Example: GPVN-1-1 -> father_folder_name = "1", father_member_filename = "1"
        parts = father_code.split('-')
        if len(parts) >= 3 and parts[0] == 'GPVN':
            father_folder_name = parts[1]
            father_member_index = parts[2] # Assuming member_filename is just the index

            # Check if the father is in the same folder as the current member
            # This is a simplification; a more robust solution might handle cross-folder fathers
            if father_folder_name == current_folder_name:
                father_member_json_path = os.path.join(
                    OUTPUT_DIR,
                    father_folder_name,
                    "data",
                    "members",
                    f"{father_member_index}.json"
                )

                father_member_data = data_loader.load_json_file(father_member_json_path)
                if father_member_data:
                    father_spouses = []
                    if father_member_data.get("spouse"):
                        father_spouses.append(father_member_data.get("spouse"))
                    if father_member_data.get("spouses"):
                        father_spouses.extend(father_member_data.get("spouses"))

                    for spouse_data in father_spouses:
                        # Assuming the first female spouse is the mother
                        # This might need refinement based on data conventions
                        # Use gender_map to normalize gender from original_member_data
                        gender_map = {
                            "Nam": "Male",
                            "Nữ": "Female",
                            "Chân": "Other"
                        }
                        spouse_gender = spouse_data.get("gender")
                        processed_spouse_gender = gender_map.get(spouse_gender, spouse_gender)

                        if processed_spouse_gender == "Female":
                            inferred_mother_code = spouse_data.get("code")
                            if inferred_mother_code:
                                logger.info(f"Suy luận 'mother_code': '{inferred_mother_code}' từ vợ/chồng của cha '{father_code}'.")
                                return inferred_mother_code
                else:
                    logger.warning(f"Không tìm thấy hoặc không thể tải file JSON của cha tại '{father_member_json_path}'. Không thể suy luận 'mother_code'.")
            else:
                logger.warning(f"Cha '{father_code}' không ở cùng thư mục '{current_folder_name}'. Không hỗ trợ suy luận 'mother_code' cho cha ở thư mục khác.")
        else:
            logger.warning(f"Mã cha '{father_code}' không đúng định dạng 'GPVN-folder-member_index'. Không thể suy luận 'mother_code'.")
    except Exception as e:
        logger.error(f"Lỗi khi suy luận 'mother_code' từ dữ liệu của cha '{father_code}': {e}.")
    return None

def main(target_folder: Optional[str] = None):
    logger.info("Bắt đầu quá trình cập nhật mối quan hệ thành viên.")
    
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
        if os.path.isdir(folder_path):
            logger.info(f"Đang xử lý thư mục: {folder_name}")

            family_code = f"GPVN-{folder_name}"
            current_family_api_id = api_services.get_family_by_code(family_code)
            if not current_family_api_id:
                logger.error(f"Không thể lấy Family ID cho thư mục '{folder_name}'. Bỏ qua cập nhật mối quan hệ.")
                continue

            # Fetch all existing members for this family from the API
            all_fetched_members = api_services.get_members_by_family_id(current_family_api_id)
            if not all_fetched_members:
                logger.warning(f"Không tìm thấy thành viên nào cho gia đình ID '{current_family_api_id}'. Bỏ qua cập nhật mối quan hệ.")
                continue


            
            # Helper to find member_id by member_code from the fetched list
            def get_member_id_by_code(member_code_to_find: str) -> Optional[str]:
                for member in all_fetched_members:
                    if member.get("code") == member_code_to_find:
                        return member.get("id")
                return None

            data_folder_path = os.path.join(folder_path, "data")
            members_source_path = os.path.join(data_folder_path, "members")
            members_processed_output_path = os.path.join(data_folder_path, "members_processed")
            os.makedirs(members_processed_output_path, exist_ok=True) # Ensure output directory exists

            gender_map = {
                "Nam": "Male",
                "Nữ": "Female",
                "Chân": "Other" # Thêm ánh xạ cho "Chân"
            }

            if os.path.isdir(members_source_path):
                logger.info(f"Bắt đầu cập nhật mối quan hệ cho các thành viên trong thư mục {folder_name}.")
                for member_json_filename in sorted(os.listdir(members_source_path)):
                    if member_json_filename.endswith(".json"):
                        member_json_file_path = os.path.join(members_source_path, member_json_filename)
                        
                        original_member_data = data_loader.load_member_data(member_json_file_path)
                        if not original_member_data:
                            logger.error(f"Không thể tải member.json từ '{member_json_file_path}'. Bỏ qua thành viên này.")
                            continue

                        member_code = original_member_data.get("code")
                        if not member_code:
                            logger.error(f"Thành viên từ file '{member_json_filename}' thiếu 'code'. Bỏ qua.")
                            continue

                        member_api_id = get_member_id_by_code(member_code)
                        if not member_api_id:
                            logger.warning(f"Không tìm thấy thành viên với mã '{member_code}' trong API. Bỏ qua cập nhật mối quan hệ.")
                            continue
                        
                        update_payload = {}
                        processed_member_data = original_member_data.copy() # Create a copy to store resolved IDs

                        # Resolve fatherId
                        father_code = (original_member_data.get("father") or {}).get("code")
                        if father_code and father_code.strip() != "" and father_code != "null":
                            father_api_id = get_member_id_by_code(father_code)
                            if father_api_id:
                                update_payload["fatherId"] = father_api_id
                                processed_member_data["fatherId"] = father_api_id # Store in processed data
                            else:
                                logger.warning(f"Không tìm thấy API ID cho cha có mã '{father_code}' của thành viên '{member_code}'.")
                        
                        # Resolve motherId
                        mother_code = (original_member_data.get("mother") or {}).get("code")
                        if not mother_code or mother_code.strip() == "" or mother_code == "null":
                            # Try to infer mother_code from father's data if father_code is present
                            if father_code and father_code.strip() != "" and father_code != "null":
                                inferred_mother_code = infer_mother_code_from_father_data(father_code, folder_name)
                                if inferred_mother_code:
                                    mother_code = inferred_mother_code

                        if mother_code and mother_code.strip() != "" and mother_code != "null":
                            mother_api_id = get_member_id_by_code(mother_code)
                            if mother_api_id:
                                update_payload["motherId"] = mother_api_id
                                processed_member_data["motherId"] = mother_api_id # Store in processed data
                            else:
                                logger.warning(f"Không tìm thấy API ID cho mẹ có mã '{mother_code}' của thành viên '{member_code}'.")

                        # Resolve husbandId / wifeId (spouses)
                        # The original data might have 'spouse' (single) or 'spouses' (list)
                        spouses_to_resolve = []
                        if original_member_data.get("spouse"):
                            spouses_to_resolve.append(original_member_data.get("spouse"))
                        if original_member_data.get("spouses"):
                            spouses_to_resolve.extend(original_member_data.get("spouses"))
                        
                        if spouses_to_resolve:
                            member_gender = original_member_data.get("gender") 
                            processed_member_gender = gender_map.get(member_gender, member_gender)
                            
                            resolved_spouse_id = None
                            for spouse_data in spouses_to_resolve:
                                spouse_code = spouse_data.get("code")
                                if spouse_code and spouse_code.strip() != "" and spouse_code != "null":
                                    current_spouse_api_id = get_member_id_by_code(spouse_code)
                                    if current_spouse_api_id:
                                        # Only assign the first found spouse as primary (API limitation)
                                        if not resolved_spouse_id:
                                            if processed_member_gender == "Male":
                                                update_payload["wifeId"] = current_spouse_api_id
                                                processed_member_data["wifeId"] = current_spouse_api_id
                                            elif processed_member_gender == "Female":
                                                update_payload["husbandId"] = current_spouse_api_id
                                                processed_member_data["husbandId"] = current_spouse_api_id
                                            else:
                                                logger.warning(f"Không thể xác định giới tính của thành viên '{member_code}' để liên kết vợ/chồng '{spouse_code}'. Giới tính đã xử lý: '{processed_member_gender}'")
                                            resolved_spouse_id = current_spouse_api_id
                                        else:
                                            logger.warning(f"Thành viên '{member_code}' có nhiều vợ/chồng được định nghĩa. Chỉ vợ/chồng đầu tiên ('{spouse_code}' được tìm thấy) được gán làm vợ/chồng chính.")
                                    else:
                                        logger.warning(f"Không tìm thấy API ID cho vợ/chồng có mã '{spouse_code}' của thành viên '{member_code}'.")
                        
                        if update_payload:
                            if api_services.update_member_relationships(member_api_id, current_family_api_id, update_payload):
                                logger.info(f"Cập nhật mối quan hệ cho thành viên '{member_code}' thành công.")
                            else:
                                logger.error(f"Cập nhật mối quan hệ cho thành viên '{member_code}' thất bại.")
                        else:
                            logger.info(f"Không có mối quan hệ nào để cập nhật cho thành viên '{member_code}'.")
                        
                        # Save processed member data to members_processed folder
                        processed_member_output_path = os.path.join(members_processed_output_path, member_json_filename)
                        try:
                            with open(processed_member_output_path, 'w', encoding='utf-8') as f:
                                json.dump(processed_member_data, f, ensure_ascii=False, indent=2)
                            logger.info(f"Đã lưu dữ liệu thành viên đã xử lý cho '{member_code}' vào '{processed_member_output_path}'.")
                        except Exception as e:
                            logger.error(f"Lỗi khi lưu dữ liệu thành viên đã xử lý cho '{member_code}': {e}")
            else:
                logger.warning(f"Thư mục 'members' không tồn tại trong {data_folder_path}. Bỏ qua xử lý các file thành viên.")
        else:
            logger.debug(f"Bỏ qua '{folder_name}' vì nó không phải là thư mục.")

    logger.info("Hoàn tất quá trình cập nhật mối quan hệ thành viên.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cập nhật mối quan hệ thành viên từ dữ liệu trung gian đã lưu.")
    parser.add_argument("--folder", type=str, help="Chỉ định thư mục gia đình cần xử lý (ví dụ: '1'). Nếu không, tất cả các thư mục sẽ được xử lý.")
    args = parser.parse_args()
    main(target_folder=args.folder)