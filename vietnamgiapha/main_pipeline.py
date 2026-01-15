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

async def run_pipeline_for_range(start_id: int, end_id: int):
    failed_ids = []
    log_file_path = "failed_crawls.txt"

    for i in range(start_id, end_id + 1):
        family_id = str(i)
        print(f"--- Processing Family ID: {family_id} ---")
        try:
            success = await main_pipeline(family_id)
            if not success:
                failed_ids.append(family_id)
                with open(log_file_path, "a") as f:
                    f.write(f"{family_id}\n")
                print(f"Failed to process Family ID: {family_id}. Added to {log_file_path}")
        except Exception as e:
            failed_ids.append(family_id)
            with open(log_file_path, "a") as f:
                f.write(f"{family_id} (Error: {e})\n")
            print(f"An error occurred while processing Family ID: {family_id}: {e}. Added to {log_file_path}")
        print(f"--- Finished processing Family ID: {family_id} ---\n")

    if failed_ids:
        print(f"\n--- Summary: Failed to process {len(failed_ids)} family IDs ---")
        print(f"Failed IDs: {', '.join(failed_ids)}")
        print(f"Details logged to {log_file_path}")
    else:
        print("\n--- Summary: All family IDs processed successfully ---")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        target_family_id = sys.argv[1]
        asyncio.run(main_pipeline(target_family_id))
    elif len(sys.argv) == 3:
        try:
            start_id = int(sys.argv[1])
            end_id = int(sys.argv[2])
            if start_id > end_id:
                print("Error: start_id cannot be greater than end_id.")
                sys.exit(1)
            asyncio.run(run_pipeline_for_range(start_id, end_id))
        except ValueError:
            print("Error: start_id and end_id must be integers.")
            print("Usage: python main_pipeline.py <family_id>")
            print("       python main_pipeline.py <start_id> <end_id>")
            sys.exit(1)
    else:
        print("Usage: python main_pipeline.py <family_id>")
        print("       python main_pipeline.py <start_id> <end_id>")
        sys.exit(1)
