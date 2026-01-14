import requests
import os
import sys

def _crawl_and_save_html(url: str, output_filepath: str):
    """
    Helper function to crawl a URL and save its HTML content to a specified file.
    """
    try:
        print(f"Crawling URL: {url}")
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

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

def crawl_giapha_html(family_id: str):
    """
    Crawls multiple HTML pages for a given family ID and saves them to appropriate files.

    Args:
        family_id (str): The ID of the family to crawl.
    """
    
    # Define directories
    family_id_dir = family_id
    raw_data_dir = os.path.join(family_id_dir, "raw_data")

    # Create directories if they don't exist
    if not os.path.exists(family_id_dir):
        os.makedirs(family_id_dir)
        print(f"Created directory: {family_id_dir}")
    if not os.path.exists(raw_data_dir):
        os.makedirs(raw_data_dir)
        print(f"Created directory: {raw_data_dir}")

    # URLs to crawl and their corresponding output filenames
    pages_to_crawl = {
        "giapha.html": f"https://vietnamgiapha.com/XemGiaPha/{family_id}/giapha.html",
        "pha_ky_gia_su.html": f"https://vietnamgiapha.com/XemPhaKy/{family_id}/pha_ky_gia_su.html",
        "thuy_to.html": f"https://vietnamgiapha.com/XemThuyTo/{family_id}/thuy_to.html",
        "toc_uoc.html": f"https://vietnamgiapha.com/XemTocUoc/{family_id}/toc_uoc.html",
        "pha_he.html": f"https://vietnamgiapha.com/XemPhaHe/{family_id}/pha_he.html",
    }

    for filename, url in pages_to_crawl.items():
        if filename == "giapha.html":
            output_filepath = os.path.join(family_id_dir, filename)
        else:
            output_filepath = os.path.join(raw_data_dir, filename)
        
        _crawl_and_save_html(url, output_filepath)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crawl_giapha.py <family_id>")
        sys.exit(1)
    
    family_id_to_crawl = sys.argv[1]
    crawl_giapha_html(family_id_to_crawl)