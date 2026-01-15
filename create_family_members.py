import requests
import json
import os
import argparse
import glob
import time
import sys
import traceback # Keep sys for file=sys.stderr

BASE_URL = "http://localhost:8080/api" # Assuming the API is running locally
ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImVlOUx4b24yV0xaMUNvN2g3aFMyTCJ9.eyJodHRwczovL2ZhbWlseXRyZWUuY29tL3JvbGVzIjpbIkFkbWluIl0sImh0dHBzOi8vZmFtaWx5dHJlZS5jb20vZW1haWwiOiJ0aGFvLmhrOTBAZ21haWwuY29tIiwiaHR0cHM6Ly9mYW1pbHl0cmVlLmNvbS9uYW1lIjoidGhhby5oazkwQGdtYWlsLmNvbSIsImlzcyI6Imh0dHBzOi8vZGV2LWc3NnRxMDBnaWN3ZHprM3oudXMuYXV0aDAuY29tLyIsInN1YiI6ImF1dGgwfDY4ZTM4YTVhOTY5MTA3ZWJhYTkxMjU3NyIsImF1ZCI6WyJodHRwOi8vbG9jYWxob3N0OjUwMDAiLCJodHRwczovL2Rldi1nNzZ0cTAwZ2ljd2R6azN6LnVzLmF1dGgwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE3Njg0MTAwOTQsImV4cCI6MTc2ODQ5NjQ5NCwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsImF6cCI6InY0alNlNVFSNFVqNmRkb0JCTUhOdGFETkh3djhVelFOIn0.YrKqrCSa1J7N02eQfQvVd_TEMLCe0MUp8vEdJx85yEgau1V_4BPfGPAaMmn5T5VgXvtuB1GiKYUo_VcOhaw0VModI8ewRtBvLLyc7dGFfXpwbXYS3AyuWOmhZQg6TqZxIssxVXOMi7qYuIkOp9xceXabUMr4D3TLGMKO0U7AlRXUgtCkGqw1ERiM4mAQri40RKF0zpN0mJb3bFQkk-igS0lBMZo7l8kWd7sguAlpeMrC95yUmOfvCOCbpBULhn0-Yb1z0nEaCgcUJ02qIdCLgbez42tmNmQXeva2MVUmCREdt2r_TqlbclWJRzVZiEwHy6e6_5Hn1X6iDEpKyXB-TA"

def get_member(member_id):
    url = f"{BASE_URL}/member/{member_id}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi lấy thông tin thành viên {member_id}: {e}", file=sys.stderr)
        return None

def update_member(member_id, member_data):
    url = f"{BASE_URL}/member/{member_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    try:
        response = requests.put(url, headers=headers, json=member_data)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi cập nhật thành viên {member_id}: {e}", file=sys.stderr)
        print(f"Phản hồi lỗi: {response.text}", file=sys.stderr)
        return False

