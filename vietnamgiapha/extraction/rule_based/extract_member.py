import os # Added os import
import json
import re
from bs4 import BeautifulSoup

# 4. Schema output chuẩn (bắt buộc)
OUTPUT_SCHEMA = {
    "lastName": "",
    "firstName": "",
    "code": "",
    "nickname": "",
    "dateOfBirth": None,
    "dateOfDeath": None,
    "dateOfDeathLunar": None,
    "placeOfBirth": None,
    "placeOfDeath": None,
    "phone": "",
    "email": "",
    "address": "",
    "gender": "",
    "avatarUrl": "",
    "avatarBase64": "",
    "occupation": "",
    "biography": "",
    "isRoot": False,
    "order": 0,
    "generation": 0,
    "father": None,
    "mother": None, # Mother is not explicitly mentioned in the task, but is in schema-member.txt. Will keep it null for now.
    "spouses": []
}

# Helper functions
def extract_between_parentheses(text):
    """Trích xuất văn bản trong dấu ngoặc đơn."""
    match = re.search(r'\((.*?)\)', text)
    return match.group(1).strip() if match else ""

def remove_parentheses(text):
    """Xóa phần trong dấu ngoặc đơn khỏi văn bản."""
    return re.sub(r'\s*\(.*?\)\s*', '', text).strip()

def parse_name_gender(text):
    """Phân tích họ, tên và giới tính từ một chuỗi."""
    gender = extract_between_parentheses(text)
    name = remove_parentheses(text)
    
    # 8. Chuẩn hoá dữ liệu (bắt buộc) - Trim string
    name = name.strip()
    gender = gender.strip()

    parts = name.split(maxsplit=1) # Split only on the first space to get lastName and the rest as firstName
    
    last_name = parts[0] if parts else ""
    first_name = parts[1] if len(parts) > 1 else ""

    return {
        "lastName": last_name,
        "firstName": first_name,
        "gender": gender
    }

def normalize_date(date_str):
    """Chuẩn hóa chuỗi ngày thành định dạng YYYY-MM-DD hoặc trả về None."""
    if not date_str or date_str.lower() in ["chưa rõ", "không rõ"]:
        return None
    
    # Simple regex to find common date formats (DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD)
    # This is a very basic normalization. A real-world scenario might need date parsing libraries.
    date_str = date_str.strip().replace('-', '/')
    
    match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
    if match:
        day, month, year = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    
    return None # Return None if date format is not recognized

def clean_text(text):
    """Loại bỏ khoảng trắng thừa, &nbsp; và các ký tự XML lạ."""
    if text is None:
        return ""
    text = text.replace('\xa0', ' ').replace('&nbsp;', ' ').strip() # Remove non-breaking space
    return text

def extract_last_name(full_name):
    """Trích xuất họ từ tên đầy đủ."""
    parts = full_name.strip().split(maxsplit=1)
    return parts[0] if parts else ""

def extract_first_name(full_name):
    """Trích xuất tên từ tên đầy đủ."""
    parts = full_name.strip().split(maxsplit=1)
    return parts[1] if len(parts) > 1 else ""

def generate_member_code(folder_name, member_filename):
    """Tạo mã thành viên dựa trên folder_name và member_filename.
    Format: GPVN-{folder_name}-{member_suffix_from_filename}
    Ví dụ: GPVN-1-1 (nếu folder_name là '1' và member_filename là 'GPVN-1691-1.json')
    """
    member_id_parts = os.path.splitext(member_filename)[0].split('-') # e.g., ["GPVN", "1691", "1"]
    member_suffix = ""
    if len(member_id_parts) >= 3:
        member_suffix = member_id_parts[2] # "1" from "GPVN-1691-1"
    else:
        # Fallback if filename format is unexpected, take the whole name after GPVN-
        member_suffix = os.path.splitext(member_filename)[0].replace("GPVN-", "")

    return f"GPVN-{folder_name}-{member_suffix}"

def extract_text_after_colon(text):
    """Trích xuất văn bản sau dấu hai chấm đầu tiên."""
    parts = text.split(':', 1)
    return parts[1].strip() if len(parts) > 1 else ""

def split_by_br_or_newline(html_content):
    """Tách văn bản HTML bởi thẻ <br> hoặc xuống dòng."""
    soup = BeautifulSoup(str(html_content), "lxml")
    # Replace <br> tags with newlines for consistent splitting
    for br in soup.find_all("br"):
        br.replace_with("\n")
    # Get text and split by newlines, filter out empty lines
    return [line.strip() for line in soup.get_text().split('\n') if line.strip()]

def parse_stub_member(name_text):
    """Tạo đối tượng thành viên stub từ tên."""
    # Reuse parse_name_gender for gender and name splitting
    name_gender_info = parse_name_gender(name_text)
    return {
        "lastName": name_gender_info["lastName"],
        "firstName": name_gender_info["firstName"],
        "gender": name_gender_info["gender"],
        "code": None
    }

