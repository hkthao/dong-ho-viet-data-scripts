import os
import subprocess
import sys
import asyncio
from bs4 import BeautifulSoup

async def run_command(command_parts: list, description: str):
    """Executes a shell command asynchronously and prints its output."""
    print(f"\n--- {description} ---")
    try:
        process = await asyncio.create_subprocess_exec(
            *command_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if stdout:
            print(stdout.decode().strip())
        if stderr:
            print("Stderr:\n", stderr.decode().strip())

        if process.returncode != 0:
            print(f"Error during {description}: Command exited with code {process.returncode}. Command: {' '.join(command_parts)}")
            return False
        return True
    except FileNotFoundError:
        print(f"Error: Command not found for {description}. Ensure {command_parts[0]} is in PATH or correctly specified. Command: {' '.join(command_parts)}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during {description}: {e}. Command: {' '.join(command_parts)}")
        return False

def check_file_exists(filepath: str, description: str):
    """Checks if a file exists and prints a message."""
    if os.path.exists(filepath):
        print(f"'{description}' already exists at {filepath}. Skipping step.")
        return True
    return False

def check_directory_not_empty(dirpath: str, description: str):
    """Checks if a directory exists and is not empty."""
    if os.path.exists(dirpath) and os.listdir(dirpath):
        print(f"'{description}' directory already exists and is not empty at {dirpath}. Skipping step.")
        return True
    return False

def remove_html_tag_attributes(html_content: str) -> str:
    """
    Removes all attributes from HTML tags in the given HTML content.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    for tag in soup.find_all(True): # find_all(True) gets all tags
        tag.attrs = {} # Remove all attributes
    return str(soup)

def remove_html_tags(html_content: str) -> str:
    """
    Removes all HTML tags from the given HTML content, returning only the text.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    return soup.get_text(separator=' ', strip=True)

def remove_specific_html_tags(html_content: str, tags_to_unwrap: list) -> str:
    """
    Removes specified HTML tags from the given HTML content while keeping their text content.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    for tag_name in tags_to_unwrap:
        for tag in soup.find_all(tag_name):
            tag.unwrap()
    return str(soup)


