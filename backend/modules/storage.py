import os
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Configuration
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
STORAGE_BASE_URL = os.getenv("SUPABASE_STORAGE_URL")
LOCAL_ADS_DIR = "/home/pi/media/ads" # Ensure this folder exists

supabase: Client = create_client(URL, KEY)

def sync_ads():
    print("🔄 Starting Ad Sync...")
    
    # Ensure local directory exists
    if not os.path.exists(LOCAL_ADS_DIR):
        os.makedirs(LOCAL_ADS_DIR)

    # 1. Fetch active video_filenames from Supabase
    try:
        response = supabase.table("ads").select("video_filename").eq("status", "active").execute()
        active_ads = [item['video_filename'] for item in response.data]
    except Exception as e:
        print(f"❌ Error fetching ads: {e}")
        return

    # 2. Download missing files
    for filename in active_ads:
        local_path = os.path.join(LOCAL_ADS_DIR, filename)
        if not os.path.exists(local_path):
            print(f"📥 Downloading: {filename}")
            file_url = f"{STORAGE_BASE_URL}/{filename}"
            
            with httpx.stream("GET", file_url) as r:
                with open(local_path, "wb") as f:
                    for data in r.iter_bytes():
                        f.write(data)
            print(f"✅ Finished: {filename}")

    # 3. Clean up: Delete local files not in Supabase active list
    local_files = os.listdir(LOCAL_ADS_DIR)
    for local_file in local_files:
        if local_file not in active_ads:
            print(f"🗑️ Deleting old ad: {local_file}")
            os.remove(os.path.join(LOCAL_ADS_DIR, local_file))

    print("🏁 Sync Complete.")