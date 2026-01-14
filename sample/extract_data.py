import markdown # Import the markdown library
from bs4 import BeautifulSoup
import json
import re

def format_date(date_str):
    if not date_str:
        return None
    date_str = date_str.strip()
    # Try to parse full date DD/MM/YYYY
    match_full_date = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
    if match_full_date:
        day, month, year = match_full_date.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    
    # Try to parse full date DD-MM-YYYY
    match_full_date_dash = re.match(r'(\d{1,2})-(\d{1,2})-(\d{4})', date_str)
    if match_full_date_dash:
        day, month, year = match_full_date_dash.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    
    # Try to parse year only YYYY
    match_year = re.match(r'(\d{4})', date_str)
    if match_year:
        year = match_year.group(1)
        return f"{year}-01-01"
    
    return date_str # Return as is if no specific format matches or it's not a date

# This helper function extracts details from a specific table (converted from markdown)
def _extract_details_from_rows(table_soup):
    details = {}
    
    # Find all rows in the table body (excluding header row)
    rows = table_soup.find_all('tr')
    # The first row is usually the header in markdown tables, so skip it
    if rows and rows[0].find('th'):
        rows = rows[1:]

    for row in rows:
        cells = row.find_all(['th', 'td'])
        if len(cells) == 2:
            key = cells[0].get_text(strip=True).replace(':', '').replace('\xa0', ' ')
            value = cells[1].get_text(strip=True).replace('\xa0', ' ')
            details[key] = value
    return details


# Helper function to process a single person's raw details into a structured dictionary
def _process_person_details(raw_details, description, key_translation_map):
    processed_data = {}
    
    # Handle description combination
    table_description_key_vn = 'Sự nghiệp, công đức, ghi chú'
    combined_description = []

    if table_description_key_vn in raw_details:
        combined_description.append(raw_details[table_description_key_vn])
    if description:
        combined_description.append(description)
    
    if combined_description:
        processed_data[key_translation_map[table_description_key_vn]] = '\n'.join(combined_description).strip()

    if 'Tên' in raw_details:
        name_gender = raw_details['Tên']
        if '(Nữ)' in name_gender:
            processed_data[key_translation_map['Tên']] = name_gender.replace('(Nữ)', '').strip()
            processed_data[key_translation_map['Giới tính']] = 'Female'
        elif '(Nam)' in name_gender:
            processed_data[key_translation_map['Tên']] = name_gender.replace('(Nam)', '').strip()
            processed_data[key_translation_map['Giới tính']] = 'Male'
        else:
            processed_data[key_translation_map['Tên']] = name_gender.strip()
            processed_data[key_translation_map['Giới tính']] = 'Unknown'
    else:
        processed_data[key_translation_map['Giới tính']] = 'Unknown'

    # Map other fields
    for key_vn, key_en in key_translation_map.items():
        if key_vn in raw_details and key_vn not in ['Tên', 'Giới tính', table_description_key_vn]: # Exclude raw description already handled
            if key_vn in ['Ngày sinh', 'Ngày mất']:
                processed_data[key_en] = format_date(raw_details[key_vn])
            else:
                processed_data[key_en] = raw_details[key_vn]
    return processed_data

