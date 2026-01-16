# -*- coding: utf-8 -*-
import os
import json
import requests
import logging
from typing import Optional

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cấu hình API
BASE_URL = "http://localhost:8080/api" # Thay đổi nếu API của bạn chạy ở địa chỉ khác
AUTH_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImVlOUx4b24yV0xaMUNvN2g3aFMyTCJ9.eyJodHRwczovL2ZhbWlseXRyZWUuY29tL3JvbGVzIjpbIkFkbWluIl0sImh0dHBzOi8vZmFtaWx5dHJlZS5jb20vZW1haWwiOiJ0aGFvLmhrOTBAZ21haWwuY29tIiwiaHR0cHM6Ly9mYW1pbHl0cmVlLmNvbS9uYW1lIjoidGhhby5oazkwQGdtYWlsLmNvbSIsImlzcyI6Imh0dHBzOi8vZGV2LWc3NnRxMDBnaWN3ZHprM3oudXMuYXV0aDAuY29tLyIsInN1YiI6ImF1dGgwfDY4ZTM4YTVhOTY5MTA3ZWJhYTkxMjU3NyIsImF1ZCI6WyJodHRwOi8vbG9jYWxob3N0OjUwMDAiLCJodHRwczovL2Rldi1nNzZ0cTAwZ2ljd2R6azN6LnVzLmF1dGgwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE3Njg1NTk1NzksImV4cCI6MTc2ODY0NTk3OSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsImF6cCI6InY0alNlNVFSNFVqNmRkb0JCTUhOdGFETkh3djhVelFOIn0.H6z5J4ymNMOzxKii044fvSbT-llLQH6APT-2z0P1vw5jnXzgov9uYCbxZvv4qt76175LjKlamhXWH2FjGSAcey8YUnYGsvWZjlJw8YG3dHkUNnUtaJFXdjgPwA06FatBj4sze4JgfZdNLMsBpvcY2nlHJ6DrV888Xci7c3Ly3XmmTg9KPRU9TuBbSXFHtr2qJTrBmIiEZvaDbJQl5UGudYdNhPc8qPrOK-X2hZWQ1h2e9saMIF1sZH-oOLKerTAny7j89djtXoUgjThKa8OGSCULgHO4YmWZCWCJ6_E2vOUR9KgZvv2EAxar4pKMZHyRBvraPuNtv1mR-5ebvJ1ifg" # Thay thế bằng token xác thực thực tế của bạn

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

OUTPUT_DIR = "output"

# Global map to store member_code (string) -> member_api_id (GUID)
member_code_to_api_id_global_map = {}

