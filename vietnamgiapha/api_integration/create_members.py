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

# Danh sách các tên gia đình không hợp lệ hoặc giữ chỗ cần bỏ qua
INVALID_FAMILY_NAMES = ["TỘC -","GIA PHẢ TỘC -"]

def load_pha_he_data(pha_he_path: str):
    """
    Tải dữ liệu pha_he.json.
    Trả về nội dung JSON thô hoặc None nếu có lỗi.
    """
    try:
        with open(pha_he_path, 'r', encoding='utf-8') as f:
            pha_he_data = json.load(f)
        logging.info(f"Đã tải và xử lý '{pha_he_path}'.")
        return pha_he_data
    except FileNotFoundError:
        logging.warning(f"Không tìm thấy file pha_he.json tại '{pha_he_path}'.")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Lỗi đọc file JSON pha_he.json tại '{pha_he_path}': {e}.")
        return None
    except Exception as e:
        logging.error(f"Lỗi không xác định khi tải pha_he.json tại '{pha_he_path}': {e}.")
        return None


def get_family_by_code(family_code: str) -> Optional[str]:
    """
    Kiểm tra xem gia đình có tồn tại không và trả về Family ID nếu có.
    """
    try:
        response = requests.get(f"{BASE_URL}/family/by-code/{family_code}", headers=HEADERS)
        if response.status_code == 200:
            try:
                result = response.json()
                logging.debug(f"Phản hồi JSON API cho gia đình '{family_code}': {json.dumps(result, indent=2)}")
                if result.get("id"):
                    logging.info(f"Gia đình với mã '{family_code}' đã tồn tại, ID: {result['id']}")
                    return result["id"]
            except json.JSONDecodeError:
                logging.error(f"Phản hồi API không phải JSON hợp lệ khi kiểm tra gia đình '{family_code}': {response.text}")
                return None
        elif response.status_code == 404:
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


def get_member_by_code(family_id: str, member_code: str, member_code_to_api_id_map: dict) -> Optional[str]:
    """
    Kiểm tra xem thành viên có tồn tại không và trả về Member ID nếu có.
    Ưu tiên kiểm tra trong map cục bộ trước để tránh gọi API lặp lại.
    """
    if member_code in member_code_to_api_id_map:
        return member_code_to_api_id_map[member_code]

    try:
        response = requests.get(f"{BASE_URL}/member/by-family/{family_id}/by-code/{member_code}", headers=HEADERS)
        if response.status_code == 200:
            try:
                result = response.json()
                logging.debug(f"Phản hồi JSON API cho thành viên '{member_code}' trong gia đình '{family_id}': {json.dumps(result, indent=2)}")
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
    family_code = f"GPVN-{folder_name}"
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
        
        logging.debug(f"DEBUG: Checking API response for GUID. Status Code: {response.status_code}, Response Text (raw): '{response.text}', Length: {len(response.text)}")
        
        # Strip surrounding quotes from the response text if present, as some APIs might return GUIDs as '"guid"'
        cleaned_response_text = response.text.strip('"')

        # Check for direct GUID string for 201 Created responses
        if response.status_code == 201 and len(cleaned_response_text) == 36 and all(c in "0123456789abcdef-" for c in cleaned_response_text.lower()):
            family_id = cleaned_response_text
            logging.info(f"Tạo gia đình '{family_payload['name']}' ({family_code}) thành công với ID: {family_id} (từ GUID trực tiếp).")
            return family_id

        try:
            # Then, try to parse as JSON
            result = response.json()
            logging.debug(f"Phản hồi JSON API khi tạo gia đình '{family_payload['name']}': {json.dumps(result, indent=2)}")
            if isinstance(result, dict) and result.get("succeeded"):
                family_id = result.get("value")
                logging.info(f"Tạo gia đình '{family_payload['name']}' ({family_code}) thành công với ID: {family_id}")
                return family_id
            else:
                if isinstance(result, dict):
                    error_details = result.get('errors') or result.get('detail') or result
                    logging.error(f"Tạo gia đình '{family_payload['name']}' ({family_code}) thất bại: {error_details}. Phản hồi thô: {response.text}")
                else:
                    logging.error(f"Tạo gia đình '{family_payload['name']}' ({family_code}) thất bại. Phản hồi API không phải JSON hợp lệ hoặc không có trường 'succeeded': {response.text}")
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

