"""
Script to cleanup old uploaded videos and analysis results from the server to save disk space.
This script deletes files older than 24 hours in the 'data' directory.
You can run this script using a cron job. Example cron (every night at 2 AM):
0 2 * * * /path/to/venv/bin/python /path/to/project/backend/cleanup_script.py
"""
import os
import time
import shutil

def cleanup_old_files(directory: str, max_age_hours: int = 24):
    """Deletes files in a directory that are older than max_age_hours."""
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist. Skipping.")
        return

    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    deleted_count = 0

    print(f"Cleaning up files older than {max_age_hours} hours in {directory} and its subdirectories...")

    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_creation_time = os.path.getctime(filepath)
            
            if (current_time - file_creation_time) > max_age_seconds:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    print(f"Deleted old file: {filepath}")
                except Exception as e:
                    print(f"Failed to delete {filepath}: {e}")
                    
    print(f"Cleanup complete. Deleted {deleted_count} files.")

if __name__ == "__main__":
    # The data directory is located in the root of the project
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(project_root, "data")
    
    # We can clean both uploads and results if they are in data, 
    # but let's just clean the whole data directory
    cleanup_old_files(data_dir, max_age_hours=24)
