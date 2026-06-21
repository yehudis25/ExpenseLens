import datetime
from google.colab import drive
from googleapiclient.discovery import build
from google.auth import default

FOLDER_ID = "_________"

# authenticate and initialize the Google Drive API Service
try:
    # Authenticate using the environment's default credentials
    creds, _ = default()
    drive_service = build('drive', 'v3', credentials=creds)
except Exception as e:
    print(f"Authentication failed. Make sure Drive is mounted or credentials exist: {e}")
    exit(1)

# Calculate the cutoff timestamp (30 days ago) in ISO format
thirty_days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=30)).isoformat() + 'Z'

# query files created before that timestamp inside your designated folder
query = f"'{FOLDER_ID}' in parents and createdTime < '{thirty_days_ago}'"

try:
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print("No old receipts found to delete.")
    else:
        for item in items:
            drive_service.files().delete(fileId=item['id']).execute()
            print(f"Automatically purged: {item['name']}")

except Exception as e:
    print(f"An error occurred during cleanup: {e}")
