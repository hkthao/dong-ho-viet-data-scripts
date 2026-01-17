# -*- coding: utf-8 -*-
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

def load_json_file(file_path: str) -> Optional[dict]:
    """
    Tải dữ liệu từ một file JSON.
    Trả về nội dung JSON thô hoặc None nếu có lỗi.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Đã tải và xử lý '{file_path}'.")
        return data
    except FileNotFoundError:
        logger.warning(f"Không tìm thấy file tại '{file_path}'.")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Lỗi đọc file JSON tại '{file_path}': {e}.")
        return None
    except Exception as e:
        logger.error(f"Lỗi không xác định khi tải file JSON tại '{file_path}': {e}.")
        return None

def load_pha_he_data(pha_he_path: str) -> Optional[dict]:
    """
    Tải dữ liệu pha_he.json.
    """
    return load_json_file(pha_he_path)

def load_family_data(folder_path: str) -> Optional[dict]:
    """
    Tải dữ liệu gia đình từ family.json trong đường dẫn thư mục.
    """
    family_json_path = os.path.join(folder_path, "data", "family.json")
    return load_json_file(family_json_path)

def load_member_data(member_json_file_path: str) -> Optional[dict]:
    """
    Tải dữ liệu thành viên từ file JSON cụ thể.
    """
    return load_json_file(member_json_file_path)