def parse_family_html(html_content, family_id, member_filename):
    """Phân tích HTML gia phả và trả về JSON theo schema."""
    soup = BeautifulSoup(html_content, "lxml")
    rows = soup.find_all("tr")

    output = {
        "lastName": "",
        "firstName": "",
        "code": "",
        "nickname": "",
        "dateOfBirth": None,
        "dateOfDeath": None,
        "dateOfDeathLunar": None,
        "placeOfBirth": None,
        "placeOfDeath": None,
        "phone": "",
        "email": "",
        "address": "",
        "gender": "",
        "avatarUrl": "",
        "avatarBase64": "",
        "occupation": "",
        "biography": "",
        "isRoot": False,
        "isDeceased": False, # Explicitly initialize isDeceased to False
        "order": 0,
        "generation": 0,
        "father": None,
        "mother": None,
        "spouses": [], # Explicitly initialize as an empty list for each call
        "siblings": [], # Re-introducing siblings list as per extended schema
        "children": [] # Re-introducing children list as per extended schema
    }

    current_section = None
    current_spouse = None
    
    # Helper to apply values, cleaning text
    def set_output_field(obj, key, value):
        if obj is not None:
            obj[key] = clean_text(value)
        
    for i, row in enumerate(rows):
        row_text = row.get_text(strip=True)

        # 6. Nhận diện section bằng TEXT
        if "Chi tiết gia đình" in row_text:
            current_section = "FAMILY"
            continue
        elif "Người trong gia đình" in row_text:
            current_section = "PERSON"
            current_spouse = None # Reset spouse context
            continue
        elif "Liên quan (chồng, vợ)" in row_text:
            current_section = "SPOUSE_SECTION"
            # Prepare for a new spouse. The actual spouse object is created when 'Tên' is found.
            current_spouse = None
            continue

        cells = row.find_all(["td", "th"]) # Include th as some labels might be in th
        if not cells:
            continue

        label = clean_text(cells[0].get_text())
        value = clean_text(cells[1].get_text()) if len(cells) > 1 else ""

        # Handle "Là con của" if it appears in the FAMILY section (before PERSON starts)
        if current_section == "FAMILY" and "Là con của" in row_text:
            father_link = row.find('a', href=re.compile(r'/XemChiTietTungNguoi/(\d+)/(\d+)/'))
            
            father_name_text = ""
            father_code = None
            
            if father_link:
                href = father_link.get('href')
                father_name_text = clean_text(father_link.get_text())
                match = re.search(r'/XemChiTietTungNguoi/(\d+)/(\d+)/', href)
                if match:
                    extracted_family_id = match.group(1)
                    extracted_member_id = match.group(2)
                    father_code = f"GPVN-{extracted_family_id}-{extracted_member_id}"
            
            # If father_link was not found, or if father_name_text is still empty after trying to get it from the link,
            # then try to get the name from the general row text (e.g., for cases without a link)
            if not father_name_text:
                name_part_from_row_text = extract_text_after_colon(label) # `label` is `clean_text(cells[0].get_text())`
                father_name_text = name_part_from_row_text

            if not father_name_text: # If after all attempts, no name, skip
                continue

            # Determine if this father is the "Thuỷ tổ"
            is_progenitor = "Thuỷ tổ".lower() in father_name_text.lower() or "Thủy tổ".lower() in father_name_text.lower()

            output["isRoot"] = is_progenitor

            # If it's a progenitor AND there's no link associated, then father is truly None (no object)
            if is_progenitor and father_link is None:
                 output["father"] = None
            else:
                father_info = parse_name_gender(father_name_text)
                output["father"] = {
                    "lastName": father_info["lastName"],
                    "firstName": father_info["firstName"],
                    "code": father_code, # This will be None if no link was found, which is acceptable
                    "gender": "Nam"
                }
        
        # Now process fields specific to the current_section
        if current_section == "PERSON":
            if label == "Tên":
                name_gender_info = parse_name_gender(value)
                output["lastName"] = name_gender_info["lastName"]
                output["firstName"] = name_gender_info["firstName"]
                output["gender"] = name_gender_info["gender"]
            elif label == "Tên thường":
                set_output_field(output, "nickname", value)
            elif label == "Đời thứ":
                try:
                    output["generation"] = int(value)
                except ValueError:
                    output["generation"] = 0
            elif label == "Là con thứ":
                try:
                    output["order"] = int(value)
                except ValueError:
                    output["order"] = 0
            elif label == "Ngày sinh":
                output["dateOfBirth"] = normalize_date(value)
            elif label == "Ngày mất":
                output["dateOfDeath"] = normalize_date(value)
                output["isDeceased"] = True
            elif label == "Ngày mất (ÂL)": # Assuming lunar date might be present
                output["dateOfDeathLunar"] = value # Keep as string for now
            elif label == "Nơi sinh":
                set_output_field(output, "placeOfBirth", value)
            elif label == "Nơi an táng":
                set_output_field(output, "placeOfDeath", value)
            elif label == "Điện thoại":
                set_output_field(output, "phone", value)
            elif label == "Email":
                set_output_field(output, "email", value)
            elif label == "Địa chỉ":
                set_output_field(output, "address", value)
            elif label == "Nghề nghiệp":
                set_output_field(output, "occupation", value)
            elif label == "Hưởng thọ": # "Hưởng thọ" implies deceased
                output["isDeceased"] = True
            elif label == "Sự nghiệp, công đức, ghi chú":
                # Assuming biography is in the next row's first cell
                if i + 1 < len(rows):
                    next_row = rows[i + 1]
                    next_row_cells = next_row.find_all(["td", "th"])
                    if next_row_cells:
                        set_output_field(output, "biography", next_row_cells[0].get_text())
            # avatarUrl, avatarBase64 not directly extractable from text labels

        elif current_section == "SPOUSE_SECTION":
            if label == "Tên":
                # If a new spouse's name is encountered, and there's an existing current_spouse,
                # add the existing one to the list before starting a new one.
                if current_spouse is not None and (current_spouse["lastName"] or current_spouse["firstName"]):
                    output["spouses"].append(current_spouse)

                name_gender_info = parse_name_gender(value)
                # Increment spouse_count to generate unique ID
                spouse_count = len(output["spouses"]) + 1
                
                # Extract member_suffix from member_filename (e.g., "1" from "GPVN-1691-1.json")
                member_id_parts = os.path.splitext(member_filename)[0].split('-')
                member_suffix = ""
                if len(member_id_parts) >= 3:
                    member_suffix = member_id_parts[2]
                else:
                    member_suffix = os.path.splitext(member_filename)[0].replace("GPVN-", "")

                spouse_code = f"GPVN-{family_id}-{member_suffix}-S{spouse_count}" # family_id here is the folder_name
                
                current_spouse = {
                    "code": spouse_code, # Changed from 'id' to 'code'
                    "lastName": name_gender_info["lastName"],
                    "firstName": name_gender_info["firstName"],
                    "gender": name_gender_info["gender"],
                    "dateOfBirth": None,
                    "dateOfDeath": None,
                    "biography": ""
                }
            elif current_spouse is not None:
                if label == "Ngày sinh":
                    current_spouse["dateOfBirth"] = normalize_date(value)
                elif label == "Ngày mất":
                    current_spouse["dateOfDeath"] = normalize_date(value)
                elif label == "Sự nghiệp, công đức, ghi chú":
                    if i + 1 < len(rows):
                        next_row = rows[i + 1]
                        next_row_cells = next_row.find_all(["td", "th"])
                        if next_row_cells:
                            set_output_field(current_spouse, "biography", next_row_cells[0].get_text())
        

        
    # After the loop, if there's a current_spouse that hasn't been added, add it.
    # Also ensure spouse_count is correctly incremented for the last spouse if it was just created.
    if current_spouse is not None and (current_spouse["lastName"] or current_spouse["firstName"]):
        # Check if the last current_spouse object was already added by a previous 'Tên' label
        # or if it's a new one that needs to be appended.
        # A simpler check: if the CODE is not yet set, append it.
        if "code" not in current_spouse:
            spouse_count = len(output["spouses"]) + 1
            
            # Extract member_suffix from member_filename (e.g., "1" from "GPVN-1691-1.json")
            member_id_parts = os.path.splitext(member_filename)[0].split('-')
            member_suffix = ""
            if len(member_id_parts) >= 3:
                member_suffix = member_id_parts[2]
            else:
                member_suffix = os.path.splitext(member_filename)[0].replace("GPVN-", "")
            
            current_spouse["code"] = f"GPVN-{family_id}-{member_suffix}-S{spouse_count}"
        output["spouses"].append(current_spouse)

    # 7.9 Father - If "Là con của" was not found, then it's a root.
    if output["father"] is None:
        output["isRoot"] = True
    
    # 9. Sinh code (nếu cần)
    if output["lastName"] and output["firstName"] and output["gender"] and output["generation"] is not None and output["order"] is not None:
        output["code"] = generate_member_code(
            folder_name=family_id, # family_id in parse_family_html is the folder_name
            member_filename=member_filename
        )

    # Ensure mother is null
    output["mother"] = None

    # Implement parsing for "Các anh em, dâu rể" and "Con cái"
    # These sections are not state-based like PERSON or SPOUSE_SECTION;
    # their data is typically self-contained within a single <td> element.
    for i, row in enumerate(rows):
        row_text = row.get_text(strip=True)
        cells = row.find_all(["td", "th"])

        if not cells:
            continue

        # Logic for "Các anh em, dâu rể"
        if "Các anh em, dâu rể:" in row_text:
            data_td = cells[0] # The entire data is in the first cell
            
            if "Không có anh em" in data_td.get_text(strip=True): # Check if there are no siblings
                output["siblings"] = [] # Explicitly empty
            else:
                # Find all <a> tags within the data_td for siblings
                sibling_links = data_td.find_all('a', href=re.compile(r'/XemChiTietTungNguoi/(\d+)/(\d+)/'))
                
                for link in sibling_links:
                    name_text = clean_text(link.get_text())
                    href = link.get('href')
                    
                    sibling_code = None
                    match = re.search(r'/XemChiTietTungNguoi/(\d+)/(\d+)/', href)
                    if match:
                        extracted_family_id = match.group(1)
                        extracted_member_id = match.group(2)
                        sibling_code = f"GPVN-{extracted_family_id}-{extracted_member_id}"
                    
                    sibling_info = parse_name_gender(name_text)
                    sibling = {
                        "lastName": sibling_info["lastName"],
                        "firstName": sibling_info["firstName"],
                        "code": sibling_code,
                        "gender": sibling_info["gender"] # Can be empty if not in parentheses
                    }
                    output["siblings"].append(sibling)
            continue # Move to next row

        # Logic for "Con cái"
        if "Con cái:" in row_text:
            data_td = cells[0] # The entire data is in the first cell

            # Find all <a> tags within the data_td for children
            child_links = data_td.find_all('a', href=re.compile(r'/XemChiTietTungNguoi/(\d+)/(\d+)/'))
            
            for link in child_links:
                name_text = clean_text(link.get_text())
                href = link.get('href')
                
                child_code = None
                match = re.search(r'/XemChiTietTungNguoi/(\d+)/(\d+)/', href)
                if match:
                    extracted_family_id = match.group(1)
                    extracted_member_id = match.group(2)
                    child_code = f"GPVN-{extracted_family_id}-{extracted_member_id}"
                
                child_info = parse_name_gender(name_text)
                child = {
                    "lastName": child_info["lastName"],
                    "firstName": child_info["firstName"],
                    "code": child_code,
                    "gender": child_info["gender"] # Can be empty if not in parentheses
                }
                output["children"].append(child)
            continue # Move to next row
    
    # Ensure all string fields are "" if None or not set
    for key, val in output.items():
        if isinstance(val, str) and not val:
            output[key] = ""
        elif val is None and key in ["lastName", "firstName", "code", "nickname", "phone", "email", "address", "gender", "avatarUrl", "avatarBase64", "occupation", "biography"]:
            output[key] = ""
    
    # Ensure spouse fields are also standardized
    for spouse in output["spouses"]:
        for key, val in spouse.items():
            if isinstance(val, str) and not val:
                spouse[key] = ""
            elif val is None and key in ["lastName", "firstName", "gender", "biography"]:
                spouse[key] = ""
    
    # Ensure sibling stub objects are standardized
    for sibling in output["siblings"]:
        for key, val in sibling.items():
            if isinstance(val, str) and not val:
                sibling[key] = ""
            elif val is None and key in ["lastName", "firstName", "gender", "code"]:
                sibling[key] = ""

    # Ensure children stub objects are standardized
    for child in output["children"]:
        for key, val in child.items():
            if isinstance(val, str) and not val:
                child[key] = ""
            elif val is None and key in ["lastName", "firstName", "gender", "code"]:
                child[key] = ""
    
    # Final check for isDeceased - if dateOfDeath is set, then isDeceased must be True
    if output["dateOfDeath"]:
        output["isDeceased"] = True
    
    # Ensure mother is null
    output["mother"] = None

    return json.dumps(output, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import os
    sample_dir = "vietnamgiapha/sample"
    output_dir = "output_json"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    html_files = [f for f in os.listdir(sample_dir) if f.endswith(".html")]
    
    for filename in sorted(html_files):
        file_path = os.path.join(sample_dir, filename)
        print(f"--- Parsing {filename} ---")
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        try:
            json_output = parse_family_html(html_content)
            
            # Construct output JSON filename
            base_filename = os.path.splitext(filename)[0]
            output_json_path = os.path.join(output_dir, f"{base_filename}.json")
            print(f"Attempting to write to: {os.path.abspath(output_json_path)}")
            
            with open(output_json_path, "w", encoding="utf-8") as json_f:
                json_f.write(json_output)
            print(f"Output written to {output_json_path}")
            
        except Exception as e:
            print(f"Error parsing {filename}: {e}")
        print("-" * 30)