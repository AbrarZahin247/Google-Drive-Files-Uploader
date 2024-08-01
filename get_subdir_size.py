import os
import logging
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError

def get_folder_sizes(service, folder_id, parent_name="Root"):
    """
    Calculate the total size of files in each subdirectory under the given Google Drive folder ID.

    Args:
        service: Authorized Google Drive API service instance.
        folder_id: ID of the parent Google Drive folder.
        parent_name: Name of the parent folder (used for logging).

    Returns:
        A dictionary where keys are folder paths and values are the total size of files in those folders in bytes.
    """
    try:
        # Store the total size of files for each folder path
        folder_sizes = {}

        # Function to list all files and subfolders in the specified folder
        def list_files_and_subfolders(service, folder_id):
            page_token = None
            while True:
                response = service.files().list(
                    q=f"'{folder_id}' in parents",
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, size)',
                    pageToken=page_token
                ).execute()
                for file in response.get('files', []):
                    yield file
                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break

        # Recursive function to traverse the folder structure
        def traverse_folder(service, folder_id, path):
            total_size = 0
            subfolder_paths = []

            # List all items in the current folder
            for item in list_files_and_subfolders(service, folder_id):
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # It's a subfolder, traverse it
                    subfolder_paths.append((item['id'], os.path.join(path, item['name'])))
                else:
                    # It's a file, add its size to the total
                    size = int(item.get('size', 0))
                    total_size += size

            # Store the total size of files for the current folder
            folder_sizes[path] = total_size
            logging.info(f"Folder '{path}' contains files with a total size of {total_size} bytes.")
            print(f"Folder '{path}' contains files with a total size of {total_size} bytes.")

            # Recursively calculate sizes in subfolders
            for subfolder_id, subfolder_path in subfolder_paths:
                traverse_folder(service, subfolder_id, subfolder_path)

        # Start traversal from the root folder
        traverse_folder(service, folder_id, parent_name)

        return folder_sizes

    except HttpError as error:
        logging.error(f"An error occurred: {error}")
        return {}

def authenticate(service_account_file):
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=SCOPES)
    logging.info("Authenticated with Google Drive API.")
    return creds

# Example usage:
if __name__ == '__main__':
    service_account_file = "credentials.json"
    creds = authenticate(service_account_file)
    service = build('drive', 'v3', credentials=creds)
    parent_folder_id = ""
    
    folder_sizes = get_folder_sizes(service, parent_folder_id)
    for folder_path, size in folder_sizes.items():
        size_mb = size / 1_048_576  # Convert bytes to MB
        size_gb = size / 1_073_741_824  # Convert bytes to GB
        print(f"Folder '{folder_path}' contains files with a total size of {size} bytes, "
            f"{size_mb:.2f} MB, {size_gb:.2f} GB.")
