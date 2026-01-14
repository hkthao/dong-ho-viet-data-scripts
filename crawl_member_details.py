# Run 'playwright install' in your terminal to install necessary browser binaries.
import requests
import os
import sys
from bs4 import BeautifulSoup
import re
import asyncio
from playwright.async_api import async_playwright

async def _crawl_and_save_html(url: str, output_filepath: str):
    """
    Helper function to crawl a URL using Playwright and save its HTML content to a specified file.
    """
    try:
        print(f"Crawling URL: {url} using Playwright")
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            
            # Wait for the network to be idle or for a specific selector if content is dynamic
            # For now, let's wait for network idle as a general approach
            await page.wait_for_load_state("networkidle")
            
            html_content = await page.content()
            await browser.close()

        # Ensure the directory exists before writing the file
        output_dir = os.path.dirname(output_filepath)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Successfully saved HTML to: {output_filepath}")
        return True
    except Exception as e:
        print(f"Error crawling {url} with Playwright: {e}")
        return False

async def crawl_member_details(family_id: str, pha_he_html_path: str):
    """
    Reads pha_he.html, extracts member detail URLs, crawls them, and saves to raw_data/members.

    Args:
        family_id (str): The ID of the family.
        pha_he_html_path (str): Path to the pha_he.html file.
    """
    try:
        with open(pha_he_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"Error: {pha_he_html_path} not found.")
        return
    except Exception as e:
        print(f"Error reading {pha_he_html_path}: {e}")
        return

    soup = BeautifulSoup(html_content, 'html.parser')

    member_base_url = "https://vietnamgiapha.com/XemChiTietTungNguoi/"
    
    # Target directory for member HTML files
    members_output_dir = os.path.join("output", family_id, "raw_data", "members")
    if not os.path.exists(members_output_dir):
        os.makedirs(members_output_dir)
        print(f"Created directory: {members_output_dir}")

    # Find all <a> tags that have an href containing "javascript:o("
    # The links are typically structured as javascript:o(family_id, member_id)
    links = soup.find_all('a', href=re.compile(r'javascript:o\(\d+,\d+\)'))

    for link in links:
        href = link.get('href')
        match = re.search(r'o\((\d+),(\d+)\)', href)
        if match:
            # We already have family_id, but extract it for consistency/validation
            extracted_family_id = match.group(1)
            member_id = match.group(2)
            
            # Construct the full member detail URL
            member_detail_url = f"{member_base_url}{extracted_family_id}/{member_id}/giapha.html"
            
            # Construct the output file path for this member
            output_filepath = os.path.join(members_output_dir, f"{member_id}.html")
            
            await _crawl_and_save_html(member_detail_url, output_filepath)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python crawl_member_details.py <family_id> <pha_he_html_path>")
        sys.exit(1)
    
    family_id_to_crawl = sys.argv[1]
    pha_he_html_file = sys.argv[2]
    
    asyncio.run(crawl_member_details(family_id_to_crawl, pha_he_html_file))