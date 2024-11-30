import os
import re

def delete_blockchain_files():
    """
    Deletes all blockchain_[i].json files in the current directory.
    """
    # Define the pattern for the files to delete
    pattern = re.compile(r"blockchain_\d+\.json")

    # Get all files in the current directory
    files = os.listdir()

    # Filter files that match the pattern
    blockchain_files = [file for file in files if pattern.match(file)]

    # Delete the matching files
    for file in blockchain_files:
        try:
            os.remove(file)
            print(f"Deleted: {file}")
        except Exception as e:
            print(f"Failed to delete {file}: {e}")

    if not blockchain_files:
        print("No blockchain_[i].json files found.")

if __name__ == "__main__":
    delete_blockchain_files()