def create_member_and_collect_relationships(family_id: str, member_data: dict,
                  pending_relationship_updates: list, member_code_to_api_id_map: dict) -> Optional[str]:
    """
    Tạo một thành viên mới thông qua API (Pass 1).
    Trả về Member ID nếu thành công, ngược lại trả về None.
    Thu thập thông tin mối quan hệ để cập nhật ở lượt 2.
    """
    member_code = member_data.get("code")
    logging.info(f"Đang xử lý thành viên với mã: {member_code} cho gia đình ID: {family_id} (Lượt 1 - Tạo)")

    # Kiểm tra các trường bắt buộc và làm sạch dữ liệu
    first_name = member_data.get("firstName")
    last_name = member_data.get("lastName")

    if first_name == "..":
        first_name = None
    if last_name == "..":
        last_name = None
    
    if not first_name or not last_name:
        logging.error(f"Thành viên '{member_data.get('code')}' thiếu 'firstName' hoặc 'lastName' bắt buộc (hoặc giá trị không hợp lệ). Bỏ qua thành viên này.")
        return None

    # Bước 1: Kiểm tra xem thành viên chính đã tồn tại chưa
    existing_member_id = get_member_by_code(family_id, member_data.get("code"), member_code_to_api_id_map)
    
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
        "isRoot": member_code == f"GPVN-{family_id}-1", # Set isRoot to True if member_code matches "GPVN-{familyId}-1"
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



    member_id_of_primary_member = existing_member_id
    if not existing_member_id:
        try:
            response = requests.post(f"{BASE_URL}/member", headers=HEADERS, json=member_payload)
            response.raise_for_status()

            # Check for direct GUID string for 201 Created responses
            if response.status_code == 201:
                cleaned_response_text = response.text.strip('"')
                if len(cleaned_response_text) == 36 and all(c in "0123456789abcdef-" for c in cleaned_response_text.lower()):
                    member_id_of_primary_member = cleaned_response_text
                    logging.info(f"Tạo thành viên '{member_payload['firstName']} {member_payload['lastName']}' ({member_data.get('code')}) thành công với ID: {member_id_of_primary_member} (từ GUID trực tiếp).")
                    member_code_to_api_id_map[member_data.get("code")] = member_id_of_primary_member
            
            # If not a direct GUID, try to parse as JSON or handle other 2xx responses
            else:
                try:
                    result = response.json()
                    logging.debug(f"Phản hồi JSON API khi tạo thành viên chính '{member_payload['firstName']} {member_payload['lastName']}': {json.dumps(result, indent=2)}")
                    if result.get("succeeded"):
                        member_id_of_primary_member = result.get("value")
                        logging.info(f"Tạo thành viên '{member_payload['firstName']} {member_payload['lastName']}' ({member_data.get('code')}) thành công với ID: {member_id_of_primary_member}")
                        member_code_to_api_id_map[member_data.get("code")] = member_id_of_primary_member
                    else:
                        logging.error(f"Tạo thành viên '{member_payload['firstName']} {member_payload['lastName']}' ({member_data.get('code')}) thất bại: {result.get('errors')}. Phản hồi thô: {response.text}")
                except json.JSONDecodeError as json_err:
                    logging.error(f"Lỗi khi xử lý phản hồi API tạo thành viên '{member_payload['firstName']} {member_payload['lastName']}' ({member_data.get('code') }): {json_err}. Phản hồi thô: {response.text}")
                except Exception as e:
                    logging.error(f"Lỗi không xác định khi xử lý phản hồi API tạo thành viên '{member_payload['firstName']} {member_payload['lastName']}' ({member_data.get('code') }): {e}. Phản hồi thô: {response.text}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Lỗi khi gọi API tạo thành viên '{member_payload['firstName']} {member_payload['lastName']}' ({member_data.get('code') }): {e}")
            member_id_of_primary_member = None # Ensure it's None on failure    else:
        logging.info(f"Thành viên chính '{member_data.get('code') }' đã tồn tại, ID: {existing_member_id}. Bỏ qua tạo mới.")
        member_code_to_api_id_map[member_data.get("code")] = existing_member_id
    
    if not member_id_of_primary_member:
        return None

    # Sau khi thành viên chính đã được tạo hoặc tìm thấy, thu thập thông tin quan hệ để cập nhật ở Lượt 2
    # Cha/mẹ và vợ/chồng sẽ được xử lý ở lượt cập nhật thứ 2.
    resolved_father_code = (member_data.get("father") or {}).get("code")
    resolved_mother_code = (member_data.get("mother") or {}).get("code")

    # NEW LOGIC FOR MOTHER_CODE INFERENCE
    if resolved_mother_code is None and resolved_father_code:
        # Avoid self-reference for father
        if resolved_father_code == member_code:
            logging.debug(f"Thành viên '{member_code}' là thủy tổ (cha là chính mình). Bỏ qua suy luận mẹ từ vợ/chồng của cha.")
        else:
            # Parse father_code to get folder_name and member_filename
            try:
                # Example: GPVN-1-1 -> folder_name = "1", member_filename = "1"
                parts = resolved_father_code.split('-')
                if len(parts) >= 3 and parts[0] == 'GPVN':
                    father_folder_name = parts[1]
                    father_member_filename = parts[2] # Assuming member_filename is just the index

                    father_member_json_path = os.path.join(
                        OUTPUT_DIR,
                        father_folder_name,
                        "data",
                        "members",
                        f"{father_member_filename}.json"
                    )

                    if os.path.exists(father_member_json_path):
                        with open(father_member_json_path, 'r', encoding='utf-8') as f:
                            father_member_data = json.load(f)

                        father_spouses = father_member_data.get("spouses")
                        if father_spouses and isinstance(father_spouses, list) and len(father_spouses) > 0:
                            # Take the code of the first spouse
                            inferred_mother_code = father_spouses[0].get("code")
                            if inferred_mother_code:
                                resolved_mother_code = inferred_mother_code
                                logging.info(f"Suy luận 'mother_code': '{resolved_mother_code}' cho thành viên '{member_code}' từ người phối ngẫu đầu tiên của cha '{resolved_father_code}'.")
                            else:
                                logging.warning(f"Người phối ngẫu đầu tiên của cha '{resolved_father_code}' không có 'code'. Không thể suy luận 'mother_code' cho thành viên '{member_code}'.")
                        else:
                            logging.warning(f"Cha '{resolved_father_code}' không có thông tin người phối ngẫu (spouses) hoặc danh sách trống. Không thể suy luận 'mother_code' cho thành viên '{member_code}'.")
                    else:
                        logging.warning(f"Không tìm thấy file JSON của cha tại '{father_member_json_path}'. Không thể suy luận 'mother_code' cho thành viên '{member_code}'.")
                else:
                    logging.warning(f"Mã cha '{resolved_father_code}' không đúng định dạng 'GPVN-folder-member_index'. Không thể suy luận 'mother_code' cho thành viên '{member_code}'.")
            except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
                logging.error(f"Lỗi khi đọc file JSON của cha '{resolved_father_code}' để suy luận 'mother_code' cho thành viên '{member_code}': {e}.")

    relationship_data = {
        "member_api_id": member_id_of_primary_member,
        "member_code": member_data.get("code"),
        "gender": member_payload.get("gender"),
        "family_api_id": family_id, # Thêm family_api_id vào đây
        "father_code": resolved_father_code,
        "mother_code": resolved_mother_code,
        "spouse_codes": []
    }
    pending_relationship_updates.append(relationship_data)

    # Xử lý các vợ/chồng phụ (luôn tạo mới hoặc kiểm tra tồn tại, và thu thập để cập nhật mối quan hệ)
    if additional_spouses_list:
        logging.info(f"Thành viên {member_code} có {len(additional_spouses_list)} vợ/chồng phụ.")
        for i, spouse_data in enumerate(additional_spouses_list):
            spouse_code_suffix = spouse_data.get("code") # Should be the full code now from extract_member.py
            if not spouse_code_suffix:
                logging.error(f"Vợ/chồng phụ của thành viên {member_code} thiếu mã code. Bỏ qua.")
                continue
            spouse_code = spouse_code_suffix
            logging.info(f"Đang xử lý vợ/chồng phụ với mã: {spouse_code}")

            existing_spouse_id = get_member_by_code(family_id, spouse_code, member_code_to_api_id_map)
            spouse_api_id = existing_spouse_id
            
            spouse_first_name = spouse_data.get("firstName", "")
            spouse_last_name = spouse_data.get("lastName", "")
            if spouse_first_name == "..":
                spouse_first_name = None
            if spouse_last_name == "..":
                spouse_last_name = None

            spouse_gender = spouse_data.get("gender")
            processed_spouse_gender = gender_map.get(spouse_gender, spouse_gender)

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
                "gender": processed_spouse_gender or None,
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
                    response = requests.post(f"{BASE_URL}/member", headers=HEADERS, json=spouse_payload)
                    response.raise_for_status()
                    spouse_api_id = None

                    # Check for direct GUID string for 201 Created responses for spouses
                    if response.status_code == 201:
                        cleaned_response_text = response.text.strip('"')
                        if len(cleaned_response_text) == 36 and all(c in "0123456789abcdef-" for c in cleaned_response_text.lower()):
                            spouse_api_id = cleaned_response_text
                            logging.info(f"Tạo vợ/chồng phụ '{spouse_payload['firstName']} {spouse_payload['lastName']}' ({spouse_code}) thành công với ID: {spouse_api_id} (từ GUID trực tiếp).")
                            member_code_to_api_id_map[spouse_code] = spouse_api_id
                            # NO MORE 'continue' HERE
                    
                    # If not a direct GUID, try to parse as JSON
                    try:
                        result = response.json()
                        logging.debug(f"Phản hồi JSON API khi tạo vợ/chồng phụ '{spouse_payload['firstName']} {spouse_payload['lastName']}': {json.dumps(result, indent=2)}")
                        if result.get("succeeded"):
                            spouse_api_id = result.get("value")
                            logging.info(f"Tạo vợ/chồng phụ '{spouse_payload['firstName']} {spouse_payload['lastName']}' ({spouse_code}) thành công với ID: {spouse_api_id}")
                            member_code_to_api_id_map[spouse_code] = spouse_api_id
                        else:
                            logging.error(f"Tạo vợ/chồng phụ '{spouse_payload['firstName']} {spouse_payload['lastName']}' ({spouse_code}) thất bại: {result.get('errors')}. Phản hồi thô: {response.text}")
                            # NO MORE 'continue' HERE
                    except json.JSONDecodeError as json_err:
                        logging.error(f"Lỗi khi xử lý phản hồi API tạo vợ/chồng phụ '{spouse_payload['firstName']} {spouse_payload['lastName']}' ({spouse_code}): {json_err}. Phản hồi thô: {response.text}")
                        # NO MORE 'continue' HERE
                    except Exception as e:
                        logging.error(f"Lỗi không xác định khi xử lý phản hồi API tạo vợ/chồng phụ '{spouse_payload['firstName']} {spouse_payload['lastName']}' ({spouse_code}): {e}. Phản hồi thô: {response.text}")
                        # NO MORE 'continue' HERE
            else:
                logging.info(f"Vợ/chồng phụ '{spouse_code}' đã tồn tại, ID: {existing_spouse_id}. Bỏ qua tạo mới.")
                member_code_to_api_id_map[spouse_code] = existing_spouse_id

            if spouse_api_id: # Only proceed if spouse_api_id was successfully obtained
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
                    "father_code": (spouse_data.get("father") or {}).get("code"), # Lấy code từ đối tượng 'father', an toàn với null
                    "mother_code": (spouse_data.get("mother") or {}).get("code"), # Lấy code từ đối tượng 'mother', an toàn với null
                    "spouse_codes": [member_code] # Vợ/chồng phụ này kết hôn với thành viên chính
                }
                logging.debug(f"Đang thêm spouse_relationship_data vào pending_relationship_updates: {json.dumps(spouse_relationship_data, indent=2)}")
                pending_relationship_updates.append(spouse_relationship_data)

    return member_id_of_primary_member

