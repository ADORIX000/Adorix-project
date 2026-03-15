import os
import threading
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
URL = os.getenv("SUPABASE_URL")
# Using SERVICE_ROLE_KEY for administrative access to bypass RLS
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not URL or not KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) must be set in .env")

supabase: Client = create_client(URL, KEY)

def report_ad_event(ad_id, viewer_age_group, viewer_gender, watch_time, engaged):
    """
    Inserts a new analytic event into the Supabase database.
    This is intended to be called in a background thread to prevent UI blocking.
    """
    def _report():
        try:
            payload = {
                "ad_id": ad_id,
                "viewer_age_group": viewer_age_group,
                "viewer_gender": viewer_gender,
                "watch_time_seconds": float(watch_time),
                "engaged": bool(engaged)
            }
            print(f"📊 [Analytics] Reporting event: {payload}")
            supabase.table("analytics_events").insert(payload).execute()
            print(f"✅ [Analytics] Event reported successfully.")
        except Exception as e:
            print(f"❌ [Analytics] Error reporting event: {e}")

    # Run in a background thread to avoid blocking the main kiosk loop
    threading.Thread(target=_report, daemon=True).start()

if __name__ == "__main__":
    # Internal test
    report_ad_event("test_ad_123", "30-39", "Male", 15.5, True)
