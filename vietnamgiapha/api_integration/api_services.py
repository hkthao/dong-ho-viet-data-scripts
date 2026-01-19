# -*- coding: utf-8 -*-
import os
import json
import requests
import logging
from typing import Optional
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv(override=True)

# Cấu hình logging
logger = logging.getLogger(__name__)

# Cấu hình API
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080/api") # Lấy từ biến môi trường, mặc định là localhost
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "") # Lấy từ biến môi trường, mặc định là chuỗi rỗng

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

def get_family_by_code(family_code: str) -> Optional[str]:
    """
    Kiểm tra xem gia đình có tồn tại không và trả về Family ID nếu có.
    """
    try:
        response = requests.get(f"{BASE_URL}/family/by-code/{family_code}", headers=HEADERS)
        if response.status_code == 200:
            try:
                result = response.json()
                logger.debug(f"Phản hồi JSON API cho gia đình '{family_code}': {json.dumps(result, indent=2)}")
                if result.get("id"):
                    logger.info(f"Gia đình với mã '{family_code}' đã tồn tại, ID: {result['id']}")
                    return result["id"]
            except json.JSONDecodeError:
                logger.error(f"Phản hồi API không phải JSON hợp lệ khi kiểm tra gia đình '{family_code}': {response.text}")
                return None
        elif response.status_code == 404:
            logger.info(f"Gia đình với mã '{family_code}' chưa tồn tại.")
            return None
        else:
            logger.error(f"Lỗi khi kiểm tra gia đình '{family_code}': {response.status_code} - {response.text}")
            return None
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Lỗi HTTP khi kiểm tra gia đình '{family_code}': {http_err}. Phản hồi: {response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Lỗi kết nối khi gọi API kiểm tra gia đình '{family_code}': {req_err}")
        return None

def create_family_api_call(family_payload: dict) -> Optional[str]:
    """
    Tạo một gia đình mới thông qua API.
    Trả về Family ID nếu thành công, ngược lại trả về None.
    """
    family_code = family_payload.get("code")
    family_name = family_payload.get("name")
    logger.info(f"Đang gọi API tạo gia đình với mã: {family_code}")

    try:
        response = requests.post(f"{BASE_URL}/family", headers=HEADERS, json=family_payload)
        response.raise_for_status() # Ném lỗi cho các mã trạng thái HTTP xấu (4xx hoặc 5xx)
        
        logger.debug(f"DEBUG: Checking API response for GUID. Status Code: {response.status_code}, Response Text (raw): '{response.text}', Length: {len(response.text)}")
        
        # Strip surrounding quotes from the response text if present, as some APIs might return GUIDs as '"guid"'
        cleaned_response_text = response.text.strip('"')

        # Check for direct GUID string for 201 Created responses
        if response.status_code == 201 and len(cleaned_response_text) == 36 and all(c in "0123456789abcdef-" for c in cleaned_response_text.lower()):
            family_id = cleaned_response_text
            logger.info(f"Tạo gia đình '{family_name}' ({family_code}) thành công với ID: {family_id} (từ GUID trực tiếp).")
            return family_id

        try:
            # Then, try to parse as JSON
            result = response.json()
            logger.debug(f"Phản hồi JSON API khi tạo gia đình '{family_name}': {json.dumps(result, indent=2)}")
            if isinstance(result, dict) and result.get("succeeded"):
                family_id = result.get("value")
                logger.info(f"Tạo gia đình '{family_name}' ({family_code}) thành công với ID: {family_id}")
                return family_id
            else:
                if isinstance(result, dict):
                    error_details = result.get('errors') or result.get('detail') or result
                    logger.error(f"Tạo gia đình '{family_name}' ({family_code}) thất bại: {error_details}. Phản hồi thô: {response.text}")
                else:
                    logger.error(f"Tạo gia đình '{family_name}' ({family_code}) thất bại. Phản hồi API không phải JSON hợp lệ hoặc không có trường 'succeeded': {response.text}")
                return None
        except json.JSONDecodeError:
            logger.error(f"Phản hồi API không phải JSON hợp lệ khi tạo gia đình '{family_name}' ({family_code}): {response.text}")
            return None
            
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Lỗi HTTP khi gọi API tạo gia đình '{family_name}' ({family_code}): {http_err}. Phản hồi: {response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Lỗi kết nối khi gọi API tạo gia đình '{family_name}' ({family_code}): {req_err}")
        return None

def update_family_api_call(family_id: str, family_payload: dict) -> bool:
    """
    Cập nhật thông tin gia đình thông qua API.
    Trả về True nếu thành công, ngược lại trả về False.
    """
    family_code = family_payload.get("code")
    family_name = family_payload.get("name")
    logger.info(f"Đang gọi API cập nhật gia đình '{family_name}' (ID: {family_id}, mã: {family_code})")

    try:
        response = requests.put(f"{BASE_URL}/family/{family_id}", headers=HEADERS, json=family_payload)
        response.raise_for_status()

        if response.status_code == 204: # 204 No Content thường được trả về cho PUT/PATCH thành công
            logger.info(f"Cập nhật gia đình '{family_name}' (ID: {family_id}) thành công (204 No Content).")
            return True
        else:
            # API có thể trả về 200 OK với một đối tượng thành công
            try:
                result = response.json()
                if result.get("succeeded"):
                    logger.info(f"Cập nhật gia đình '{family_name}' (ID: {family_id}) thành công.")
                    return True
                else:
                    error_details = result.get('errors') or result.get('detail') or result
                    logger.error(f"Cập nhật gia đình '{family_name}' (ID: {family_id}) thất bại: {error_details}. Phản hồi thô: {response.text}")
                    return False
            except json.JSONDecodeError:
                # Nếu không phải JSON, nhưng mã trạng thái là 2xx, vẫn coi là thành công
                if response.status_code >= 200 and response.status_code < 300:
                    logger.info(f"Cập nhật gia đình '{family_name}' (ID: {family_id}) thành công (không có JSON phản hồi).")
                    return True
                else:
                    logger.error(f"Phản hồi API không phải JSON hợp lệ khi cập nhật gia đình '{family_name}' (ID: {family_id}): {response.text}")
                    return False
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Lỗi HTTP khi gọi API cập nhật gia đình '{family_name}' (ID: {family_id}): {http_err}. Phản hồi: {response.text}")
        return False
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Lỗi kết nối khi gọi API cập nhật gia đình '{family_name}' (ID: {family_id}): {req_err}")
        return False

def fix_family_relationships_api_call(family_id: str) -> bool:
    """
    Sửa lỗi quan hệ trong gia đình thông qua API.
    Trả về True nếu thành công, ngược lại trả về False.
    """
    logger.info(f"Đang gọi API sửa lỗi quan hệ cho gia đình ID: {family_id}")
    try:
        response = requests.post(f"{BASE_URL}/family/{family_id}/fix-relationships", headers=HEADERS)
        response.raise_for_status() # Ném lỗi cho các mã trạng thái HTTP xấu (4xx hoặc 5xx)

        if response.status_code == 204:
            logger.info(f"Sửa lỗi quan hệ cho gia đình ID: {family_id} thành công (204 No Content).")
            return True
        elif response.status_code == 200: # Some APIs might return 200 with success message
            logger.info(f"Sửa lỗi quan hệ cho gia đình ID: {family_id} thành công (200 OK).")
            return True
        else:
            logger.error(f"Sửa lỗi quan hệ cho gia đình ID: {family_id} thất bại: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Lỗi HTTP khi gọi API sửa lỗi quan hệ cho gia đình ID: {family_id}: {http_err}. Phản hồi: {response.text}")
        return False
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Lỗi kết nối khi gọi API sửa lỗi quan hệ cho gia đình ID: {family_id}: {req_err}")
        return False

def recalculate_family_stats_api_call(family_id: str) -> bool:
    """
    Tính toán lại thống kê gia đình thông qua API.
    Trả về True nếu thành công, ngược lại trả về False.
    """
    logger.info(f"Đang gọi API tính toán lại thống kê cho gia đình ID: {family_id}")
    try:
        response = requests.post(f"{BASE_URL}/family/{family_id}/recalculate-stats", headers=HEADERS)
        response.raise_for_status() # Ném lỗi cho các mã trạng thái HTTP xấu (4xx hoặc 5xx)

        if response.status_code == 200: # Expected 200 OK for success
            logger.info(f"Tính toán lại thống kê cho gia đình ID: {family_id} thành công (200 OK).")
            # Optionally parse response for updated stats if needed, but for now, just success confirmation
            return True
        else:
            logger.error(f"Tính toán lại thống kê cho gia đình ID: {family_id} thất bại: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Lỗi HTTP khi gọi API tính toán lại thống kê cho gia đình ID: {family_id}: {http_err}. Phản hồi: {response.text}")
        return False
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Lỗi kết nối khi gọi API tính toán lại thống kê cho gia đình ID: {family_id}: {req_err}")
        return False


def get_member_by_code(family_id: str, member_code: str) -> Optional[str]:
    """
    Kiểm tra xem thành viên có tồn tại không và trả về Member ID nếu có.
    """
    try:
        response = requests.get(f"{BASE_URL}/member/by-family/{family_id}/by-code/{member_code}", headers=HEADERS)
        if response.status_code == 200:
            try:
                result = response.json()
                logger.debug(f"Phản hồi JSON API cho thành viên '{member_code}' trong gia đình '{family_id}': {json.dumps(result, indent=2)}")
                if result.get("id"):
                    logger.info(f"Thành viên với mã '{member_code}' trong gia đình '{family_id}' đã tồn tại, ID: {result['id']}")
                    return result["id"]
            except json.JSONDecodeError:
                logger.error(f"Phản hồi API không phải JSON hợp lệ khi kiểm tra thành viên '{member_code}' trong gia đình '{family_id}': {response.text}")
                return None
        elif response.status_code == 404 or (response.status_code == 400 and "not found" in response.text.lower()):
            logger.info(f"Thành viên với mã '{member_code}' trong gia đình '{family_id}' chưa tồn tại.")
            return None
        else:
            logger.error(f"Lỗi khi kiểm tra thành viên '{member_code}' trong gia đình '{family_id}': {response.status_code} - {response.text}")
            return None
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Lỗi HTTP khi kiểm tra thành viên '{member_code}' trong gia đình '{family_id}': {http_err}. Phản hồi: {response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Lỗi kết nối khi gọi API kiểm tra thành viên '{member_code}' trong gia đình '{family_id}': {req_err}")
        return None

def create_member_api_call(family_id: str, member_payload: dict) -> Optional[str]:
    """
    Tạo một thành viên mới thông qua API.
    Trả về Member ID nếu thành công, ngược lại trả về None.
    """
    member_code = member_payload.get("code")
    member_name = f"{member_payload.get('firstName')} {member_payload.get('lastName')}"
    logger.info(f"Đang gọi API tạo thành viên '{member_name}' với mã: {member_code} cho gia đình ID: {family_id}")

    try:
        response = requests.post(f"{BASE_URL}/member", headers=HEADERS, json=member_payload)
        response.raise_for_status()

        # Check for direct GUID string for 201 Created responses
        if response.status_code == 201:
            cleaned_response_text = response.text.strip('"')
            if len(cleaned_response_text) == 36 and all(c in "0123456789abcdef-" for c in cleaned_response_text.lower()):
                member_id = cleaned_response_text
                logger.info(f"Tạo thành viên '{member_name}' ({member_code}) thành công với ID: {member_id} (từ GUID trực tiếp).")
                return member_id
        
        # If not a direct GUID, try to parse as JSON or handle other 2xx responses
        try:
            result = response.json()
            logger.debug(f"Phản hồi JSON API khi tạo thành viên '{member_name}': {json.dumps(result, indent=2)}")
            if result.get("succeeded"):
                member_id = result.get("value")
                logger.info(f"Tạo thành viên '{member_name}' ({member_code}) thành công với ID: {member_id}")
                return member_id
            else:
                logger.error(f"Tạo thành viên '{member_name}' ({member_code}) thất bại: {result.get('errors')}. Phản hồi thô: {response.text}")
        except json.JSONDecodeError as json_err:
            logger.error(f"Lỗi khi xử lý phản hồi API tạo thành viên '{member_name}' ({member_code}): {json_err}. Phản hồi thô: {response.text}")
        except Exception as e:
            logger.error(f"Lỗi không xác định khi xử lý phản hồi API tạo thành viên '{member_name}' ({member_code}): {e}. Phản hồi thô: {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi khi gọi API tạo thành viên '{member_name}' ({member_code}): {e}")
    
    return None

def get_members_by_family_id(family_id: str) -> Optional[list]:
    """
    Lấy danh sách tất cả các thành viên thuộc về một gia đình cụ thể dựa trên familyId.
    Trả về một list các dict thành viên nếu thành công, ngược lại trả về None.
    """
    try:
        response = requests.get(f"{BASE_URL}/member/by-family/{family_id}", headers=HEADERS)
        if response.status_code == 200:
            try:
                members = response.json()
                logger.info(f"Đã lấy thành công {len(members)} thành viên cho gia đình ID: {family_id}.")
                return members
            except json.JSONDecodeError:
                logger.error(f"Phản hồi API không phải JSON hợp lệ khi lấy thành viên theo familyId '{family_id}': {response.text}")
                return None
        else:
            logger.error(f"Lỗi khi lấy thành viên theo familyId '{family_id}': {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Lỗi kết nối khi gọi API lấy thành viên theo familyId '{family_id}': {req_err}")
        return None

def update_member_relationships(member_id: str, family_id: str, update_payload: dict) -> bool:
    """
    Cập nhật mối quan hệ cho một thành viên thông qua API.
    Trả về True nếu thành công, ngược lại trả về False.
    """
    try:
        request_body = {
            "memberId": member_id,
            "familyId": family_id,
            **update_payload
        }
        logger.debug(f"Đang gửi request_body cập nhật mối quan hệ cho thành viên '{member_id}': {json.dumps(request_body, indent=2)}")
        response = requests.put(f"{BASE_URL}/member/{member_id}/relationships", headers=HEADERS, json=request_body)
        response.raise_for_status()

        if response.status_code == 204:
            logger.info(f"Cập nhật mối quan hệ cho thành viên '{member_id}' thành công (204 No Content).")
            return True
        else:
            try:
                result = response.json()
                if result.get("succeeded"):
                    logger.info(f"Cập nhật mối quan hệ cho thành viên '{member_id}' thành công.")
                    return True
                else:
                    logger.error(f"Cập nhật mối quan hệ cho thành viên '{member_id}' thất bại: {result.get('errors')}. Phản hồi thô: {response.text}")
                    return False
            except json.JSONDecodeError:
                logger.error(f"Phản hồi API không phải JSON hợp lệ khi cập nhật mối quan hệ cho thành viên '{member_id}': {response.text}")
                return False
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Lỗi HTTP khi cập nhật mối quan hệ cho thành viên '{member_id}': {http_err}. Phản hồi: {response.text}")
        return False
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Lỗi kết nối khi gọi API cập nhật mối quan hệ cho thành viên '{member_id}': {req_err}")
        return False