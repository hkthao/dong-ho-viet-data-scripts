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

            pending_reverse_updates = [] # Initialize the list to store reverse relationship updates


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
                        
                        is_root_member = original_member_data.get("isRoot", False)

                        update_payload = {}
                        processed_member_data = original_member_data.copy() # Create a copy to store resolved IDs

                        # Resolve fatherId
                        father_code = (original_member_data.get("father") or {}).get("code")
                        if is_root_member: # If it's a root member, they shouldn't have a father
                            father_code = None
                        if father_code and father_code.strip() != "" and father_code != "null":
                            father_api_id = get_member_id_by_code(father_code)
                            if father_api_id:
                                update_payload["fatherId"] = father_api_id
                                processed_member_data["fatherId"] = father_api_id # Store in processed data
                            else:
                                logger.warning(f"Không tìm thấy API ID cho cha có mã '{father_code}' của thành viên '{member_code}'.")
                        
                        # Resolve motherId
                        mother_code = (original_member_data.get("mother") or {}).get("code")
                        if is_root_member: # If it's a root member, they shouldn't have a mother
                            mother_code = None

                        # Infer mother_code if not present but father_code is available
                        if not mother_code and father_code and father_code.strip() != "" and father_code != "null":
                            inferred_mother_code = f"{father_code}-S1"
                            inferred_mother_api_id = None
                            inferred_mother_gender = None

                            for fetched_member in all_fetched_members:
                                if fetched_member.get("code") == inferred_mother_code:
                                    inferred_mother_api_id = fetched_member.get("id")
                                    inferred_mother_gender = fetched_member.get("gender")
                                    break
                            
                            if inferred_mother_api_id and inferred_mother_gender == "Female":
                                mother_code = inferred_mother_code
                                logger.info(f"Đã suy luận mẹ chính '{inferred_mother_code}' cho thành viên '{member_code}' dựa trên vợ của cha '{father_code}'.")

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

                        member_gender = original_member_data.get("gender")
                        processed_member_gender = gender_map.get(member_gender, member_gender)

                        # Simple inference for primary spouse based on naming convention
                        if processed_member_gender == "Male" and member_code:
                            inferred_spouse_code = f"{member_code}-S1"
                            inferred_spouse_member_api_id = None
                            inferred_spouse_gender = None

                            # Find the inferred spouse in all_fetched_members
                            for fetched_member in all_fetched_members:
                                if fetched_member.get("code") == inferred_spouse_code:
                                    inferred_spouse_member_api_id = fetched_member.get("id")
                                    inferred_spouse_gender = fetched_member.get("gender")
                                    break
                            
                            if inferred_spouse_member_api_id and inferred_spouse_gender == "Female":
                                spouses_to_resolve.append({"code": inferred_spouse_code, "id": inferred_spouse_member_api_id, "gender": inferred_spouse_gender})
                                logger.info(f"Đã suy luận vợ chính '{inferred_spouse_code}' cho thành viên '{member_code}' dựa trên quy ước đặt tên.")
                        
                        if original_member_data.get("spouse"):
                            spouses_to_resolve.append(original_member_data.get("spouse"))
                        if original_member_data.get("spouses"):
                            spouses_to_resolve.extend(original_member_data.get("spouses"))
                        
                        member_gender = original_member_data.get("gender") 
                        processed_member_gender = gender_map.get(member_gender, member_gender)

                        resolved_wife_api_id = None
                        resolved_husband_api_id = None

                        if spouses_to_resolve:
                            for spouse_data in spouses_to_resolve:
                                spouse_code = spouse_data.get("code")
                                if spouse_code and spouse_code.strip() != "" and spouse_code != "null":
                                    current_spouse_api_id = get_member_id_by_code(spouse_code)
                                    if current_spouse_api_id:
                                        # Only assign the first found spouse as primary (API limitation)
                                        if processed_member_gender == "Male" and not resolved_wife_api_id:
                                            resolved_wife_api_id = current_spouse_api_id
                                        elif processed_member_gender == "Female" and not resolved_husband_api_id:
                                            resolved_husband_api_id = current_spouse_api_id
                                        else:
                                            logger.warning(f"Thành viên '{member_code}' có nhiều vợ/chồng được định nghĩa. Chỉ vợ/chồng đầu tiên ('{spouse_code}' được tìm thấy) được gán làm vợ/chồng chính.")
                                    else:
                                        logger.warning(f"Không tìm thấy API ID cho vợ/chồng có mã '{spouse_code}' của thành viên '{member_code}'.")


                        

                        
                        # Apply resolved IDs to update_payload
                        if resolved_wife_api_id:
                            update_payload["wifeId"] = resolved_wife_api_id
                            processed_member_data["wifeId"] = resolved_wife_api_id
                            # Queue reverse update for the wife
                            pending_reverse_updates.append({
                                "member_api_id": resolved_wife_api_id,
                                "family_api_id": current_family_api_id,
                                "update_payload": {"husbandId": member_api_id}
                            })
                        
                        if resolved_husband_api_id:
                            update_payload["husbandId"] = resolved_husband_api_id
                            processed_member_data["husbandId"] = resolved_husband_api_id
                            # Queue reverse update for the husband
                            pending_reverse_updates.append({
                                "member_api_id": resolved_husband_api_id,
                                "family_api_id": current_family_api_id,
                                "update_payload": {"wifeId": member_api_id}
                            })
                        
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

            # Process pending reverse relationship updates
            if pending_reverse_updates:
                logger.info(f"Đang xử lý {len(pending_reverse_updates)} cập nhật mối quan hệ ngược lại cho thư mục {folder_name}.")
                for reverse_update_data in pending_reverse_updates:
                    member_api_id_to_update = reverse_update_data["member_api_id"]
                    family_api_id_for_update = reverse_update_data["family_api_id"]
                    update_payload_for_reverse = reverse_update_data["update_payload"]

                    if api_services.update_member_relationships(member_api_id_to_update, family_api_id_for_update, update_payload_for_reverse):
                        logger.info(f"Cập nhật mối quan hệ ngược lại cho thành viên '{member_api_id_to_update}' thành công với payload: {update_payload_for_reverse}.")
                    else:
                        logger.error(f"Cập nhật mối quan hệ ngược lại cho thành viên '{member_api_id_to_update}' thất bại với payload: {update_payload_for_reverse}.")
            else:
                logger.info(f"Không có cập nhật mối quan hệ ngược lại nào để xử lý cho thư mục {folder_name}.")
        else:
            logger.debug(f"Bỏ qua '{folder_name}' vì nó không phải là thư mục.")

    logger.info("Hoàn tất quá trình cập nhật mối quan hệ thành viên.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cập nhật mối quan hệ thành viên từ dữ liệu trung gian đã lưu.")
    parser.add_argument("--folder", type=str, help="Chỉ định thư mục gia đình cần xử lý (ví dụ: '1'). Nếu không, tất cả các thư mục sẽ được xử lý.")
    args = parser.parse_args()
    main(target_folder=args.folder)