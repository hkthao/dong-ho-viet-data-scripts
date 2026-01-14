from bs4 import BeautifulSoup
import json
import re
import sys

def format_date(date_str):
    if not date_str:
        return None
    date_str = date_str.strip()
    # Try to parse full date DD/MM/YYYY
    match_full_date = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
    if match_full_date:
        day, month, year = match_full_date.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    
    # Try to parse year only YYYY
    match_year = re.match(r'(\d{4})', date_str)
    if match_year:
        year = match_year.group(1)
        return f"{year}-01-01"
    
    return date_str # Return as is if no specific format matches or it's not a date

# This helper function extracts details from a specific set of rows,
# stopping at a given header or an <hr/> tag.
def _extract_details_from_rows(rows_soup_list, stop_on_header=None):
    details = {}
    description_collected = []
    in_description_section = False
    description_already_collected_for_this_section = False
    
    for row_index, row in enumerate(rows_soup_list):
        # Check for stop condition first (before any other processing of the row)
        if stop_on_header and stop_on_header in row.get_text(strip=True):
            return details, '\n'.join(description_collected), rows_soup_list[row_index] # Return the exact row object

        # Check for "Sự nghiệp, công đức, ghi chú" header to start description collection
        is_description_start_header = ('Sự nghiệp, công đức, ghi chú' in row.get_text(strip=True) and
                                     row.find('td', style=lambda value: value and 'font-weight:bold' in value))
        if is_description_start_header:
            in_description_section = True
            description_already_collected_for_this_section = False # Reset flag for new description section
            continue # Skip this header row itself, next row should contain description content
        
        # Stop description collection if an <hr/> tag is found
        if in_description_section and row.find('hr'):
            in_description_section = False # No longer in description section
            continue # Don't process this <hr> row as description content
        
        # If we are in the description section AND haven't collected it yet, process the row as description content
        if in_description_section and not description_already_collected_for_this_section:
            description_td = row.find('td', colspan='3')
            if description_td:
                paragraph_texts = [p.get_text(separator=' ', strip=True) for p in description_td.find_all('p')]
                clean_text = '\n'.join(p for p in paragraph_texts if p) # Join non-empty paragraphs with newline
                if clean_text:
                    description_collected.append(clean_text)
                    description_already_collected_for_this_section = True # Mark as collected
            
            in_description_section = False # This description section is now fully processed or skipped
            continue # Continue to next row

        # Process as a regular key-value pair if not in description section and not a description header
        key_td = row.find('td', style=lambda value: value and 'font-weight:bold' in value)
        if key_td:
            key = key_td.get_text(strip=True).replace(':', '').replace('\xa0', ' ')
            value_td = key_td.find_next_sibling('td')
            if value_td:
                value = value_td.get_text(strip=True).replace('\xa0', ' ')
                details[key] = value
            # If a new key-value pair is found, it implicitly means any prior description section has ended.
            in_description_section = False
            description_already_collected_for_this_section = False # Reset for any new description sections
            continue # Continue to next row after processing key-value pair

    return details, '\n'.join(description_collected), None # Return None for remaining rows if no stop_on_header was met

