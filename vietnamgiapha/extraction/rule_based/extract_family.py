import json
import re
from bs4 import BeautifulSoup
import os

# 1. Output Schema definition
FINAL_OUTPUT_SCHEMA = {
  "name": "",
  "code": "",
  "description": "",
  "address": "",
  "genealogyRecord": "",
  "progenitorName": "",
  "familyCovenant": "",
  "contactInfo": "",
  "otherInfo": "",
  "avatarBase64": "",
  "visibility": "Private",
  "managerIds": [],
  "viewerIds": [],
  "locationId": ""
}

def clean_text(text: str) -> str:
    """Removes non-breaking spaces and merges multiple spaces into one."""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()

def extract_overview(html: str) -> dict:
    """Extracts overview data from giapha.html (HTML 1)."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n")

    result = {}

    # NAME
    name_div = soup.find('div', align='center')
    if name_div:
        font_tag = name_div.find('font', {'color': '#ff0000', 'size': '6'})
        if font_tag:
            # The name is usually after a <br/> tag within this font tag
            br_tag = font_tag.find('br') # Keep this to check for its existence
            if font_tag:
                name_text = font_tag.get_text(separator=' ', strip=True)
                if name_text:
                    result["name"] = clean_text(name_text)

    # DESCRIPTION (lời nói tiêu biểu)
    m = re.search(r"Lời nói tiêu biểu của học tộc\s+(.*)", text)
    if m:
        result["description"] = clean_text(m.group(1))
    
    # ADDRESS
    # The task.txt suggests a simple regex for address: "Thôn.*?tỉnh.*"
    # From giapha.html, it's more specifically within a font tag inside a div after "Ở tại"
    # Re-using the more robust logic from previous attempts
    address_container_div = None
    for div_tag in soup.find_all('div', align='center'):
        if 'Ở tại' in div_tag.get_text():
            address_container_div = div_tag
            break
            
    if address_container_div:
        address_font = address_container_div.find('font', size='+1')
        if address_font:
            result["address"] = clean_text(address_font.get_text())
    
    contact_info_div = soup.find('div', align='left')

    other_info_content = []
    contact_info_content = []

    if contact_info_div:
        all_children = list(contact_info_div.children)
        delimiter_tag_found = None
        delimiter_index = -1

        for i, child in enumerate(all_children):
            if hasattr(child, 'name') and child.name == 'b' and "Thông tin người quản lý gia phả này:" in child.get_text():
                delimiter_tag_found = child
                delimiter_index = i
                break
            # Also check if it's a <li> containing the b tag
            if hasattr(child, 'name') and child.name == 'li':
                nested_delimiter = child.find('b', string=re.compile(r"Thông tin người quản lý gia phả này:"))
                if nested_delimiter:
                    delimiter_tag_found = nested_delimiter
                    delimiter_index = i # The index of the <li> containing the delimiter
                    break

        if delimiter_tag_found and delimiter_index != -1:
            # Everything before the delimiter_tag's parent element (if nested) or itself (if direct)
            # goes to other_info_content.
            # Everything after goes to contact_info_content.
            
            # Special handling for nested delimiter: if delimiter_tag_found was nested in a <li>
            # we need to split the content of that <li> itself.
            if delimiter_tag_found.name == 'b' and delimiter_tag_found.parent.name == 'li' and all_children[delimiter_index].name == 'li':
                li_element_with_delimiter = all_children[delimiter_index]
                
                # Content before the delimiter within the li
                for pre_element in li_element_with_delimiter.contents:
                    if pre_element == delimiter_tag_found:
                        break
                    if isinstance(pre_element, str) and not clean_text(pre_element): continue
                    other_info_content.append(pre_element)
                
                # Content after the delimiter within the li (should be contact info)
                collect_from_delimiter = False # Initialize the flag
                for post_element in li_element_with_delimiter.contents:
                    if post_element == delimiter_tag_found:
                        # Start collecting from here to contact_info_content
                        collect_from_delimiter = True
                        continue
                    if collect_from_delimiter:
                        if isinstance(post_element, str) and not clean_text(post_element): continue
                        contact_info_content.append(post_element)
                
                # Now, add remaining children of contact_info_div after this li to contact_info_content
                contact_info_content.extend(all_children[delimiter_index+1:])
                
                # Add children before this li to other_info_content
                other_info_content.extend(all_children[:delimiter_index])

            else: # Delimiter is a direct child
                other_info_content.extend(all_children[:delimiter_index])
                contact_info_content.extend(all_children[delimiter_index+1:])
        else:
            # If no delimiter, all content is otherInfo
            other_info_content.extend([child for child in all_children if not (isinstance(child, str) and not clean_text(child))])
    
    # Process other_info_content
    other_info_items_processed = []
    for element in other_info_content:
        if isinstance(element, str) and not clean_text(element):
            continue
        elif element.name == 'li':
            li_text = clean_text(element.get_text())
            if "Tổng quan gia phả:" in li_text and li_text.strip() != "Tổng quan gia phả:":
                parts = li_text.split("Tổng quan gia phả:", 1)
                if clean_text(parts[0]):
                    other_info_items_processed.append(clean_text(parts[0]))
                other_info_items_processed.append("Tổng quan gia phả:")
                if clean_text(parts[1]):
                    other_info_items_processed.append(clean_text(parts[1]))
            else:
                other_info_items_processed.append(li_text)
        elif element.name == 'b': # This will capture "Các ngày lễ giỗ:"
            other_info_items_processed.append(clean_text(element.get_text()))
        elif hasattr(element, 'get_text'): # Catch any other tags that have text content
             if clean_text(element.get_text()):
                other_info_items_processed.append(clean_text(element.get_text()))
        elif isinstance(element, str): # Catch NavigableStrings that are not just whitespace
            if clean_text(element):
                other_info_items_processed.append(clean_text(element))


    result["otherInfo"] = " | ".join(other_info_items_processed).strip()

    # Process contact_info_content
    contact_lines = []
    for element in contact_info_content:
        if isinstance(element, str) and not clean_text(element):
            continue
        elif element.name == 'li':
            li_text = element.get_text(strip=True)
            if any(k in li_text for k in ["Người làm", "Địa chỉ", "Điện thoại", "Email"]):
                if "Email:" in li_text:
                    email_a_tag = element.find('a')
                    if email_a_tag and 'mailto:' in email_a_tag['href']:
                        email_address = clean_text(email_a_tag['href'].replace('mailto:', '')).replace(' ở ', '@').lower()
                        contact_lines.append(f"Email: {email_address}")
                    else:
                        contact_lines.append(clean_text(li_text))
                else:
                    contact_lines.append(clean_text(li_text))
        elif hasattr(element, 'get_text'): # Catch any other tags that have text content
             if clean_text(element.get_text()):
                contact_lines.append(clean_text(element.get_text()))
        elif isinstance(element, str): # Catch NavigableStrings that are not just whitespace
            if clean_text(element):
                contact_lines.append(clean_text(element))

    result["contactInfo"] = " | ".join(contact_lines)


    return result

def extract_progenitor(html: str) -> dict:
    """Extracts progenitor data from thuy_to.html (HTML 2)."""
    soup = BeautifulSoup(html, "html.parser")

    content_div = soup.find("div", align="justify")
    if not content_div:
        return {}

    full_text = clean_text(content_div.get_text("\n"))

    result = {}
    result["genealogyRecord"] = full_text

    # PROGENITOR NAME
    # Adjusted regex to capture full Vietnamese names including diacritics
    m = re.search(r"CỤ TỔ\s+([A-ZĐÁÀẢẠÃĂẮẰẲẶẪÂẤẦẨẬẪÈÉẺẸẼÊẾỀỂỆỄÌÍỈỊĨÒÓỎỌÕÔỐỒỔỘỖƠỚỜỞỢỠÙÚỦỤŨƯỨỪỬỰỮỲÝỶỴỸ\s]+)", full_text)
    if m:
        result["progenitorName"] = clean_text(m.group(1))

    return result

def extract_phaky(html: str) -> dict:
    """Extracts genealogy record data from pha_ky_gia_su.html."""
    soup = BeautifulSoup(html, "html.parser")
    result = {}

    # Find the main content <td> using the background and height attributes
    main_content_td = soup.find('td', {'valign': 'top', 'background': True, 'height': '100%'})
    
    if main_content_td:
        # Inside this <td>, find the <div> with align="justify"
        justify_div = main_content_td.find('div', align='justify')
        if justify_div:
            result["genealogyRecord"] = clean_text(justify_div.get_text())

    return result
def extract_tocuoc(html: str) -> dict:
    """Extracts family covenant data from toc_uoc.html."""
    soup = BeautifulSoup(html, "html.parser")
    result = {}

    # Find the main content <td> using the background and height attributes
    main_content_td = soup.find('td', {'valign': 'top', 'background': True, 'height': '100%'})

    if main_content_td:
        # Check if "TỘC ƯỚC - GIA PHÁP" heading exists within this main content block
        heading_td = main_content_td.find('td', string=re.compile(r"TỘC ƯỚC - GIA PHÁP"))
        if heading_td:
            # Inside the same main content block, find the div with align="justify"
            justify_div = main_content_td.find('div', align='justify')
            if justify_div:
                family_covenant_text = []
                for element in justify_div.find_all(['p', 'span']):
                    if element.name == 'p' and element.get_text(strip=True) == '':
                        continue
                    family_covenant_text.append(element.get_text())
                result["familyCovenant"] = clean_text(" ".join(family_covenant_text))

    return result

def build_schema(overview: dict, progenitor: dict, phaky: dict, tocuoc: dict, folder_name: str) -> dict:
    """Combines extracted data into the final schema."""
    final_output = FINAL_OUTPUT_SCHEMA.copy()

    final_output["name"] = overview.get("name", "")
    final_output["code"] = f"GPVN-{folder_name}"
    final_output["description"] = overview.get("description", "")
    final_output["address"] = overview.get("address", "")
    
    # Combine genealogyRecord from progenitor and phaky
    genealogy_records = []
    if progenitor.get("genealogyRecord"):
        genealogy_records.append(progenitor.get("genealogyRecord"))
    if phaky.get("genealogyRecord"):
        genealogy_records.append(phaky.get("genealogyRecord"))
    final_output["genealogyRecord"] = " ".join(genealogy_records).strip()

    final_output["progenitorName"] = progenitor.get("progenitorName", "")
    final_output["familyCovenant"] = tocuoc.get("familyCovenant", "") # Now from tocuoc
    final_output["contactInfo"] = overview.get("contactInfo", "")
    final_output["otherInfo"] = overview.get("otherInfo", "")
    # Default values are already set in FINAL_OUTPUT_SCHEMA

    return final_output

if __name__ == "__main__":
    sample_files_map = {
        "giapha": "vietnamgiapha/sample/family/giapha.html",
        "thuy_to": "vietnamgiapha/sample/thuy_to.html",
        "pha_ky_gia_su": "vietnamgiapha/sample/pha_ky_gia_su.html",
        "toc_uoc": "vietnamgiapha/sample/toc_uoc.html",
    }
    
    output_dir = "output_json_family"
    os.makedirs(output_dir, exist_ok=True)

    giapha_html_content = ""
    thuy_to_html_content = ""
    phaky_html_content = ""
    tocuoc_html_content = ""

    if "giapha" in sample_files_map:
        with open(sample_files_map["giapha"], "r", encoding="utf-8") as f:
            giapha_html_content = f.read()
    
    if "thuy_to" in sample_files_map:
        with open(sample_files_map["thuy_to"], "r", encoding="utf-8") as f:
            thuy_to_html_content = f.read()

    if "pha_ky_gia_su" in sample_files_map:
        with open(sample_files_map["pha_ky_gia_su"], "r", encoding="utf-8") as f:
            phaky_html_content = f.read()
            
    if "toc_uoc" in sample_files_map:
        with open(sample_files_map["toc_uoc"], "r", encoding="utf-8") as f:
            tocuoc_html_content = f.read()


    overview_data = extract_overview(giapha_html_content)
    progenitor_data = extract_progenitor(thuy_to_html_content)
    phaky_data = extract_phaky(phaky_html_content)
    tocuoc_data = extract_tocuoc(tocuoc_html_content)
    
    final_family_data = build_schema(overview_data, progenitor_data, phaky_data, tocuoc_data, "sample")

    output_json_path = os.path.join(output_dir, "family_data.json")
    with open(output_json_path, "w", encoding="utf-8") as json_f:
        json.dump(final_family_data, json_f, ensure_ascii=False, indent=2)
    print(f"Combined family data written to {output_json_path}")
    print("-" * 30)