def create_family(family_data):
    url = f"{BASE_URL}/family"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    try:
        response = requests.post(url, headers=headers, json=family_data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()["value"]
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi tạo gia đình: {e}", file=sys.stderr)
        if hasattr(response, 'text'):
            print(f"Phản hồi lỗi: {response.text}", file=sys.stderr)
        return None

def create_member(member_data):
    url = f"{BASE_URL}/member"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    # Wrap member_data in a 'command' object
    payload = member_data
    print(f"DEBUG: Sending payload to /api/member: {json.dumps(payload, ensure_ascii=False, indent=2)}", file=sys.stderr)
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        print(f"DEBUG: API /member response status: {response.status_code}", file=sys.stderr)
        print(f"DEBUG: API /member raw response: {response.text}", file=sys.stderr)
        try:
            response_json = response.json()
            if isinstance(response_json, dict) and "value" in response_json:
                return response_json["value"]
            elif isinstance(response_json, str): # If API returns GUID as a string directly
                return response_json
            else: # Fallback for unexpected JSON structure
                print(f"Cảnh báo: Phản hồi API /member không chứa khóa 'value' hoặc có định dạng không mong đợi: {response.text}", file=sys.stderr)
                return None
        except json.JSONDecodeError:
            print(f"Lỗi: Không thể phân tích cú pháp JSON từ phản hồi API /member: {response.text}", file=sys.stderr)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi tạo thành viên: {e}", file=sys.stderr)
        if hasattr(response, 'text'):
            print(f"Phản hồi lỗi: {response.text}", file=sys.stderr)
        return None

def get_family_by_code(family_code):
    url = f"{BASE_URL}/family/by-code/{family_code}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json() # Direct return of FamilyDto object

    except requests.exceptions.RequestException as e:
        if hasattr(response, 'status_code'):
            if response.status_code == 404:
                return None # Family not found
            else:
                try:
                    error_response = response.json()
                    if not error_response.get("succeeded", True): # Check if API explicitly says not succeeded
                        print(f"Lỗi API khi lấy thông tin gia đình bằng code {family_code}: {error_response.get('errors')}", file=sys.stderr)
                        return None
                except json.JSONDecodeError:
                    pass # Not a JSON error, proceed with generic error message
        print(f"Lỗi khi lấy thông tin gia đình bằng code {family_code}: {e}", file=sys.stderr)
        if hasattr(response, 'text'):
            print(f"Phản hồi lỗi: {response.text}", file=sys.stderr)
        return None

def get_member_by_family_id_and_code(family_id, member_code):
    url = f"{BASE_URL}/member/by-family/{family_id}/by-code/{member_code}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json() # Returns the full MemberDto object
    except requests.exceptions.RequestException as e:
        if hasattr(response, 'status_code'):
            if response.status_code == 404: # This is the expected "not found" status
                return None
            elif response.status_code == 400: # Handle 400 Bad Request
                try:
                    error_response = response.json()
                    if "detail" in error_response and "not found" in error_response["detail"].lower():
                        return None # Treat as "not found" if the message indicates it
                except json.JSONDecodeError:
                    pass # Not a JSON error, proceed with generic error message
        print(f"Lỗi khi lấy thông tin thành viên bằng family ID '{family_id}' và code '{member_code}': {e}", file=sys.stderr)
        if hasattr(response, 'text'):
            print(f"Phản hồi lỗi: {response.text}", file=sys.stderr)
        return None

def parse_name(full_name):
    full_name = str(full_name).strip() # Ensure it's a string and trim whitespace
    parts = full_name.split()
    
    last_name = ""
    first_name = ""

    if len(parts) > 1:
        first_name = parts[-1]
        last_name = " ".join(parts[:-1])
    elif len(parts) == 1:
        # If only one word, treat it as first name, and use a placeholder for last name
        # Or, treat it as last name and use a placeholder for first name
        # Given Vietnamese names, often the last part is the given name.
        first_name = parts[0]
        last_name = "Unknown" # Or handle as per specific convention
    else: # Empty string
        first_name = "Unknown"
        last_name = "Unknown"
            
    # Ensure both are non-empty
    if not last_name:
        last_name = "Chưa xác định" # Hoặc xử lý theo quy ước cụ thể
    if not first_name:
        first_name = "Chưa xác định"
            
    return last_name, first_name

import re

def format_date_for_api(date_string):
    if date_string is None or date_string == "null" or date_string == "":
        return None
    
    # Check for YYYY-MM-DD format
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_string):
        return f"{date_string}T00:00:00Z"
    
    # Check for YYYY-01-01 format (meaning only year is known)
    if re.match(r"^\d{4}-01-01$", date_string):
        return f"{date_string}T00:00:00Z" # This is already YYYY-MM-DDT00:00:00Z

    # If only year is provided (e.g., "1960"), format as YYYY-01-01
    if re.match(r"^\d{4}$", date_string):
        return f"{date_string}-01-01T00:00:00Z"

    # Fallback for unexpected formats, return None to avoid API errors
    return None

