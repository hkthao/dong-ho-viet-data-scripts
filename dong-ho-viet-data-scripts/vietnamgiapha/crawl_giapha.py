import requests
from requests import Session
import os
import sys
from bs4 import BeautifulSoup

# This script uses the 'requests' library for crawling static HTML pages.
# 'requests' is generally more lightweight and efficient for static content
# compared to Playwright, which is better suited for dynamic, JavaScript-rendered pages.
# For dynamic page crawling, refer to crawl_member_details.py.

def _clean_giapha_html(html_content: str) -> str:
    """
    Cleans the giapha.html content by extracting only the content of the first <tr>
    within the first <table> found inside a specific <td> tag.
    """
    soup = BeautifulSoup(html_content, 'lxml') # Use 'lxml' parser for better performance

    target_td = soup.find('td', valign='top', background="https://vietnamgiapha.com/giapha_tml/oldbook//images/bg.jpeg", height="100%")

    if target_td:
        first_table = target_td.find('table')
        if first_table:
            first_tr = first_table.find('tr')
            if first_tr:
                # Return the content of the first <tr> within a simple HTML structure
                return f"<html><body><table>{str(first_tr)}</table></body></html>"
            else:
                print("Warning: First <tr> not found within the first <table> in target <td>.")
        else:
            print("Warning: First <table> not found within target <td>.")
    else:
        print("Warning: Specific <td> tag not found.")
    
    return html_content # Return original content if specific elements are not found

def _crawl_and_save_html_with_requests(session: requests.Session, url: str, output_filepath: str):
    """
    Helper function to crawl a URL and save its HTML content to a specified file using requests.Session.
    """
    try:
        print(f"Crawling URL: {url}")
        response = session.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        # Explicitly set encoding to utf-8, as declared in the HTML meta tag
        response.encoding = 'utf-8'

        html_content_to_save = response.text
        # Clean the HTML content if it's giapha.html
        if os.path.basename(output_filepath) == "giapha.html":
            print("Cleaning giapha.html content...")
            html_content_to_save = _clean_giapha_html(response.text)
            if not html_content_to_save: # If cleaning failed, use original content or handle as error
                print("HTML cleaning returned empty content, using original content.")
                html_content_to_save = response.text # Fallback to original content

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
        print(f"Error crawling {url}: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def crawl_giapha_html(family_id: str, output_giapha_html_path: str, output_base_dir_for_others: str):
    """
    Crawls multiple HTML pages for a given family ID and saves them to appropriate files.
    giapha.html is saved to output_giapha_html_path.
    Other related HTML files are saved to output_base_dir_for_others.

    Args:
        family_id (str): The ID of the family to crawl.
        output_giapha_html_path (str): The full path where giapha.html will be saved.
        output_base_dir_for_others (str): The base directory for other HTML files.
    """
    
    # Ensure the directories exist
    os.makedirs(os.path.dirname(output_giapha_html_path), exist_ok=True)
    os.makedirs(output_base_dir_for_others, exist_ok=True)
    print(f"Created directory: {os.path.dirname(output_giapha_html_path)}")
    print(f"Created directory: {output_base_dir_for_others}")

    # URLs to crawl and their corresponding output filenames
    pages_to_crawl = {
        "giapha.html": f"https://vietnamgiapha.com/XemGiaPha/{family_id}/giapha.html",
        "pha_ky_gia_su.html": f"https://vietnamgiapha.com/XemPhaKy/{family_id}/pha_ky_gia_su.html",
        "thuy_to.html": f"https://vietnamgiapha.com/XemThuyTo/{family_id}/thuy_to.html",
        "toc_uoc.html": f"https://vietnamgiapha.com/XemTocUoc/{family_id}/toc_uoc.html",
        "pha_he.html": f"https://vietnamgiapha.com/XemPhaHe/{family_id}/pha_he.html",
    }

    with Session() as session:
        for filename, url in pages_to_crawl.items():
            if filename == "giapha.html":
                output_filepath = output_giapha_html_path
            else:
                output_filepath = os.path.join(output_base_dir_for_others, filename)
            
            _crawl_and_save_html_with_requests(session, url, output_filepath)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python crawl_giapha.py <family_id> <output_giapha_html_path> <output_base_dir_for_others>")
        sys.exit(1)
    
    family_id_to_crawl = sys.argv[1]
    output_giapha_html_filepath = sys.argv[2]
    output_base_dir_for_other_files = sys.argv[3]
    crawl_giapha_html(family_id_to_crawl, output_giapha_html_filepath, output_base_dir_for_other_files)