def main(target_folder: Optional[str] = None, member_limit: int = 0):
    logging.info("Bắt đầu quá trình tạo gia đình và thành viên.")
    
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
            if not family_name or family_name.strip() == "" or family_name.strip() in INVALID_FAMILY_NAMES:
                logging.warning(f"File family.json không tồn tại, trường 'name' trống hoặc chứa tên không hợp lệ ('{family_name}') trong thư mục {folder_name}. Bỏ qua thư mục này.")
                continue

            family_id = create_family(folder_name, family_data)
            if not family_id:
                logging.error(f"Không thể tạo gia đình cho thư mục {folder_name}. Bỏ qua các thành viên trong thư mục này.")
                continue

            # --- Xử lý từng file thành viên (Lượt 1 - Tạo) ---
            logging.info(f"Đang xử lý từng file thành viên trong thư mục {folder_name} (Lượt 1 - Tạo).")
            pending_relationship_updates = [] # Danh sách để lưu các cập nhật quan hệ cho Lượt 2
            member_code_to_api_id_family_map = {} # Map cục bộ cho gia đình hiện tại

            members_folder_path = os.path.join(data_folder_path, "members")
            if os.path.isdir(members_folder_path):
                logging.debug(f"Files found in members folder: {os.listdir(members_folder_path)}")
                member_count = 0
                for member_json_filename in sorted(os.listdir(members_folder_path)):
                    if member_json_filename.endswith(".json"):
                        if member_limit > 0 and member_count >= member_limit:
                            logging.info(f"Đã đạt giới hạn {member_limit} thành viên. Dừng xử lý các thành viên còn lại.")
                            break
                        
                        member_json_file_path = os.path.join(members_folder_path, member_json_filename)

                        try:
                            with open(member_json_file_path, 'r', encoding='utf-8') as f:
                                member_data = json.load(f)

                            logging.info(f"Đang xử lý thành viên từ file JSON: {member_json_filename} (Lượt 1 - Tạo)")

                            created_member_id = create_member_and_collect_relationships(
                                family_id,
                                member_data,
                                pending_relationship_updates,
                                member_code_to_api_id_family_map
                            )
                            if created_member_id:
                                member_count += 1
                        except json.JSONDecodeError as e:
                            logging.error(f"Lỗi đọc file JSON thành viên '{member_json_filename}': {e}")
                            continue
                        except Exception as e:
                            logging.error(f"Lỗi không xác định khi đọc file thành viên '{member_json_filename}': {e}")
                            continue
            else:
                logging.warning(f"Thư mục 'members' không tồn tại trong {data_folder_path}. Bỏ qua xử lý các file thành viên.")
            
            # Lưu dữ liệu trung gian cho script cập nhật mối quan hệ
            relationships_file = os.path.join(data_folder_path, "_relationships_to_update.json")
            member_map_file = os.path.join(data_folder_path, "_member_code_map.json")

            # Xóa các file trung gian cũ để đảm bảo dữ liệu mới
            if os.path.exists(relationships_file):
                os.remove(relationships_file)
                logging.info(f"Đã xóa file trung gian cũ: '{relationships_file}'.")
            if os.path.exists(member_map_file):
                os.remove(member_map_file)
                logging.info(f"Đã xóa file trung gian cũ: '{member_map_file}'.")
            # --- END DELETION ---

            try:
                with open(relationships_file, 'w', encoding='utf-8') as f:
                    json.dump(pending_relationship_updates, f, ensure_ascii=False, indent=2)
                logging.debug(f"Nội dung của '{relationships_file}' trước khi lưu: {json.dumps(pending_relationship_updates, indent=2)}")
                logging.info(f"Đã lưu {len(pending_relationship_updates)} mối quan hệ vào '{relationships_file}'.")
                
                with open(member_map_file, 'w', encoding='utf-8') as f:
                    json.dump(member_code_to_api_id_family_map, f, ensure_ascii=False, indent=2)
                logging.info(f"Đã lưu {len(member_code_to_api_id_family_map)} ánh xạ mã thành viên vào '{member_map_file}'.")
            except Exception as e:
                logging.error(f"Lỗi khi lưu dữ liệu trung gian cho thư mục {folder_name}: {e}")

        else:
            logging.debug(f"Bỏ qua '{folder_name}' vì nó không phải là thư mục.")

logging.info("Hoàn tất quá trình tạo gia đình và thành viên.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tạo gia đình và thành viên vào API, lưu dữ liệu mối quan hệ trung gian.")
    parser.add_argument("--folder", type=str, help="Chỉ định thư mục gia đình cần xử lý (ví dụ: '1'). Nếu không, tất cả các thư mục sẽ được xử lý.")
    parser.add_argument("--member_limit", type=int, default=0, help="Giới hạn số lượng thành viên được tạo từ mỗi thư mục. Mặc định là 0 (không giới hạn).")
    args = parser.parse_args()
    main(target_folder=args.folder, member_limit=args.member_limit)
