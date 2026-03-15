import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Load environment variables
load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not URL or not KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    sys.exit(1)

supabase: Client = create_client(URL, KEY)

def populate_ads():
    print("=" * 60)
    print("📂 ADORIX - POPULATING ADS TABLE FROM STORAGE BUCKET")
    print("=" * 60)

    # 1. Fetch files from Supabase Storage
    try:
        print("🔍 Listing files in 'adorix-ads-media' bucket...")
        storage_files = supabase.storage.from_("adorix-ads-media").list()
        # Filter for .mp4 files
        bucket_filenames = {f['name'] for f in storage_files if f['name'].endswith('.mp4')}
        print(f"📋 Found {len(bucket_filenames)} video(s) in storage.")
    except Exception as e:
        print(f"❌ Error listing storage: {e}")
        return

    # 2. Fetch existing ads from Database
    try:
        print("🔍 Fetching existing ads from 'ads' table...")
        response = supabase.table("ads").select("video_filename").execute()
        db_filenames = {item['video_filename'] for item in response.data if item.get('video_filename')}
        print(f"📋 Found {len(db_filenames)} entry(s) already in database.")
    except Exception as e:
        print(f"❌ Error fetching database: {e}")
        return

    # 3. Identify missing files
    missing_files = bucket_filenames - db_filenames
    
    if not missing_files:
        print("\n✅ Database is already up to date with storage. No changes needed.")
        return

    print(f"\n✨ Found {len(missing_files)} new ad(s) to add to database.")
    
    # 4. Insert missing files
    for filename in missing_files:
        try:
            print(f"➕ Adding: {filename}")
            payload = {
                "video_filename": filename,
                "status": "active"
            }
            supabase.table("ads").insert(payload).execute()
        except Exception as e:
            print(f"❌ Failed to add {filename}: {e}")

    print("\n" + "=" * 60)
    print("🏁 INVENTORY SYNC COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    populate_ads()
