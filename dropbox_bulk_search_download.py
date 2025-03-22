import os
import csv
import dropbox
from dropbox.exceptions import AuthError
import time

def read_keywords_from_csv(csv_file_path):
    """
    Read keywords from a CSV file, skipping the header row.
    
    Args:
        csv_file_path (str): Path to the CSV file containing keywords
        
    Returns:
        list: List of keywords extracted from the CSV
    """
    keywords = []
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip the header row
            for row in csv_reader:
                if row:  # Check if row is not empty
                    keywords.append(row[0].strip())
        return keywords
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

def authenticate_dropbox(access_token):
    """
    Authenticate to Dropbox using the provided access token.
    
    Args:
        access_token (str): Dropbox API access token
        
    Returns:
        dropbox.Dropbox: Authenticated Dropbox instance or None if authentication fails
    """
    try:
        dbx = dropbox.Dropbox(access_token)
        dbx.users_get_current_account()
        print("Successfully authenticated to Dropbox")
        return dbx
    except AuthError as e:
        print(f"Authentication error: {e}")
        return None

def search_files_by_keyword(dbx, keyword, path=""):
    """
    Search for files in Dropbox folder that match the given keyword.
    
    Args:
        dbx (dropbox.Dropbox): Authenticated Dropbox instance
        keyword (str): Keyword to search for
        path (str): Dropbox folder path to search in
        
    Returns:
        list: List of matching file metadata
    """
    try:
        # Use the files_search method directly
        results = dbx.files_search(query=keyword, path=path)
        matches = results.matches
        
        # Extract file metadata from search results
        matching_files = []
        for match in matches:
            if hasattr(match, 'metadata') and hasattr(match.metadata, 'path_display'):
                file_path = match.metadata.path_display
                matching_files.append({
                    'path': file_path,
                    'name': os.path.basename(file_path)
                })
        
        return matching_files
    except Exception as e:
        print(f"Error searching for files with keyword '{keyword}': {e}")
        return []

def download_file(dbx, dropbox_file_path, local_folder_path):
    """
    Download a file from Dropbox to a local folder.
    
    Args:
        dbx (dropbox.Dropbox): Authenticated Dropbox instance
        dropbox_file_path (str): Path of the file in Dropbox
        local_folder_path (str): Local folder where the file will be downloaded
        
    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        local_file_path = os.path.join(local_folder_path, os.path.basename(dropbox_file_path))
        
        # Check if the file already exists
        if os.path.exists(local_file_path):
            print(f"File '{os.path.basename(dropbox_file_path)}' already exists locally. Skipping.")
            return True
        
        # Download the file
        print(f"Downloading '{dropbox_file_path}' to '{local_file_path}'...")
        dbx.files_download_to_file(local_file_path, dropbox_file_path)
        
        print(f"Successfully downloaded '{os.path.basename(dropbox_file_path)}'")
        return True
    except Exception as e:
        print(f"Error downloading file '{dropbox_file_path}': {e}")
        return False

def main():
    # Configuration - Replace these with your actual values
    CSV_FILE_PATH = "keywords.csv"
    DROPBOX_TOKEN = "YOUR_DROPBOX_ACCESS_TOKEN"
    DROPBOX_FOLDER_PATH = ""  # Root folder by default, specify a path if needed
    LOCAL_DOWNLOAD_FOLDER = "downloaded_files"
    
    # Create local download folder if it doesn't exist
    if not os.path.exists(LOCAL_DOWNLOAD_FOLDER):
        os.makedirs(LOCAL_DOWNLOAD_FOLDER)
        print(f"Created local folder: {LOCAL_DOWNLOAD_FOLDER}")
    
    # Read keywords from CSV
    print(f"Reading keywords from {CSV_FILE_PATH}...")
    keywords = read_keywords_from_csv(CSV_FILE_PATH)
    
    if not keywords:
        print("No keywords found in the CSV file. Exiting.")
        return
    
    print(f"Found {len(keywords)} keywords: {', '.join(keywords)}")
    
    # Authenticate with Dropbox
    dbx = authenticate_dropbox(DROPBOX_TOKEN)
    if not dbx:
        print("Failed to authenticate with Dropbox. Exiting.")
        return
    
    # Dictionary to keep track of all found files to avoid duplicates
    all_found_files = {}
    
    # Search for each keyword
    for keyword in keywords:
        print(f"\nSearching for files matching keyword: '{keyword}'")
        matching_files = search_files_by_keyword(dbx, keyword, DROPBOX_FOLDER_PATH)
        
        if matching_files:
            print(f"Found {len(matching_files)} files matching '{keyword}'")
            
            # Add files to the dictionary to avoid duplicates
            for file in matching_files:
                all_found_files[file['path']] = file
        else:
            print(f"No files found matching '{keyword}'")
        
        # Add a small delay to avoid rate limiting
        time.sleep(1)
    
    # Download all found files
    if all_found_files:
        print(f"\nDownloading {len(all_found_files)} unique files...")
        for file_path, file_info in all_found_files.items():
            download_file(dbx, file_path, LOCAL_DOWNLOAD_FOLDER)
    else:
        print("\nNo files found matching any of the keywords.")
    
    print("\nDownload process completed!")

if __name__ == "__main__":
    main()