def get_family_by_code(family_code: str) -> Optional[str]:
    """
    Kiểm tra xem gia đình có tồn tại không và trả về Family ID nếu có.
    """
    try:
        response = requests.get(f"{BASE_URL}/family/by-code/{family_code}", headers=HEADERS)
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("id"):
                    logging.info(f"Gia đình với mã '{family_code}' đã tồn tại, ID: {result['id']}")
                    return result["id"]
            except json.JSONDecodeError:
                logging.error(f"Phản hồi API không phải JSON hợp lệ khi kiểm tra gia đình '{family_code}': {response.text}")
                return None
        elif response.status_code == 404 or (response.status_code == 400 and "Family with code" in response.text and "not found" in response.text):
            logging.info(f"Gia đình với mã '{family_code}' chưa tồn tại.")
            return None
        else:
            logging.error(f"Lỗi khi kiểm tra gia đình '{family_code}': {response.status_code} - {response.text}")
            return None
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Lỗi HTTP khi kiểm tra gia đình '{family_code}': {http_err}. Phản hồi: {response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Lỗi kết nối khi gọi API kiểm tra gia đình '{family_code}': {req_err}")
        return None

def get_member_by_code(family_id: str, member_code: str) -> Optional[str]:
    """
    Kiểm tra xem thành viên có tồn tại không và trả về Member ID nếu có.
    """
    try:
        response = requests.get(f"{BASE_URL}/member/by-family/{family_id}/by-code/{member_code}", headers=HEADERS)
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("id"):
                    logging.info(f"Thành viên với mã '{member_code}' trong gia đình '{family_id}' đã tồn tại, ID: {result['id']}")
                    return result["id"]
            except json.JSONDecodeError:
                logging.error(f"Phản hồi API không phải JSON hợp lệ khi kiểm tra thành viên '{member_code}' trong gia đình '{family_id}': {response.text}")
                return None
        elif response.status_code == 404:
            logging.info(f"Thành viên với mã '{member_code}' trong gia đình '{family_id}' chưa tồn tại.")
            return None
        else:
            logging.error(f"Lỗi khi kiểm tra thành viên '{member_code}' trong gia đình '{family_id}': {response.status_code} - {response.text}")
            return None
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Lỗi HTTP khi kiểm tra thành viên '{member_code}' trong gia đình '{family_id}': {http_err}. Phản hồi: {response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Lỗi kết nối khi gọi API kiểm tra thành viên '{member_code}' trong gia đình '{family_id}': {req_err}")
        return None

def create_family(folder_name: str, family_data: dict) -> Optional[str]:
    """
    Tạo một gia đình mới thông qua API.
    Trả về Family ID nếu thành công, ngược lại trả về None.
    """
    family_code = f"VNGP-{folder_name}"
    logging.info(f"Đang xử lý gia đình với mã: {family_code}")

    # Bước 1: Kiểm tra xem gia đình đã tồn tại chưa
    existing_family_id = get_family_by_code(family_code)
    if existing_family_id:
        return existing_family_id

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

    try:
        response = requests.post(f"{BASE_URL}/family", headers=HEADERS, json=family_payload)
        response.raise_for_status() # Ném lỗi cho các mã trạng thái HTTP xấu (4xx hoặc 5xx)
        
        try:
            result = response.json()
            if isinstance(result, dict) and result.get("succeeded"):
                family_id = result.get("value")
                logging.info(f"Tạo gia đình '{family_payload['name']}' ({family_code}) thành công với ID: {family_id}")
                return family_id
            else:
                error_details = result.get('errors')
                if isinstance(error_details, str) and len(error_details) == 36 and all(c in "0123456789abcdef-" for c in error_details): # Simple GUID check
                    logging.error(f"Tạo gia đình '{family_payload['name']}' ({family_code}) thất bại. Mã lỗi API: {error_details}. Vui lòng kiểm tra log backend API để biết thêm chi tiết.")
                else:
                    logging.error(f"Tạo gia đình '{family_payload['name']}' ({family_code}) thất bại: {error_details if isinstance(error_details, dict) or isinstance(error_details, list) else response.text}")
                return None
        except json.JSONDecodeError:
            logging.error(f"Phản hồi API không phải JSON hợp lệ khi tạo gia đình '{family_payload['name']}' ({family_code}): {response.text}")
            return None
            
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Lỗi HTTP khi gọi API tạo gia đình '{family_payload['name']}' ({family_code}): {http_err}. Phản hồi: {response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Lỗi kết nối khi gọi API tạo gia đình '{family_payload['name']}' ({family_code}): {req_err}")
        return None

def create_member(family_id: str, folder_name: str, file_name: str, member_data: dict,
                  pending_relationship_updates: list) -> Optional[str]:
    """
    Tạo một thành viên mới thông qua API (Pass 1).
    Trả về Member ID nếu thành công, ngược lại trả về None.
    Thu thập thông tin mối quan hệ để cập nhật ở lượt 2.
    """
    member_code = f"VNGP-{folder_name}-{os.path.splitext(file_name)[0]}"
    logging.info(f"Đang xử lý thành viên với mã: {member_code} cho gia đình ID: {family_id} (Lượt 1 - Tạo)")

    # Kiểm tra các trường bắt buộc và làm sạch dữ liệu
    first_name = member_data.get("firstName")
    last_name = member_data.get("lastName")

    if first_name == "..":
        first_name = None
    if last_name == "..":
        last_name = None
    
    if not first_name or not last_name:
        logging.error(f"Thành viên '{member_code}' thiếu 'firstName' hoặc 'lastName' bắt buộc (hoặc giá trị không hợp lệ). Bỏ qua thành viên này.")
        return None

    # Bước 1: Kiểm tra xem thành viên chính đã tồn tại chưa
    existing_member_id = get_member_by_code(family_id, member_code)
    
    # Bỏ qua children và siblings như yêu cầu mới
    member_data.pop("children", None)
    member_data.pop("siblings", None)

    # Lấy thông tin vợ/chồng từ member_data.get("spouse") hoặc member_data.get("spouses")
    primary_spouse_data = member_data.get("spouse") 
    additional_spouses_list = member_data.get("spouses", [])

    # Ánh xạ giới tính từ tiếng Việt sang tiếng Anh
    gender_map = {
        "Nam": "Male",
        "Nữ": "Female",
        "Chân": "Other" # Thêm ánh xạ cho "Chân"
    }
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
        "isRoot": member_data.get("isRoot", False),
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

    logging.debug(f"Payload thành viên gửi đi: {json.dumps(member_payload, indent=2)}") # Log the payload

    member_id_of_primary_member = existing_member_id
    if not existing_member_id:
        try:
            response = requests.post(f"{BASE_URL}/member", headers=HEADERS, json=member_payload)
            response.raise_for_status()
            result = response.json()
            if result.get("succeeded"):
                member_id_of_primary_member = result.get("value")
                logging.info(f"Tạo thành viên '{member_payload['firstName']} {member_payload['lastName']}' ({member_code}) thành công với ID: {member_id_of_primary_member}")
                member_code_to_api_id_global_map[member_code] = member_id_of_primary_member
            else:
                logging.error(f"Tạo thành viên '{member_payload['firstName']} {member_payload['lastName']}' ({member_code}) thất bại: {result.get('errors')}")
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Lỗi khi gọi API tạo thành viên '{member_payload['firstName']} {member_payload['lastName']}' ({member_code}): {e}")
            return None
    else:
        logging.info(f"Thành viên chính '{member_code}' đã tồn tại, ID: {existing_member_id}. Bỏ qua tạo mới.")
        member_code_to_api_id_global_map[member_code] = existing_member_id
    
    if not member_id_of_primary_member:
        return None

    # Sau khi thành viên chính đã được tạo hoặc tìm thấy, thu thập thông tin quan hệ để cập nhật ở Lượt 2
    relationship_data = {
        "member_api_id": member_id_of_primary_member,
        "member_code": member_code,
        "gender": member_payload.get("gender"), # Giới tính của thành viên chính
        "father_code": member_data.get("father", {}).get("code"), # Lấy code từ đối tượng 'father'
        "mother_code": member_data.get("mother", {}).get("code"), # Lấy code từ đối tượng 'mother'
        "spouse_codes": [] # Sẽ thu thập mã của tất cả vợ/chồng (chính và phụ)
    }
    
    pending_relationship_updates.append(relationship_data)

    # Xử lý các vợ/chồng phụ (luôn tạo mới hoặc kiểm tra tồn tại, và thu thập để cập nhật mối quan hệ)
    if additional_spouses_list:
        logging.info(f"Thành viên {member_code} có {len(additional_spouses_list)} vợ/chồng phụ.")
        for i, spouse_data in enumerate(additional_spouses_list):
            spouse_code_suffix = spouse_data.get("code") or f"SP{i+1}"
            spouse_code = f"{member_code}-{spouse_code_suffix}"
            logging.info(f"Đang xử lý vợ/chồng phụ với mã: {spouse_code}")

            existing_spouse_id = get_member_by_code(family_id, spouse_code)
            spouse_api_id = existing_spouse_id
            
            spouse_first_name = spouse_data.get("firstName", "")
            spouse_last_name = spouse_data.get("lastName", "")
            if spouse_first_name == "..":
                spouse_first_name = None
            if spouse_last_name == "..":
                spouse_last_name = None

            spouse_payload = {
                "lastName": spouse_last_name or None,
                "firstName": spouse_first_name or None,
                "id": None, # Thêm trường ID với giá trị null khi tạo mới spouse
                "code": spouse_code,
                "nickname": spouse_data.get("nickname") or None,
                "dateOfBirth": spouse_data.get("dateOfBirth") or None,
                "dateOfDeath": spouse_data.get("dateOfDeath") or None,
                "placeOfBirth": spouse_data.get("placeOfBirth") or None,
                "placeOfDeath": spouse_data.get("placeOfDeath") or None,
                "phone": spouse_data.get("phone") or None,
                "email": spouse_data.get("email") or None,
                "address": spouse_data.get("address") or None,
                "gender": spouse_data.get("gender") or None,
                "avatarUrl": spouse_data.get("avatarUrl") or None,
                "avatarBase64": spouse_data.get("avatarBase64") or None,
                "occupation": spouse_data.get("occupation") or None,
                "biography": spouse_data.get("biography") or None,
                "familyId": family_id,
                "isRoot": False, 
                "isDeceased": spouse_data.get("isDeceased", False),
                "order": spouse_data.get("order", 0),
                "birthLocationId": spouse_data.get("birthLocationId") or None,
                "deathLocationId": spouse_data.get("deathLocationId") or None,
                "residenceLocationId": spouse_data.get("residenceLocationId") or None,
                "fatherId": None, # Sẽ được cập nhật ở lượt 2
                "motherId": None, # Sẽ được cập nhật ở lượt 2
                "husbandId": None,
                "wifeId": None
            }

            if not existing_spouse_id:
                try:
                    response = requests.post(f"{BASE_URL}/member", headers=HEADERS, json=spouse_payload)
                    response.raise_for_status()
                    result = response.json()
                    if result.get("succeeded"):
                        spouse_api_id = result.get("value")
                        logging.info(f"Tạo vợ/chồng phụ '{spouse_payload['firstName']} {spouse_payload['lastName']}' ({spouse_code}) thành công với ID: {spouse_api_id}")
                        member_code_to_api_id_global_map[spouse_code] = spouse_api_id
                    else:
                        logging.error(f"Tạo vợ/chồng phụ '{spouse_payload['firstName']} {spouse_payload['lastName']}' ({spouse_code}) thất bại: {result.get('errors')}")
                        continue
                except requests.exceptions.RequestException as e:
                    logging.error(f"Lỗi khi gọi API tạo vợ/chồng phụ '{spouse_payload['firstName']} {spouse_payload['lastName']}' ({spouse_code}): {e}")
                    continue
            else:
                logging.info(f"Vợ/chồng phụ '{spouse_code}' đã tồn tại, ID: {existing_spouse_id}. Bỏ qua tạo mới.")
                member_code_to_api_id_global_map[spouse_code] = existing_spouse_id

            if spouse_api_id:
                # Add this spouse's code to the primary member's spouse_codes list
                # Find the primary member's rel_data in pending_relationship_updates
                # Assuming the primary member's rel_data is always the first one appended for this family processing cycle
                for primary_member_rel_data in pending_relationship_updates:
                    if primary_member_rel_data["member_api_id"] == member_id_of_primary_member:
                        primary_member_rel_data["spouse_codes"].append(spouse_code)
                        break

                spouse_relationship_data = {
                    "member_api_id": spouse_api_id,
                    "member_code": spouse_code,
                    "gender": spouse_payload.get("gender"),
                    "father_code": spouse_data.get("father", {}).get("code"), # Lấy code từ đối tượng 'father'
                    "mother_code": spouse_data.get("mother", {}).get("code"), # Lấy code từ đối tượng 'mother'
                    "spouse_codes": [member_code] # Vợ/chồng phụ này kết hôn với thành viên chính
                }
                pending_relationship_updates.append(spouse_relationship_data)

    return member_id_of_primary_member

def main(target_folder: Optional[str] = None, member_limit: int = 0):
    logging.info("Bắt đầu quá trình tích hợp dữ liệu gia đình và thành viên.")
    
    folders_to_process = []
    if target_folder:
        folders_to_process.append(target_folder)
    else:
        folders_to_process = os.listdir(OUTPUT_DIR)

    for folder_name in folders_to_process:
        folder_path = os.path.join(OUTPUT_DIR, folder_name)
        if os.path.isdir(folder_path):
            logging.info(f"Đang xử lý thư mục: {folder_name}")

            # Đọc dữ liệu gia đình từ file family.json nếu có
            data_folder_path = os.path.join(folder_path, "data")
            family_json_path = os.path.join(data_folder_path, "family.json")
            family_data = {}
            if os.path.exists(family_json_path):
                try:
                    with open(family_json_path, 'r', encoding='utf-8') as f:
                        family_data = json.load(f)
                except json.JSONDecodeError as e:
                    logging.error(f"Lỗi đọc file family.json trong thư mục {folder_name}: {e}. Bỏ qua thư mục này.")
                    continue
            
            # Thêm kiểm tra nếu family.json không tồn tại hoặc name empty thì bỏ qua
            family_name = family_data.get("name")
            if not family_name or family_name.strip() == "":
                logging.warning(f"File family.json không tồn tại hoặc trường 'name' trống trong thư mục {folder_name}. Bỏ qua thư mục này.")
                continue

            family_id = create_family(folder_name, family_data)
            if not family_id:
                logging.error(f"Không thể tạo gia đình cho thư mục {folder_name}. Bỏ qua các thành viên trong thư mục này.")
                continue

            pha_he_json_path = os.path.join(data_folder_path, "pha_he.json")
            if os.path.exists(pha_he_json_path):
                try:
                    with open(pha_he_json_path, 'r', encoding='utf-8') as f:
                        pha_he_data = json.load(f)
                        if pha_he_data: # Kiểm tra xem file có dữ liệu không
                            logging.info(f"Tìm thấy và đang sử dụng pha_he.json trong {folder_name}, nhưng bỏ qua xử lý pha_he.json vì hàm xử lý chưa được triển khai.")
                            # process_relationships_from_pha_he(family_id, folder_name, pha_he_data)
                            # continue # Chuyển sang thư mục tiếp theo sau khi xử lý pha_he.json
                        else:
                            logging.info(f"File pha_he.json trong {folder_name} trống rỗng. Chuyển sang xử lý từng file thành viên.")
                except json.JSONDecodeError as e:
                    logging.error(f"Lỗi đọc file pha_he.json trong thư mục {folder_name}: {e}. Chuyển sang xử lý từng file thành viên.")
                except Exception as e:
                    logging.error(f"Lỗi không xác định khi xử lý pha_he.json trong thư mục {folder_name}: {e}. Chuyển sang xử lý từng file thành viên.")

            # --- Xử lý từng file thành viên nếu pha_he.json không tồn tại hoặc trống/lỗi (theo 2 lượt) ---
            logging.info(f"Đang xử lý từng file thành viên trong thư mục {folder_name} (theo 2 lượt).")
            pending_relationship_updates = [] # Danh sách để lưu các cập nhật quan hệ cho Lượt 2

            # Lượt 1: Tạo tất cả thành viên từ các file JSON riêng lẻ
            members_folder_path = os.path.join(data_folder_path, "members") # Assuming members are in 'data/members'
            if os.path.exists(members_folder_path) and os.path.isdir(members_folder_path):
                member_count = 0 # Initialize counter
                for file_name in os.listdir(members_folder_path):
                    if member_limit > 0 and member_count >= member_limit: # Check limit
                        logging.info(f"Đã đạt giới hạn {member_limit} thành viên. Dừng xử lý các thành viên còn lại.")
                        break
                    if file_name.endswith(".json"): # No need to exclude family.json and pha_he.json as it's 'members' folder
                        file_path = os.path.join(members_folder_path, file_name)
                        logging.info(f"Đang xử lý file thành viên: {file_name} (Lượt 1 - Tạo)")
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                member_data = json.load(f)
                            # create_member now also populates pending_relationship_updates
                            created_member_id = create_member(family_id, folder_name, file_name, member_data, pending_relationship_updates)
                            if created_member_id: # Only count if member was successfully created (or found existing)
                                member_count += 1
                        except json.JSONDecodeError as e:
                            logging.error(f"Lỗi đọc file JSON thành viên '{file_name}' trong thư mục {folder_name}: {e}")
                        except Exception as e:
                            logging.error(f"Lỗi không xác định khi xử lý file thành viên '{file_name}' trong thư mục {folder_name}: {e}")
            else:
                logging.warning(f"Thư mục 'members' không tồn tại trong {data_folder_path}. Bỏ qua xử lý các file thành viên riêng lẻ.")
            
            # Lượt 2: Cập nhật mối quan hệ cho các thành viên đã tạo
            logging.info(f"Bắt đầu Lượt 2: Cập nhật mối quan hệ cho các thành viên trong thư mục {folder_name}.")
            for rel_data in pending_relationship_updates:
                member_api_id = rel_data["member_api_id"]
                member_code = rel_data["member_code"]
                update_payload = {"id": member_api_id}

                # Resolve fatherId
                father_code = rel_data.get("father_code")
                if father_code and father_code.strip() != "" and father_code != "null":
                    father_api_id = member_code_to_api_id_global_map.get(father_code)
                    if father_api_id:
                        update_payload["fatherId"] = father_api_id
                    else:
                        logging.warning(f"Không tìm thấy API ID cho cha có mã '{father_code}' của thành viên '{member_code}'.")
                
                # Resolve motherId
                mother_code = rel_data.get("mother_code")
                if mother_code and mother_code.strip() != "" and mother_code != "null":
                    mother_api_id = member_code_to_api_id_global_map.get(mother_code)
                    if mother_api_id:
                        update_payload["motherId"] = mother_api_id
                    else:
                        logging.warning(f"Không tìm thấy API ID cho mẹ có mã '{mother_code}' của thành viên '{member_code}'.")

                # Resolve husbandId / wifeId (spouses)
                if rel_data.get("spouse_codes"):
                    for spouse_code_to_resolve in rel_data["spouse_codes"]:
                        if spouse_code_to_resolve and spouse_code_to_resolve.strip() != "" and spouse_code_to_resolve != "null":
                            spouse_api_id = member_code_to_api_id_global_map.get(spouse_code_to_resolve)
                            if spouse_api_id:
                                # Determine if it's husbandId or wifeId based on the current member's gender
                                if rel_data.get("gender") == "Male":
                                    update_payload["wifeId"] = spouse_api_id
                                elif rel_data.get("gender") == "Female":
                                    update_payload["husbandId"] = spouse_api_id
                                else:
                                    logging.warning(f"Không thể xác định giới tính của thành viên '{member_code}' để liên kết vợ/chồng '{spouse_code_to_resolve}'.")
                            else:
                                logging.warning(f"Không tìm thấy API ID cho vợ/chồng có mã '{spouse_code_to_resolve}' của thành viên '{member_code}'.")


                if len(update_payload) > 1: # Only update if there are relationship fields
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

    logging.info("Hoàn tất quá trình tích hợp dữ liệu.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tích hợp dữ liệu gia đình và thành viên vào API.")
    parser.add_argument("--folder", type=str, help="Chỉ định thư mục gia đình cần xử lý (ví dụ: '1'). Nếu không, tất cả các thư mục sẽ được xử lý.")
    parser.add_argument("--member_limit", type=int, default=0, help="Giới hạn số lượng thành viên được tạo từ mỗi thư mục. Mặc định là 0 (không giới hạn).")
    args = parser.parse_args()
    main(target_folder=args.folder, member_limit=args.member_limit)