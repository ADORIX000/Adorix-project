import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not URL or not KEY:
    print("Missing credentials")
    exit(1)

supabase: Client = create_client(URL, KEY)

def inspect_table(name):
    print(f"\n--- Inspecting table: {name} ---")
    try:
        # Try to get one row to see column names
        res = supabase.table(name).select("*").limit(1).execute()
        if res.data and len(res.data) > 0:
            print(f"Columns found via data: {list(res.data[0].keys())}")
        else:
            print("Table is empty. Testing common column names...")
            for col in ['id', 'uuid', 'ad_id', 'video_id', 'video_filename', 'status', 'created_at']:
                try:
                    supabase.table(name).select(col).limit(1).execute()
                    print(f"✅ Column exists: {col}")
                except Exception as e:
                    # Parse error message to see if it's "column does not exist"
                    err_msg = str(e)
                    if "does not exist" not in err_msg:
                        # If it's another error (like table not found), reporting it
                        print(f"❓ Error checking {col}: {err_msg[:50]}...")
    except Exception as e:
        print(f"❌ Table inspection failed: {e}")

if __name__ == "__main__":
    inspect_table("ads")
    inspect_table("analytics_events")
