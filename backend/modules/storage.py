import os
import httpx
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
URL = os.getenv("SUPABASE_URL")
# Using SERVICE_ROLE_KEY for administrative backend access (bypass RLS)
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

# Root directory: storage.py is in backend/modules/
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Local ads directory path (backend/ads)
LOCAL_ADS_DIR = os.path.join(ROOT_DIR, "backend", "ads")
MANIFEST_FILE = os.path.join(LOCAL_ADS_DIR, "sync_manifest.json")
MAPPING_FILE = os.path.join(LOCAL_ADS_DIR, "mapping.json")

# Specific bucket URL for downloading media
PROJECT_ID = URL.split("//")[1].split(".")[0] if URL else "jnvadpuejjoakivfjcue"
STORAGE_BUCKET_URL = f"https://{PROJECT_ID}.supabase.co/storage/v1/object/public/adorix-ads-media"

if not URL or not KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) must be set in .env")

supabase: Client = create_client(URL, KEY)

def load_manifest():
    if os.path.exists(MANIFEST_FILE):
        try:
            with open(MANIFEST_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading manifest: {e}")
    return {}

def save_manifest(manifest):
    try:
        with open(MANIFEST_FILE, "w") as f:
            json.dump(manifest, f, indent=4)
    except Exception as e:
        print(f"❌ Error saving manifest: {e}")

def sync_ads():
    """
    Synchronizes ads from Supabase storage to local filesystem.
    - Uses a manifest to track versions and handle updates of existing files.
    - Unified path: backend/ads
    """
    print("🔄 Starting Optimized Ad Sync...")
    
    # Ensure local directory exists
    if not os.path.exists(LOCAL_ADS_DIR):
        print(f"📁 Creating local ads directory: {LOCAL_ADS_DIR}")
        os.makedirs(LOCAL_ADS_DIR, exist_ok=True)

    manifest = load_manifest()
    new_manifest = {}

    # 1. Fetch active ads (filenames and IDs) from Supabase
    try:
        print("🔍 Fetching active ads from database...")
        # We select video_filename, ad_id (UUID), and description
        response = supabase.table("ads").select("ad_id, video_filename, description").eq("status", "active").execute()
        
        active_filenames = {item['video_filename'] for item in response.data if item.get('video_filename')}
        # Create mapping of filename -> ad_id
        mapping = {item['video_filename']: item['ad_id'] for item in response.data if item.get('video_filename')}
        
        print(f"📋 Found {len(active_filenames)} active ad(s) in database.")
        
        # Save mapping.json
        with open(MAPPING_FILE, "w") as f:
            json.dump(mapping, f, indent=4)
        print(f"📄 Mapping updated: {MAPPING_FILE}")
        
    except Exception as e:
        print(f"❌ Error fetching ads from database: {e}")
        return

    # 2. Get metadata from Supabase Storage to check for updates
    try:
        print("🔍 Fetching storage metadata...")
        # List all files in the bucket
        storage_files = supabase.storage.from_("adorix-ads-media").list()
        # Map filename to its metadata (size/updated_at)
        remote_metadata = {f['name']: f for f in storage_files if f['name'] in active_filenames}
    except Exception as e:
        print(f"❌ Error listing storage bucket: {e}")
        return

    # 3. Process active files
    for filename in active_filenames:
        if filename not in remote_metadata:
            print(f"⚠️ Active ad '{filename}' not found in storage bucket.")
            continue

        remote_info = remote_metadata[filename]
        # Use updated_at or size as a simple version check
        remote_version = str(remote_info.get('updated_at', remote_info.get('metadata', {}).get('size', '')))
        
        # Get description for this ad
        ad_data = next((item for item in response.data if item['video_filename'] == filename), {})
        description = ad_data.get('description', '')

        local_path = os.path.join(LOCAL_ADS_DIR, filename)
        json_path = os.path.join(LOCAL_ADS_DIR, filename.replace(".mp4", ".json"))
        local_version = manifest.get(filename)

        needs_download = not os.path.exists(local_path) or local_version != remote_version

        # 3a. Save/Update Description JSON
        try:
            desc_payload = {"description": description}
            with open(json_path, "w") as f:
                json.dump(desc_payload, f, indent=4)
        except Exception as e:
            print(f"⚠️ Failed to save description for {filename}: {e}")

        if needs_download:
            action = "Downloading missing" if not os.path.exists(local_path) else "Updating"
            print(f"📥 {action} ad: {filename}")
            file_url = f"{STORAGE_BUCKET_URL}/{filename}"
            
            try:
                with httpx.stream("GET", file_url) as r:
                    r.raise_for_status()
                    with open(local_path, "wb") as f:
                        for chunk in r.iter_bytes():
                            f.write(chunk)
                print(f"✅ Successfully synced: {filename}")
                new_manifest[filename] = remote_version
            except Exception as e:
                print(f"❌ Failed to sync {filename}: {e}")
                # Keep old version in manifest if download failed but file still exists
                if os.path.exists(local_path):
                    new_manifest[filename] = local_version
        else:
            # Already up to date
            new_manifest[filename] = local_version

    # 4. Clean up: Delete local files not marked as 'active'
    try:
        local_files = os.listdir(LOCAL_ADS_DIR)
        for local_file in local_files:
            # Don't delete metadata files
            if local_file in ["sync_manifest.json", "mapping.json"] or local_file.endswith(".json"):
                continue
            
            if local_file not in active_filenames:
                file_to_delete = os.path.join(LOCAL_ADS_DIR, local_file)
                if os.path.isfile(file_to_delete):
                    print(f"🗑️ Deleting inactive/obsolete ad: {local_file}")
                    os.remove(file_to_delete)
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

    save_manifest(new_manifest)
    print("🏁 Sync Complete.")

if __name__ == "__main__":
    sync_ads()