import json
from bs4 import BeautifulSoup
import re
import sys
import os

def extract_giapha_info(html_file_path: str):
    """
    Extracts specific information from the gia pha HTML content and returns it as a dictionary.

    Args:
        html_file_path (str): The path to the HTML file.

    Returns:
        dict: A dictionary containing the extracted information.
    """
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    
    extracted_data = {}

    # 1. Family Name
    family_name_tag = soup.find('meta', property='og:title')
    if family_name_tag:
        extracted_data['family_name'] = family_name_tag.get('content').replace("Gia phả: ", "").strip()
    else:
        title_tag = soup.find('title')
        if title_tag:
            extracted_data['family_name'] = title_tag.get_text().replace("Gia phả: ", "").strip()
        else:
            extracted_data['family_name'] = None

    # Try to extract info from og:description first
    og_description_tag = soup.find('meta', property='og:description')
    if og_description_tag:
        og_content = og_description_tag.get('content')
        
        # Address from og:description
        address_match = re.search(r'(Thôn (.*?) - Làng (.*?) - xã (.*?) - tỉnh (.*?)\.)', og_content)
        if address_match:
            extracted_data['address'] = address_match.group(1).strip()
        
        # Number of generations, families, people from og:description
        num_generations_match = re.search(r'Số đời: (\d+)', og_content)
        if num_generations_match:
            extracted_data['number_of_generations'] = num_generations_match.group(1)
            
        num_families_match = re.search(r'Số gia đình: (\d+)', og_content)
        if num_families_match:
            extracted_data['number_of_families'] = num_families_match.group(1)
            
        num_people_match = re.search(r'Số người: (\d+)', og_content)
        if num_people_match:
            extracted_data['number_of_people'] = num_people_match.group(1)
            
        # Manager name from og:description
        manager_name_match = re.search(r'Tên người quản lý: Ông (.*?)"', og_content)
        if manager_name_match:
            if 'manager_info' not in extracted_data:
                extracted_data['manager_info'] = {}
            extracted_data['manager_info']['manager_name'] = "Ông " + manager_name_match.group(1).strip()

    # Fallback/supplement for Address from body
    if 'address' not in extracted_data or not extracted_data['address']:
        address_div = soup.find('div', align='center')
        if address_div:
            font_tag = address_div.find('font', size='+1')
            if font_tag and 'Thôn Tam Kỳ' in font_tag.get_text():
                extracted_data['address'] = font_tag.get_text(strip=True).replace('\\n', ' ').strip()

    # Description (Slogan) from body
    slogan_div = None
    for div in soup.find_all('div', align='center'):
        if 'Lời nói tiêu biểu của học tộc' in div.get_text():
            slogan_div = div
            break
            
    if slogan_div:
        font_tag = slogan_div.find('font', size='+1')
        if font_tag:
            extracted_data['description'] = font_tag.get_text(strip=True)
        else:
            extracted_data['description'] = None
    else:
        extracted_data['description'] = None


    # 3. Stats (Number of generations, families, people) - Fallback/Supplement from body
    # Only if not already extracted from og:description or if body has more specific info
    if 'number_of_generations' not in extracted_data or 'number_of_families' not in extracted_data or 'number_of_people' not in extracted_data:
        total_overview_b = soup.find('b', string=re.compile(r'Tổng quan gia phả'))
        if total_overview_b:
            # Find the parent div of the b tag
            parent_div = total_overview_b.find_parent('div')
            if parent_div:
                # Find all LI tags within this div after the b tag
                li_tags = parent_div.find_all('li')
                for li in li_tags:
                    text = li.get_text(strip=True)
                    if 'Số đời từ thuỷ tổ tới con cháu' in text:
                        extracted_data['number_of_generations'] = li.find('b').get_text(strip=True) if li.find('b') else text.replace('Số đời từ thuỷ tổ tới con cháu', '').strip()
                    elif 'Số lượng gia đình:' in text:
                        extracted_data['number_of_families'] = li.find('b').get_text(strip=True) if li.find('b') else text.replace('Số lượng gia đình:', '').strip()
                    elif 'Số người:' in text:
                        extracted_data['number_of_people'] = li.find('b').get_text(strip=True) if li.find('b') else text.replace('Số người:', '').strip()

    # 4. Manager Information - Fallback/Supplement from body
    # Ensure manager_info exists, potentially from og:description
    if 'manager_info' not in extracted_data:
        extracted_data['manager_info'] = {}

    manager_info_from_body = {}
    manager_overview_b = soup.find('b', string=re.compile(r'Thông tin người quản lý gia phả này'))
    if manager_overview_b:
        parent_div = manager_overview_b.find_parent('div')
        if parent_div:
            li_tags = parent_div.find_all('li')
            for li in li_tags:
                # Get the bold tag within the li
                b_tag = li.find('b')
                if not b_tag:
                    continue # Skip if no bold tag found
                
                key_text = b_tag.get_text(strip=True)
                # Get the text directly after the bold tag
                value_text = b_tag.next_sibling
                if value_text:
                    value_text = str(value_text).strip()
                else:
                    value_text = ""

                if 'Người làm:' in key_text:
                    manager_info_from_body['manager_name'] = value_text
                elif 'Địa chỉ:' in key_text:
                    manager_info_from_body['manager_address'] = value_text
                elif 'Điện thoại:' in key_text:
                    manager_info_from_body['manager_phone'] = value_text
                elif 'Email:' in key_text:
                    email_tag = li.find('a')
                    if email_tag:
                        manager_info_from_body['manager_email'] = email_tag.get_text(strip=True)
                    else:
                        manager_info_from_body['manager_email'] = value_text # Fallback to text after <b> if no <a>
    
    # Merge manager info from body, prioritizing body for full details
    extracted_data['manager_info'].update(manager_info_from_body)

    return extracted_data

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_giapha_info.py <html_file_path>")
        sys.exit(1)
    
    html_input_path = sys.argv[1]
    
    # Extract family_id from the html_input_path (e.g., "output/1691/giapha.html" -> "1691")
    # This assumes html_input_path will always be in the format output/{family_id}/raw_data/giapha.html
    family_id_from_path = html_input_path.split(os.sep)[-3] # Get the third to last element
    
    output_base_dir = os.path.join("output", family_id_from_path)
    output_dir = os.path.join(output_base_dir, "data")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    output_filename = f"giapha_info_{family_id_from_path}.json"
    output_filepath = os.path.join(output_dir, output_filename)

    extracted_data = extract_giapha_info(html_input_path)

    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=4)
    print(f"Successfully extracted information and saved to: {output_filepath}")