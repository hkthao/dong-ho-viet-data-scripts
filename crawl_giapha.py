import requests
from requests import Session
import os
import sys

# This script uses the 'requests' library for crawling static HTML pages.
# 'requests' is generally more lightweight and efficient for static content
# compared to Playwright, which is better suited for dynamic, JavaScript-rendered pages.
# For dynamic page crawling, refer to crawl_member_details.py.

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

        # Ensure the directory exists before writing the file
        output_dir = os.path.dirname(output_filepath)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
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