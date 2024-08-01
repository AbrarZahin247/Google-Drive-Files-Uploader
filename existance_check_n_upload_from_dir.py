from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

def upload_file_if_not_exists(service_account_file, google_drive_folder_id, local_folder_path):
    # Authenticate and construct the service
    SCOPES = ['https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=SCOPES)
    logging.info("Authenticated with Google Drive API.")
    service = build('drive', 'v3', credentials=credentials)

    # Get list of files in the Google Drive folder
    def list_files_in_drive_folder(folder_id):
        # query = f"'{folder_id}' in parents and trashed = false"
        query = f"'{folder_id}' in parents"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        return results.get('files', [])

    # Get list of files in the local folder
    def list_files_in_local_folder(folder_path):
        return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

    # Check if the file exists in Google Drive
    def file_exists_in_drive(file_name, files_in_drive):
        return any(file['name'] == file_name for file in files_in_drive)

    # Upload file to Google Drive
    def upload_file_to_drive(file_name, folder_id):
        file_path = os.path.join(local_folder_path, file_name)
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        logging.info(f'Uploaded {file_name} to Google Drive at ID {file["id"]} in folder ID {folder_id}.')

    # Get the list of files in the Google Drive folder
    files_in_drive = list_files_in_drive_folder(google_drive_folder_id)
    print("==================================================================")
    print(files_in_drive)
    print("==================================================================")

    # Get the list of files in the local folder
    local_files = list_files_in_local_folder(local_folder_path)

    # Upload files that don't exist in Google Drive
    for local_file in local_files:
        if not file_exists_in_drive(local_file, files_in_drive):
            upload_file_to_drive(local_file, google_drive_folder_id)
        else:
            logging.info(f'{local_file} already exists in Google Drive. Skipping upload.')

# Example usage
service_account_file = 'xyz.json'
gdrive_folder_ids = {'images': '12345678-OoHC-zP8q'}
directory_paths = {'images': r'E:\BUET Files\Msc Research July 2024\YOLOv5_Salient_Map_Guided_Knowledge_Distillation\Okutama_Train_Val_Test\train\labels'}

for key in gdrive_folder_ids.keys():
    print("============starting working on a new folder====================")
    upload_file_if_not_exists(service_account_file, gdrive_folder_ids[key], directory_paths[key])
    print("=============ended working in the folder===================")
