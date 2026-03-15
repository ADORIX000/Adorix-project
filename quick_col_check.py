import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
s = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

try:
    # Just try to fetch everything and see what we get
    res = s.table("ads").select("*").limit(0).execute()
    # On some versions, selecting limit 0 or 1 on empty table still gives headers if we use postgrest directly
    # But with the SDK it might just be []
    
    # Try selecting 'id' explicitly
    try:
        s.table("ads").select("id").limit(1).execute()
        print("COL_ID: EXISTS")
    except Exception as e:
        print(f"COL_ID: MISSING ({e})")
        
    try:
        s.table("ads").select("uuid").limit(1).execute()
        print("COL_UUID: EXISTS")
    except Exception as e:
        print(f"COL_UUID: MISSING ({e})")

except Exception as e:
    print(f"GENERAL_ERROR: {e}")
