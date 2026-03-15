import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_system():
    print("🔍 --- ADORIX AD SYNC DIAGNOSTIC TOOL ---")
    
    # 1. Check Environment
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ [ENV] SUPABASE_URL or Keys missing in .env")
        return
    else:
        print(f"✅ [ENV] Supabase URL: {url}")
        print(f"✅ [ENV] Supabase Key: {'SERVICE_ROLE' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'ANON'}")

    # 2. Check Directory Structure
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ads_dir = os.path.join(root_dir, "backend", "ads")
    manifest_path = os.path.join(ads_dir, "sync_manifest.json")
    
    print(f"📁 [DIR] Local Ads Target: {ads_dir}")
    if os.path.exists(ads_dir):
        print(f"✅ [DIR] Ads directory exists.")
        local_files = [f for f in os.listdir(ads_dir) if os.path.isfile(os.path.join(ads_dir, f))]
        print(f"📄 [DIR] Found {len(local_files)} local files.")
    else:
        print(f"⚠️ [DIR] Ads directory does not exist yet (will be created on first sync).")
        local_files = []

    # 3. Database Check
    try:
        supabase: Client = create_client(url, key)
        print("📡 [DB] Connecting to Supabase...")
        
        db_response = supabase.table("ads").select("video_filename, status").execute()
        all_ads = db_response.data
        active_ads = [a['video_filename'] for a in all_ads if a['status'] == 'active']
        
        print(f"✅ [DB] Connected. Found {len(all_ads)} total records.")
        print(f"✅ [DB] Active ads in database: {active_ads}")
        
    except Exception as e:
        print(f"❌ [DB] Connection/Query error: {e}")
        return

    # 4. Storage Bucket Check
    try:
        print("☁️  [STORAGE] Checking 'adorix-ads-media' bucket...")
        storage_files = supabase.storage.from_("adorix-ads-media").list()
        storage_filenames = [f['name'] for f in storage_files]
        print(f"✅ [STORAGE] Files in bucket: {storage_filenames}")
        
        # Check for discrepancies
        missing_in_storage = [a for a in active_ads if a not in storage_filenames]
        if missing_in_storage:
            print(f"⚠️ [STORAGE] ALERT: Active ads missing in storage: {missing_in_storage}")
        else:
            print("✅ [STORAGE] All active DB ads found in storage.")
            
    except Exception as e:
        print(f"❌ [STORAGE] Bucket access error: {e}")

    # 5. Manifest Check
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
            print(f"✅ [MANIFEST] Local manifest tracks {len(manifest)} files.")
        except Exception as e:
            print(f"❌ [MANIFEST] Error reading manifest: {e}")
    else:
        print("ℹ️ [MANIFEST] No manifest found yet.")

    # 6. Conclusion
    print("\n--- DIAGNOSTIC COMPLETE ---")
    if active_ads and not missing_in_storage:
        print("🚀 System is ready. You can run 'python backend/modules/storage.py' to perform the sync.")
    else:
        print("💡 Resolve the warnings above before relying on synchronization.")

if __name__ == "__main__":
    verify_system()
