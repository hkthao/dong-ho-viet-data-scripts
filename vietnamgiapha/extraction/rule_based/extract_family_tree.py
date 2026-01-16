import json
import re
from bs4 import BeautifulSoup
import os

def extract_data(html_file_path):
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the main content area for family tree
    # This is the TD that contains the PHẢ HỆ - PHẢ ĐỒ TOÀN GIA TỘC heading and the div with the members
    main_content_td = None
    for td in soup.find_all('td', valign='top', background=re.compile(r'images/bg\.jpeg')):
        if td.find('td', string=re.compile(r'PHẢ HỆ - PHẢ ĐỒ TOÀN GIA TỘC')):
            main_content_td = td
            break

    if not main_content_td:
        raise ValueError("Could not find the main content TD for family tree.")

    # Find the div containing the family members
    family_members_div = main_content_td.find('div', valign='top')
    if not family_members_div:
        raise ValueError("Could not find the div containing family members.")

    persons_in_order = []
    
    # Each person entry is an <a> tag
    for a_tag in family_members_div.find_all('a'): # Find all <a> tags first
        href = a_tag.get('href', '') # Get href attribute, default to empty string if not found

        # Extract fid and id from javascript:o(fid,id)
        js_match = re.search(r'javascript:o\((\d+),(\d+)\)', href)
        if not js_match:
            continue # Skip if href does not match the expected javascript pattern

        fid, person_id = js_match.groups()
        full_id = f"GPVN-{fid}-{person_id}"
        person_raw_text = a_tag.get_text(strip=True)


        # Determine generation from the numeric prefix (e.g., "1.1", "2.1")
        generation_match = re.match(r'^(\d+)\.\d+\s(.+)', person_raw_text)
        if not generation_match:
            # Fallback if no generation prefix is found, though task.txt implies it should always be there
            generation = None
            display_name_and_spouses = person_raw_text
        else:
            generation = int(generation_match.group(1))
            display_name_and_spouses = generation_match.group(2)

        # Extract main person's name and spouses
        parts = [p.strip() for p in display_name_and_spouses.split('-')]
        main_person_name = parts[0]
        spouses = []
        if len(parts) > 1:
            for spouse_index, spouse_name_raw in enumerate(parts[1:]):
                spouse_id = f"{full_id}-S{spouse_index + 1}" # Generate unique ID for spouse
                # Check for role in parentheses, e.g., "Tô Thị Xuyến (Chính thất)"
                spouse_match = re.match(r'(.+?)\s*\((.+?)\)', spouse_name_raw)
                if spouse_match:
                    spouses.append({"id": spouse_id, "name": spouse_match.group(1).strip(), "role": spouse_match.group(2).strip()})
                else:
                    spouses.append({"id": spouse_id, "name": spouse_name_raw.strip()})
        
        persons_in_order.append({
            "id": full_id,
            "name": main_person_name,
            "generation": generation,
            "spouses": spouses,
            "children": [] # Will be populated by the stack algorithm
        })
    
    # Apply Stack Algorithm for parent-child relationships
    roots = []
    stack = [] # Stores potential parents

    for person_node in persons_in_order:
        current_generation = person_node["generation"]

        # Pop from stack until we find a parent or stack is empty
        while stack and stack[-1]["generation"] >= current_generation:
            stack.pop()

        if not stack:
            # This is a root node (no parent in the current branch)
            roots.append(person_node)
        else:
            # The top of the stack is the parent
            stack[-1]["children"].append(person_node)
            # No parentId needed if we output as a tree structure

        stack.append(person_node)
        
    return roots


