import os
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
URL = os.getenv("SUPABASE_URL")
# Using SERVICE_ROLE_KEY for administrative backend access (bypass RLS if necessary)
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
# Specific bucket URL for downloading media
PROJECT_ID = URL.split("//")[1].split(".")[0] if URL else "jnvadpuejjoakivfjcue"
STORAGE_BUCKET_URL = f"https://{PROJECT_ID}.supabase.co/storage/v1/object/public/adorix-ads-media"

# Initialize local ads directory path relative to project root (backend/ads/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_ADS_DIR = os.path.join(BASE_DIR, "ads")

if not URL or not KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) must be set in .env")

supabase: Client = create_client(URL, KEY)

def sync_ads():
    """
    Synchronizes ads from Supabase storage to local filesystem.
    - Fetches active ads from 'ads' table where status is 'active'.
    - Ensures backend/ads/ exists.
    - Downloads missing active ad files from Supabase Storage.
    - Deletes any local files in backend/ads/ that are no longer marked as 'active' in the database.
    """
    print("🔄 Starting Ad Sync...")
    
    # Ensure local directory exists
    if not os.path.exists(LOCAL_ADS_DIR):
        print(f"📁 Creating local ads directory: {LOCAL_ADS_DIR}")
        os.makedirs(LOCAL_ADS_DIR, exist_ok=True)

    # 1. Fetch active video_filenames from Supabase
    try:
        print("🔍 Fetching active ads from database...")
        response = supabase.table("ads").select("video_filename").eq("status", "active").execute()
        active_ads = [item['video_filename'] for item in response.data if item.get('video_filename')]
        print(f"📋 Found {len(active_ads)} active ad(s) in database.")
    except Exception as e:
        print(f"❌ Error fetching ads from Supabase: {e}")
        return

    # 2. Compare and Download missing files
    for filename in active_ads:
        local_path = os.path.join(LOCAL_ADS_DIR, filename)
        if not os.path.exists(local_path):
            print(f"📥 Downloading missing ad: {filename}")
            file_url = f"{STORAGE_BUCKET_URL}/{filename}"
            
            try:
                # Using httpx to download the file from the public storage URL
                with httpx.stream("GET", file_url) as r:
                    r.raise_for_status()
                    with open(local_path, "wb") as f:
                        for chunk in r.iter_bytes():
                            f.write(chunk)
                print(f"✅ Successfully downloaded: {filename}")
            except Exception as e:
                print(f"❌ Failed to download {filename}: {e}")
        else:
            # File already exists locally, no action needed
            pass

    # 3. Clean up: Delete local files in backend/ads/ that are no longer marked as 'active'
    try:
        local_files = os.listdir(LOCAL_ADS_DIR)
        for local_file in local_files:
            if local_file not in active_ads:
                file_to_delete = os.path.join(LOCAL_ADS_DIR, local_file)
                if os.path.isfile(file_to_delete):
                    print(f"🗑️ Deleting inactive/obsolete ad: {local_file}")
                    os.remove(file_to_delete)
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

    print("🏁 Sync Complete.")

if __name__ == "__main__":
    sync_ads()