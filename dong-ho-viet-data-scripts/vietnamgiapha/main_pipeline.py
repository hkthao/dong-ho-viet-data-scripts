import os
import sys
import asyncio

from crawl_pipeline import crawl_pipeline
from extract_pipeline import extract_pipeline

async def main_pipeline(family_id: str):
    print(f"Starting main pipeline for Family ID: {family_id}")

    # Run the crawling pipeline
    if not await crawl_pipeline(family_id):
        print(f"Main pipeline failed during crawling for Family ID: {family_id}")
        return False

    # Run the extraction pipeline
    if not await extract_pipeline(family_id):
        print(f"Main pipeline failed during extraction for Family ID: {family_id}")
        return False

    print(f"\nMain pipeline completed successfully for Family ID: {family_id}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main_pipeline.py <family_id>")
        sys.exit(1)
    
    target_family_id = sys.argv[1]
    asyncio.run(main_pipeline(target_family_id))