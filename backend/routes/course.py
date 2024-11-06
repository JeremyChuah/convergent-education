from flask import Blueprint, redirect, session, url_for, request, jsonify
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
from .services import load_credentials

SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

course_router = Blueprint('courses', __name__)

@course_router.route('/get_courses')
def test_api_request():
    """Test API call to list Google Classroom courses."""
    credentials = load_credentials()

    if not credentials:
        return redirect(url_for('auth.authorize'))

    # Refresh credentials if needed
    if not credentials.valid:
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

    # Initialize Drive service
    drive_service = build('drive', 'v3', credentials=credentials)

    # Fetch courses
    all_courses = fetch_courses(credentials)
    course_id = all_courses['courses'][1]['id']

    # Fetch materials
    materials = fetch_materials(course_id, credentials)
    file_id = materials['courseWorkMaterial'][0]['materials'][0]['driveFile']['driveFile']['id']

    # Fetch file metadata for name
    file_metadata = drive_service.files().get(fileId=file_id, fields="name, mimeType").execute()
    file_name = file_metadata['name']

    # Create folder if it doesn't exist
    download_folder = 'test_folder'
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    # Download materials
    download_materials(file_id, drive_service, file_name, download_folder)

    return "Downloaded"

def download_materials(file_id, service, file_name, folder_path):
    """Download a file from Google Drive into a specified folder."""
    file_path = os.path.join(folder_path, file_name)
    request = service.files().get_media(fileId=file_id)

    with open(file_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")

    print(f"Downloaded {file_name} to {file_path}")

def fetch_courses(credentials):
    """Fetches Google Classroom courses."""
    service = build("classroom", "v1", credentials=credentials)
    courses = service.courses().list().execute()
    return courses

def fetch_materials(course_id, credentials):
    """Fetches course materials for a given course."""
    service = build("classroom", "v1", credentials=credentials)
    course_materials = service.courses().courseWorkMaterials().list(courseId=course_id).execute()
    return course_materials