def extract_family_data(md_file_path): # Changed parameter name
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    html_content = markdown.markdown(md_content, extensions=['tables']) # Convert markdown to HTML with table extension
    # print("Generated HTML:\n", html_content) # For debugging
    soup = BeautifulSoup(html_content, 'html.parser')
    # print("BeautifulSoup object:\n", soup.prettify()) # For debugging
    
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

    # Find the main person's detail table by looking for the <h3> header
    main_person_header = soup.find('h3', string=re.compile(r'Người trong gia đình'))
    if not main_person_header:
        print("Error: Could not find main person's detail header.")
        return json.dumps({}, ensure_ascii=False, indent=4)
    
    person_detail_table = main_person_header.find_next_sibling('table')
    if not person_detail_table:
        print("Error: Could not find main person's detail table.")
        return json.dumps({}, ensure_ascii=False, indent=4)
    
    # --- Extract main person's details ---
    main_person_raw_details = _extract_details_from_rows(person_detail_table)
    
    # Extract description for main person (text between main person table and spouse header)
    main_person_description_paragraphs = []
    current_element = person_detail_table.next_sibling
    while current_element and current_element.name != 'h3' and 'Liên quan (chồng, vợ) trong gia đình' not in current_element.get_text(strip=True) if current_element.name == 'h3' else True:
        if current_element.name == 'p':
            main_person_description_paragraphs.append(current_element.get_text(separator=' ', strip=True))
        elif current_element.name == 'ul' or current_element.name == 'ol': # Handle lists in description
            list_items = [li.get_text(separator=' ', strip=True) for li in current_element.find_all('li')]
            main_person_description_paragraphs.append('\n'.join(list_items))
        
        current_element = current_element.next_sibling
        # To avoid infinite loops on bare strings between tags
        if isinstance(current_element, str):
            current_element = current_element.next_sibling
            
    main_person_description = '\n'.join(main_person_description_paragraphs).strip()

    main_person_processed_data = _process_person_details(main_person_raw_details, main_person_description, key_translation_map)
    
    # Extract 'Đời thứ' (generation) and 'Là con của' (father) from <p> tags before main person header
    current_element = main_person_header.previous_sibling
    generation_found = False
    father_found = False

    while current_element and (not generation_found or not father_found):
        if current_element.name == 'p':
            p_text = current_element.get_text(strip=True)
            if 'Đời thứ:' in p_text and not generation_found:
                doi_thu_value = p_text.split('Đời thứ:')[-1].strip()
                main_person_processed_data[key_translation_map['Đời thứ']] = doi_thu_value
                generation_found = True
            if 'Là con của:' in p_text and not father_found:
                father_link = current_element.find('a')
                if father_link:
                    main_person_processed_data[key_translation_map['Là con của']] = {
                        'name': father_link.get_text(strip=True),
                        'url': father_link.get('href')
                    }
                else:
                    father_name_match = re.search(r'Là con của:\s*(.+)', p_text)
                    if father_name_match:
                        main_person_processed_data[key_translation_map['Là con của']] = {
                            'name': father_name_match.group(1).strip(),
                            'url': None
                        }
                father_found = True
        current_element = current_element.previous_sibling
        # To avoid infinite loops on bare strings between tags
        if isinstance(current_element, str):
            current_element = current_element.previous_sibling

    family_data['main_person'] = main_person_processed_data

    # --- Extract spouse details ---
    spouse_header = soup.find('h3', string=re.compile(r'Liên quan \(chồng, vợ\) trong gia đình'))
    spouse_list = []
    if spouse_header:
        current_element = spouse_header.next_sibling
        while current_element:
            if current_element.name == 'h4': # Each spouse might be under an h4
                spouse_name_gender = current_element.get_text(strip=True)
                spouse_table = current_element.find_next_sibling('table')
                if spouse_table:
                    spouse_raw_details = _extract_details_from_rows(spouse_table)
                    spouse_description_paragraphs = []
                    
                    # Collect description between spouse table and next h4 or next h3 (siblings/children/end)
                    desc_element = spouse_table.next_sibling
                    while desc_element and desc_element.name != 'h4' and desc_element.name != 'h3':
                        if desc_element.name == 'p':
                            spouse_description_paragraphs.append(desc_element.get_text(separator=' ', strip=True))
                        elif desc_element.name == 'ul' or desc_element.name == 'ol': # Handle lists in description
                            list_items = [li.get_text(separator=' ', strip=True) for li in desc_element.find_all('li')]
                            spouse_description_paragraphs.append('\n'.join(list_items))
                        desc_element = desc_element.next_sibling
                        if isinstance(desc_element, str):
                            desc_element = desc_element.next_sibling

                    spouse_description = '\n'.join(spouse_description_paragraphs).strip()
                    
                    # Add name and gender from H4 to raw details for _process_person_details to handle
                    if 'Tên' not in spouse_raw_details:
                        spouse_raw_details['Tên'] = spouse_name_gender

                    spouse_processed_data = _process_person_details(spouse_raw_details, spouse_description, key_translation_map)
                    spouse_list.append(spouse_processed_data)
                current_element = spouse_table.next_sibling if spouse_table else current_element.next_sibling
                # Skip any non-tag elements that might be created by markdown
                if isinstance(current_element, str):
                    current_element = current_element.next_sibling
            else:
                current_element = current_element.next_sibling
                if isinstance(current_element, str):
                    current_element = current_element.next_sibling

    family_data['spouses'] = spouse_list # Changed 'spouse' to 'spouses' to hold a list

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

    # --- Extract siblings ---
    siblings_header = soup.find('h3', string=re.compile(r'Các anh em, dâu rể'))
    siblings_list = []
    if siblings_header:
        current_element = siblings_header.next_sibling
        # Siblings are usually just listed as text or links
        while current_element and current_element.name != 'h3': # Stop at next H3 (e.g., Children)
            if current_element.name == 'p':
                # Check for links or plain text names
                links = current_element.find_all('a')
                if links:
                    for link in links:
                        siblings_list.append({
                            'name': link.get_text(strip=True),
                            'url': link.get('href')
                        })
                else: # Plain text siblings
                    text_content = current_element.get_text(strip=True)
                    if text_content and text_content != 'Không có anh em':
                        # Simple split for comma-separated names, need to refine if complex
                        names = [name.strip() for name in text_content.split(',') if name.strip()]
                        for name in names:
                            siblings_list.append({'name': name, 'url': None})
            
            current_element = current_element.next_sibling
            if isinstance(current_element, str):
                current_element = current_element.next_sibling
    family_data['siblings'] = siblings_list

    # --- Extract children from the "Con cái" section explicitly ---
    children_explicit_header = soup.find('h3', string=re.compile(r'Con cái'))
    if children_explicit_header:
        current_element = children_explicit_header.next_sibling
        while current_element and current_element.name != 'h3':
            if current_element.name == 'ul':
                for li in current_element.find_all('li'):
                    link = li.find('a')
                    if link:
                        child_name = link.get_text(strip=True)
                        child_url = link.get('href')
                        # Check if this child is already in children_list (from description)
                        # We can merge them later or prioritize explicit list
                        if not any(c['name'] == child_name for c in family_data['children']):
                             family_data['children'].append({
                                'name': child_name,
                                'url': child_url,
                                'details': None # Details are not explicit here
                            })
                    else:
                        # Handle direct text if no link, though less likely for "Con cái"
                        text_content = li.get_text(strip=True)
                        if text_content and not any(c['name'] == text_content for c in family_data['children']):
                            family_data['children'].append({'name': text_content, 'url': None, 'details': None})
            current_element = current_element.next_sibling
            if isinstance(current_element, str):
                current_element = current_element.next_sibling

    return json.dumps(family_data, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    md_file = 'sample/sample.md' # Changed to markdown file
    json_output = extract_family_data(md_file)
    # print(json_output) # Suppress printing to stdout

    # Write to a file
    with open('family_data.json', 'w', encoding='utf-8') as f:
        f.write(json_output)
    print("Dữ liệu đã được lưu vào 'family_data.json'")