def main():
    parser = argparse.ArgumentParser(description="Tạo gia đình và thành viên từ dữ liệu JSON.")
    parser.add_argument("--folder_name", required=True, help="Tên thư mục chứa dữ liệu JSON (ví dụ: 1691). Đường dẫn đầy đủ sẽ là output/{folder_name}/data.")
    parser.add_argument("--family_id", help="ID gia đình hiện có (nếu không cung cấp, một gia đình mới sẽ được tạo).")
    parser.add_argument("--limit", type=int, default=0, help="Giới hạn số lượng thành viên sẽ được xử lý (0 = không giới hạn).")
    
    args = parser.parse_args()

    folder_name = args.folder_name
    data_dir = os.path.join("output", folder_name, "data")
    
    local_family_identifier = args.family_id if args.family_id else folder_name # Use folder_name if family_id is not provided
    api_family_guid = None # This will be the actual GUID from the API

    # Construct the family code
    family_code_to_check = f"VNGP-{local_family_identifier}" if local_family_identifier else "VNGP-TEMP"

    # 1. Kiểm tra gia đình đã tồn tại chưa
    print(f"Đang kiểm tra xem gia đình với mã '{family_code_to_check}' đã tồn tại trên API chưa...")
    existing_family = get_family_by_code(family_code_to_check)

    if existing_family:
        api_family_guid = existing_family["id"]
        print(f"Gia đình với mã '{family_code_to_check}' đã tồn tại với API GUID: {api_family_guid}. Đang sử dụng gia đình hiện có.")
    else:
        # 1. Đọc thông tin gia đình
        giapha_info_path = os.path.join(data_dir, f"giapha_info_{folder_name}.json")
        try:
            with open(giapha_info_path, "r", encoding="utf-8") as f:
                family_info = json.load(f)
        except FileNotFoundError:
            print(f"Lỗi: Không tìm thấy tệp {giapha_info_path}", file=sys.stderr)
            return
        except json.JSONDecodeError:
            print(f"Lỗi: Không thể phân tích cú pháp tệp JSON {giapha_info_path}", file=sys.stderr)
            return

        # 2. Tạo gia đình
        print("Đang tạo gia đình mới trên API...")
        family_payload = {
            "name": family_info.get("name", "Gia đình không tên"),
            "code": family_code_to_check, # Sử dụng mã gia đình đã kiểm tra
            "address": family_info.get("address"),
            "description": family_info.get("description"),
            "visibility": "Private" # Mặc định là Private
        }
        api_family_guid = create_family(family_payload)
        if api_family_guid:
            print(f"Đã tạo gia đình mới với API GUID: {api_family_guid}")
        else:
            print("Không thể tạo gia đình mới. Đang thoát.")
            return

    # The family_id passed to member_payload is always the API GUID
    family_id_for_payload = api_family_guid

    # The identifier used in codes (familyCode, memberCode)
    identifier_for_codes = local_family_identifier if local_family_identifier else api_family_guid

    # 3. Tạo thành viên (Pass 1: Create members)
    members_dir = os.path.join(data_dir, "members")
    member_files = glob.glob(os.path.join(members_dir, "*.json"))
    
    if args.limit > 0:
        member_files = member_files[:args.limit]
    
    member_id_map = {} # Map original_file_id to created_member_guid
    all_member_data_raw = {} # Store raw JSON data for second pass

    print(f"\n--- Bắt đầu tạo thành viên (Lượt 1) ---")
    print(f"Tìm thấy {len(member_files)} tệp thành viên.")

    for member_file in member_files:
        try:
            with open(member_file, "r", encoding="utf-8") as f:
                member_data_raw = json.load(f)
            
            main_person = member_data_raw.get("main_person", {})
            original_file_id = os.path.splitext(os.path.basename(member_file))[0]
            all_member_data_raw[original_file_id] = member_data_raw

            if not main_person:
                print(f"Cảnh báo: Không tìm thấy 'main_person' trong tệp {member_file}. Bỏ qua.", file=sys.stderr)
                continue

            member_name_raw = main_person.get("name")
            if member_name_raw is None or member_name_raw == "":
                member_name = "Unknown Member"
            else:
                member_name = str(member_name_raw) # Explicitly convert to string
            last_name, first_name = parse_name(member_name)

            # Logic to determine if a member is a root member
            father_name = main_person.get("father_name")
            generation = main_person.get("generation")
            child_order = main_person.get("child_order")

            is_root = False
            if father_name == "Thuỷ tổ":
                is_root = True
            elif (generation is not None and str(generation).strip().isdigit() and int(str(generation).strip()) == 0 and 
                  child_order is not None and str(child_order).strip().isdigit() and int(str(child_order).strip()) == 1):
                is_root = True

            print(f"DEBUG: Xử lý thành viên: '{member_name}' -> Họ: '{last_name}', Tên: '{first_name}', isRoot: {is_root}", file=sys.stderr)

            member_payload = {
                "lastName": last_name,
                "firstName": first_name,
                "code": f"VNGP-{identifier_for_codes}-{original_file_id}", # Add member code
                "familyId": family_id_for_payload,
                "nickname": main_person.get("nickname"),
                "dateOfBirth": format_date_for_api(main_person.get("dob")),
                "dateOfDeath": format_date_for_api(main_person.get("dod")),
                "placeOfDeath": main_person.get("burial_place"), # Map burial_place to placeOfDeath
                "gender": "Male" if main_person.get("gender") == "Nam" else ("Female" if main_person.get("gender") == "Nữ" else "Other"),
                "biography": main_person.get("description"),
                "isDeceased": main_person.get("dod") is not None and main_person.get("dod") != "null" and main_person.get("dod") != "",
                "order": main_person.get("child_order"),
                "isRoot": is_root # NEW FIELD
            }
            # Remove None and empty string values from payload
            member_payload = {k: v for k, v in member_payload.items() if v is not None and v != ""}
            
            # Check if member already exists
            member_code_to_check = f"VNGP-{identifier_for_codes}-{original_file_id}"
            existing_member = get_member_by_family_id_and_code(family_id_for_payload, member_code_to_check)

            if existing_member:
                print(f"Thành viên '{last_name} {first_name}' (ID gốc: {original_file_id}, Code: {member_code_to_check}) đã tồn tại với ID: {existing_member['id']}. Bỏ qua tạo mới.")
                member_id_map[original_file_id] = existing_member["id"]
                continue
            
            created_member_guid = create_member(member_payload)
            if created_member_guid:
                print(f"Đã tạo thành viên '{last_name} {first_name}' (ID gốc: {original_file_id}) với ID: {created_member_guid}")
                member_id_map[original_file_id] = created_member_guid
            else:
                print(f"Không thể tạo thành viên '{last_name} {first_name}' (ID gốc: {original_file_id}). Bỏ qua.")
            
        except Exception as e:
            print(f"Lỗi khi xử lý tệp {member_file}: {e}", file=sys.stderr)
            print("FULL PYTHON TRACEBACK:", file=sys.stdout)
            print(traceback.format_exc(), file=sys.stdout)

    print("\n--- Kết thúc tạo thành viên (Lượt 1) ---")

    # 4. Cập nhật mối quan hệ (Pass 2: Update relationships)
    print("\n--- Bắt thúc cập nhật mối quan hệ (Lượt 2) ---")

    name_to_guid_map = {}
    for original_id, guid in member_id_map.items():
        raw_data = all_member_data_raw.get(original_id, {}).get("main_person", {})
        full_name = raw_data.get("name")
        if full_name:
            if full_name in name_to_guid_map:
                print(f"Cảnh báo: Tên '{full_name}' bị trùng lặp. Không thể xác định duy nhất GUID cho mối quan hệ.", file=sys.stderr)
                name_to_guid_map[full_name].append(guid) # Store as list if duplicates
            else:
                name_to_guid_map[full_name] = [guid] # Always store as list to handle future duplicates

    # This map needs to be simplified for lookup later, assuming unique names for relationships for now
    # If a name has multiple GUIDs, this will pick the first one and warn.
    simple_name_to_guid_map = {}
    for name, guids in name_to_guid_map.items():
        if len(guids) > 1:
            print(f"Cảnh báo: Tên '{name}' có nhiều GUID ({guids}). Chỉ sử dụng GUID đầu tiên '{guids[0]}' cho mối quan hệ.", file=sys.stderr)
        simple_name_to_guid_map[name] = guids[0]

    for original_id, member_guid in member_id_map.items():
        raw_data = all_member_data_raw.get(original_id, {})
        main_person = raw_data.get("main_person", {})
        
        current_member_api_data = get_member(member_guid)
        if not current_member_api_data:
            print(f"Không thể lấy dữ liệu API cho thành viên {member_guid}. Bỏ qua cập nhật mối quan hệ.", file=sys.stderr)
            continue

        updated = False
        # Resolve Father/Mother
        father_name = main_person.get("father_name")
        if father_name and father_name in simple_name_to_guid_map:
            father_guid = simple_name_to_guid_map[father_name]
            if current_member_api_data.get("fatherId") != father_guid:
                current_member_api_data["fatherId"] = father_guid
                print(f"  Cập nhật cha cho thành viên {member_guid} ('{main_person.get('name')}'): {father_guid} ('{father_name}')")
                updated = True
        elif father_name:
            print(f"  Cảnh báo: Không tìm thấy cha '{father_name}' trong dữ liệu đã tạo cho thành viên {member_guid} ('{main_person.get('name')}').", file=sys.stderr)

        # Resolve Spouses
        spouses = raw_data.get("spouses", [])
        if spouses:
            for spouse in spouses:
                spouse_name = spouse.get("name")
                if spouse_name and spouse_name in simple_name_to_guid_map:
                    spouse_guid = simple_name_to_guid_map[spouse_name]
                    # This logic assumes the main person's gender is known and can determine husband/wife
                    # For simplicity, if main_person is Male, assign wifeId, else husbandId.
                    # This might need refinement based on actual data.
                    main_person_gender = main_person.get("gender")
                    if main_person_gender == "Nam" and current_member_api_data.get("wifeId") != spouse_guid:
                        current_member_api_data["wifeId"] = spouse_guid
                        print(f"  Cập nhật vợ cho thành viên {member_guid} ('{main_person.get('name')}'): {spouse_guid} ('{spouse_name}')")
                        updated = True
                        break # Assume only one wife can be assigned this way in initial pass
                    elif main_person_gender == "Nữ" and current_member_api_data.get("husbandId") != spouse_guid:
                        current_member_api_data["husbandId"] = spouse_guid
                        print(f"  Cập nhật chồng cho thành viên {member_guid} ('{main_person.get('name')}'): {spouse_guid} ('{spouse_name}')")
                        updated = True
                        break # Assume only one husband can be assigned this way in initial pass
                elif spouse_name:
                    print(f"  Cảnh báo: Không tìm thấy vợ/chồng '{spouse_name}' trong dữ liệu đã tạo cho thành viên {member_guid} ('{main_person.get('name')}').", file=sys.stderr)
        
        # Children relationships are typically set from the child's side (FatherId/MotherId)
        # or require a separate API/logic to manage. The current data structure doesn't easily support
        # setting children from the parent's side during this update.

        if updated:
            success = update_member(member_guid, current_member_api_data)
            if success:
                print(f"  Đã cập nhật mối quan hệ cho thành viên {member_guid} ('{main_person.get('name')}').")
            else:
                print(f"  Không thể cập nhật mối quan hệ cho thành viên {member_guid} ('{main_person.get('name')}').")
        else:
            print(f"  Không có mối quan hệ nào cần cập nhật cho thành viên {member_guid} ('{main_person.get('name')}').")
        
        time.sleep(0.1) # Small delay to prevent API rate limiting issues

    print("\n--- Kết thúc cập nhật mối quan hệ (Lượt 2) ---")
    print("\nQuá trình tạo và cập nhật gia đình, thành viên đã hoàn tất.")
    print("Ánh xạ ID gốc -> GUID thành viên đã tạo:")
    for original_id, guid in member_id_map.items():
        print(f"  {original_id}: {guid}")


if __name__ == "__main__":
    main()