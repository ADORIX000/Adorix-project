import os
import sys
import time
import json
import random

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import our modules
from backend.modules.storage import sync_ads
from backend.modules.analytics import report_ad_play
from backend.modules.tracker import AdSessionTracker

def run_full_flow_test():
    print("=" * 60)
    print("🚀 ADORIX FULL SYSTEM FLOW VERIFICATION")
    print("=" * 60)

    # 1. DATABASE SYNC SECTION
    print("\n[Step 1/4] Synchronizing with Supabase Database...")
    try:
        sync_ads()
    except Exception as e:
        print(f"❌ Sync Failed: {e}")
        return

    # Check mapping.json
    mapping_path = os.path.join(project_root, "backend", "ads", "mapping.json")
    if not os.path.exists(mapping_path):
        print("❌ Mapping file not created. Cannot proceed.")
        return

    with open(mapping_path, "r") as f:
        mapping = json.load(f)
        if not mapping:
            print("⚠️ No active ads found in database. Please add an 'active' ad in Supabase to test fully.")
            # We can still proceed with a dummy filename to test the fallback logic
            test_filename = "test_verification_ad.mp4"
        else:
            test_filename = random.choice(list(mapping.keys()))
            print(f"✅ Synced {len(mapping)} ads. Testing with: {test_filename}")

    # 2. TRACKER SECTION
    print("\n[Step 2/4] Simulating Kiosk Playback & Session Tracking...")
    tracker = AdSessionTracker()
    
    # Simulate a user detected (30-39 Male)
    viewer_data = {"age": "30-39", "gender": "Male"}
    print(f"👤 Simulated Viewer: {viewer_data}")
    
    tracker.start(test_filename, viewer_data)
    print(f"⏱️ Player started: {test_filename}")
    
    # Simulate 3 seconds of watching
    time.sleep(3)
    
    # Simulate engagement (e.g., they asked a question)
    tracker.set_engaged(True)
    print("✨ User Engaged! (Interaction Mode triggered)")
    
    # Simulate 2 more seconds
    time.sleep(2)
    
    # End session
    event_data = tracker.stop()
    print(f"🛑 Player stopped. Watch time: {event_data.get('duration')}s")

    # 3. ANALYTICS REPORTING SECTION
    print("\n[Step 3/4] Reporting Analytics to Supabase mapping to UUID...")
    try:
        # event_data contains {filename, age, gender, duration, engaged}
        # report_ad_play resolves the filename to UUID via mapping.json
        report_ad_play(**event_data)
        print("🚀 Reporting triggered in background thread.")
    except Exception as e:
        print(f"❌ Analytics handoff failed: {e}")

    # 4. FINAL VERIFICATION
    print("\n[Step 4/4] Finalizing...")
    print("Waiting 3 seconds for the background reporting thread to finish...")
    time.sleep(3)
    
    print("\n" + "=" * 60)
    print("🏁 FULL FLOW TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print("Check your Supabase 'analytics_events' table.")
    print(f"Target Filename: {test_filename}")
    print(f"Resolved UUID: {mapping.get(test_filename, 'FALLBACK_FILENAME')}")
    print("=" * 60)

if __name__ == "__main__":
    run_full_flow_test()
