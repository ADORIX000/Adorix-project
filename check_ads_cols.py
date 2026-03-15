import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

common_ids = ['id', 'uuid', 'ad_id', 'ad_uuid', 'uid', 'pk', 'video_id', 'entry_id', 'row_id']

print("Checking 'ads' table columns...")
for col in common_ids:
    try:
        supabase.table("ads").select(col).limit(1).execute()
        print(f"✅ FOUND: {col}")
    except Exception as e:
        msg = str(e)
        if "does not exist" not in msg:
            print(f"❓ Unexpected error for {col}: {msg}")

print("\nChecking if we can query any record to see keys...")
try:
    res = supabase.table("ads").select("*").limit(1).execute()
    if res.data:
        print(f"Columns in first row: {list(res.data[0].keys())}")
    else:
        print("Table is still empty.")
except Exception as e:
    print(f"Failed select *: {e}")
