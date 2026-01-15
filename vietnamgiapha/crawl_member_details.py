import requests
from requests import Session
import os
import sys
from bs4 import BeautifulSoup
import re
from utils import check_file_exists

def _clean_member_html(html_content: str) -> str:
    """
    Cleans the member detail HTML content by extracting only the content of a specific <td> tag
    and removing specified tags (p, span, font, img, a) within it.
    """
    soup = BeautifulSoup(html_content, 'lxml') # Use 'lxml' parser for better performance

    target_td = soup.find('td', colspan="2", valign='top', background="https://vietnamgiapha.com/giapha_tml/oldbook//images/bg.jpeg", height="100%")

    if target_td:
        # Remove unwanted tags, keeping their text content where applicable
        for tag_name in ['p', 'span', 'font', 'img', 'a']:
            for tag in target_td.find_all(tag_name):
                # If it's an image or link, replace with a placeholder or remove entirely
                # For now, let's just unwrap them, which keeps the text for <a> and removes <img> entirely
                tag.unwrap() # Removes the tag but keeps its contents (text)

        # Return the cleaned content of the target_td wrapped in a basic HTML structure
        return f"<html><body>{str(target_td)}</body></html>"
    else:
        print("Warning: Specific <td> tag not found in member detail page. Returning original content.")
    
    return html_content # Return original content if specific elements are not found

def _crawl_and_save_html(session: requests.Session, url: str, output_filepath: str):
    """
    Helper function to crawl a URL using requests.Session and save its HTML content to a specified file.
    """
    try:
        print(f"Crawling URL: {url} using requests")
        response = session.get(url, timeout=30) # 30 seconds timeout
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        
        # Explicitly set encoding to utf-8, as declared in the HTML meta tag
        response.encoding = 'utf-8'
        
        html_content = response.text

        # Clean the HTML content
        print("Cleaning member HTML content...")
        html_content_to_save = _clean_member_html(html_content)
        if not html_content_to_save: # Fallback if cleaning returns empty
            print("HTML cleaning returned empty content, using original content.")
            html_content_to_save = html_content 

        # Ensure the directory exists before writing the file
        output_dir = os.path.dirname(output_filepath)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content_to_save)
        print(f"Successfully saved HTML to: {output_filepath}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error crawling {url} with requests: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


def crawl_member_details(family_id: str, members_output_dir: str, pha_he_html_path: str):
    """
    Reads pha_he.html, extracts member detail URLs, crawls them, and saves to members_output_dir.

    Args:
        family_id (str): The ID of the family.
        members_output_dir (str): The directory where member HTML files will be saved.
        pha_he_html_path (str): Path to the pha_he.html file (which contains links to members).
    """
    try:
        with open(pha_he_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        print(f"Successfully read content from: {pha_he_html_path}")
    except FileNotFoundError:
        print(f"Error: {pha_he_html_path} not found.")
        return False
    except Exception as e:
        print(f"Error reading {pha_he_html_path}: {e}")
        return False

    soup = BeautifulSoup(html_content, 'html.parser')

    member_base_url = "https://vietnamgiapha.com/XemChiTietTungNguoi/"
    
    # Ensure the members_output_dir exists
    if not os.path.exists(members_output_dir):
        os.makedirs(members_output_dir)
        print(f"Created directory: {members_output_dir}")

    # Find all <a> tags that have an href containing "javascript:o("
    links = soup.find_all('a', href=re.compile(r'javascript:o\(\d+,\d+\)'))
    print(f"Found {len(links)} member links in {pha_he_html_path}.")

    with Session() as session: # Use a session for persistent connection
        for link in links:
            href = link.get('href')
            print(f"Checking href: {href}")
            match = re.search(r'o\((\d+),(\d+)\)', href)
            if match:
                print(f"Match found for href: {href}")
                extracted_family_id = match.group(1)
                member_id = match.group(2)
                
                # Construct the output file path for this member
                output_filepath = os.path.join(members_output_dir, f"{member_id}.html")
                
                if check_file_exists(output_filepath, f"Member {member_id} HTML"):
                    continue # Skip if file already exists
                
                print(f"Processing member_id: {member_id} from family_id: {extracted_family_id}")
                # Construct the full member detail URL
                member_detail_url = f"{member_base_url}{extracted_family_id}/{member_id}/giapha.html"
                
                _crawl_and_save_html(session, member_detail_url, output_filepath)
    return True

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python crawl_member_details.py <family_id> <members_output_dir> <pha_he_html_path>")
        sys.exit(1)
    
    family_id_to_crawl = sys.argv[1]
    members_output_directory = sys.argv[2]
    pha_he_html_file = sys.argv[3]
    
    crawl_member_details(family_id_to_crawl, members_output_directory, pha_he_html_file)