def extract_family_data(html_file_path):
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    
    family_data = {}

    # Define translation map for JSON keys
    key_translation_map = {
        'Tên': 'name',
        'Giới tính': 'gender',
        'Tên thường': 'nickname',
        'Tên Tự': 'alias',
        'Là con thứ': 'child_order',
        'Ngày sinh': 'dob',
        'Địa chỉ': 'address',
        'Đời thứ': 'generation',
        'Là con của': 'father',
        'Sự nghiệp, công đức, ghi chú': 'description',
        'Hưởng thọ': 'age_at_death',
        'Ngày mất': 'dod',
        'Nơi an táng': 'burial_place',
    }

    main_content_td = soup.find(lambda tag: tag.name.lower() == 'td', valign="top", width="85%", background=re.compile(r'bkbook.gif'))
    if not main_content_td:
        print(f"Warning: Could not find main_content_td for {html_file_path}. Returning empty JSON.")
        return json.dumps({}, ensure_ascii=False, indent=4)
    detail_container_table = main_content_td.find(lambda tag: tag.name.lower() == 'table', align="center", width="80%")
    if not detail_container_table:
        print(f"Warning: Could not find detail_container_table for {html_file_path}. Returning empty JSON.")
        return json.dumps({}, ensure_ascii=False, indent=4)
    
    # Define all_tbody_trs as the direct TR children of the main detail_container_table
    # This is needed for extracting father and other details that are in the outer table structure
    all_tbody_trs = detail_container_table.find_all(lambda tag: tag.name.lower() == 'tr', recursive=False)
    
    # --- Find the main person's detail table ---
    person_detail_table = None
    
    # First, find the td that contains the "Người trong gia đình" text and has bold styling
    main_person_header_td = detail_container_table.find(
        lambda tag: tag.name.lower() == 'td', style=lambda value: value and 'font-weight:bold' in value, string='Người trong gia đình'
    )

    if main_person_header_td:
        # Now, find the closest parent table to this td
        person_detail_table = main_person_header_td.find_parent(lambda tag: tag.name.lower() == 'table')

    if not person_detail_table:
        print(f"Error: Could not find main person's detail table for {html_file_path}. Returning empty JSON.")
        return json.dumps({}, ensure_ascii=False, indent=4)
    
    
    # --- Extract main person's details (Cao Thị Yên) ---
    all_person_table_rows = person_detail_table.find_all('tr')
    main_person_raw_details, main_person_description, spouse_start_row = _extract_details_from_rows(
        all_person_table_rows, 
        stop_on_header='Liên quan (chồng, vợ) trong gia đình'
    )
    
    main_person_processed_data = {}
    if main_person_description:
        main_person_processed_data[key_translation_map['Sự nghiệp, công đức, ghi chú']] = main_person_description

    if 'Tên' in main_person_raw_details:
        name_gender = main_person_raw_details['Tên']
        if '(Nữ)' in name_gender:
            main_person_processed_data[key_translation_map['Tên']] = name_gender.replace('(Nữ)', '').strip()
            main_person_processed_data[key_translation_map['Giới tính']] = 'Female'
        elif '(Nam)' in name_gender:
            main_person_processed_data[key_translation_map['Tên']] = name_gender.replace('(Nam)', '').strip()
            main_person_processed_data[key_translation_map['Giới tính']] = 'Male'
        else:
            main_person_processed_data[key_translation_map['Tên']] = name_gender.strip()
            main_person_processed_data[key_translation_map['Giới tính']] = 'Unknown'
    else:
        main_person_processed_data[key_translation_map['Giới tính']] = 'Unknown'

    # Map other fields for Main Person
    for key_vn, key_en in key_translation_map.items():
        if key_vn in main_person_raw_details and key_vn not in ['Tên', 'Giới tính', 'Sự nghiệp, công đức, ghi chú']:
            if key_vn == 'Ngày sinh':
                main_person_processed_data[key_en] = format_date(main_person_raw_details[key_vn])
            else:
                main_person_processed_data[key_en] = main_person_raw_details[key_vn]
    
    # Extract 'Đời thứ' (generation)
    doi_thu_td = detail_container_table.find('td', string=re.compile(r'Đời thứ:'))
    if doi_thu_td:
        doi_thu_value = doi_thu_td.get_text(strip=True).split('Đời thứ:')[-1].strip()
        main_person_processed_data[key_translation_map['Đời thứ']] = doi_thu_value
    
    # Extract 'Là con của' (father)
    # Iterate through all direct trs to find the one with 'Là con của:' text
    father_td_element = None
    for tr in all_tbody_trs:
        # Find all td elements within the current tr
        td_elements = tr.find_all('td')
        for td in td_elements:
            if 'Là con của:' in td.get_text(strip=True):
                father_td_element = td
                break
        if father_td_element:
            break

    if father_td_element:
        father_link = father_td_element.find('a')
        if father_link:
            main_person_processed_data[key_translation_map['Là con của']] = {
                'name': father_link.get_text(strip=True),
                'url': father_link.get('href')
            }
    
    family_data['main_person'] = main_person_processed_data

    # --- Extract spouse details ---
    spouse_raw_details = {}
    spouse_description = ""
    
    if spouse_start_row:
        # Get all rows from spouse_start_row onwards
        remaining_rows_for_spouse = all_person_table_rows[all_person_table_rows.index(spouse_start_row):]
        spouse_raw_details, spouse_description, _ = _extract_details_from_rows(
            remaining_rows_for_spouse, 
            stop_on_header=None # No stop header for spouse's section
        )

    spouse_processed_data = {}
    if spouse_description:
        spouse_processed_data[key_translation_map['Sự nghiệp, công đức, ghi chú']] = spouse_description

    if 'Tên' in spouse_raw_details:
        name_gender = spouse_raw_details['Tên']
        if '(Nữ)' in name_gender:
            spouse_processed_data[key_translation_map['Tên']] = name_gender.replace('(Nữ)', '').strip()
            spouse_processed_data[key_translation_map['Giới tính']] = 'Female'
        elif '(Nam)' in name_gender:
            spouse_processed_data[key_translation_map['Tên']] = name_gender.replace('(Nam)', '').strip()
            spouse_processed_data[key_translation_map['Giới tính']] = 'Male'
        else:
            spouse_processed_data[key_translation_map['Tên']] = name_gender.strip()
            spouse_processed_data[key_translation_map['Giới tính']] = 'Unknown'
    else:
        spouse_processed_data[key_translation_map['Giới tính']] = 'Unknown'

    # Map other fields for Spouse
    for key_vn, key_en in key_translation_map.items():
        if key_vn in spouse_raw_details and key_vn not in ['Tên', 'Giới tính', 'Sự nghiệp, công đức, ghi chú']:
            if key_vn in ['Ngày sinh', 'Ngày mất']:
                spouse_processed_data[key_en] = format_date(spouse_raw_details[key_vn])
            else:
                spouse_processed_data[key_en] = spouse_raw_details[key_vn]

    family_data['spouse'] = spouse_processed_data

    # --- Extract children from the main person's description ---
    children_list = []
    if key_translation_map['Sự nghiệp, công đức, ghi chú'] in family_data['main_person']:
        description = family_data['main_person'][key_translation_map['Sự nghiệp, công đức, ghi chú']]
        
        # Children pattern: looks for "NUMBER- Name: details"
        children_pattern = re.compile(r'(\d+)-\s*([^:]+):\s*(.*?)(?=\n\d+-\s*[^:]+:|\n\n|\Z)', re.DOTALL)
        
        # Use finditer to get all matches
        matches = children_pattern.finditer(description)

        for match in matches:
            child_number_str, child_name, child_details = match.groups()
            children_list.append({
                'number': int(child_number_str),
                'name': child_name.strip(),
                'details': child_details.strip()
            })
    family_data['children'] = children_list

    family_data['siblings'] = [] 

    return json.dumps(family_data, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_member_info.py <html_file_path> [output_json_file_path]")
        sys.exit(1)
    
    html_file = sys.argv[1]
    output_json_file = 'family_data.json'
    if len(sys.argv) > 2:
        output_json_file = sys.argv[2]

    json_output = extract_family_data(html_file)
    
    with open(output_json_file, 'w', encoding='utf-8') as f:
        f.write(json_output)
    print(f"Dữ liệu đã được lưu vào '{output_json_file}'")