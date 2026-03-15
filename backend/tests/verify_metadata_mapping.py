import os
import sys
import json
import time

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.modules.storage import sync_ads
from backend.modules.analytics import report_ad_play

def test_mapping_generation():
    print("🧪 Testing Mapping Generation...")
    # Trigger sync to generate mapping.json
    try:
        sync_ads()
        
        mapping_path = os.path.join(project_root, "backend", "ads", "mapping.json")
        if os.path.exists(mapping_path):
            with open(mapping_path, "r") as f:
                mapping = json.load(f)
                print(f"✅ Mapping generated with {len(mapping)} entries.")
                print(f"Sample mapping: {list(mapping.items())[:2]}")
                return mapping
        else:
            print("❌ Mapping file NOT found.")
    except Exception as e:
        print(f"❌ Sync/Mapping failed: {e}")
    return None

def test_mapped_report(mapping):
    if not mapping:
        print("⏭️ Skipping report test due to missing mapping.")
        return

    print("\n🧪 Testing Mapped Reporting...")
    # Take the first filename from mapping
    filename = list(mapping.keys())[0] if mapping else "non_existent.mp4"
    expected_uuid = mapping.get(filename, "dummy-uuid")
    
    print(f"Reporting for filename: {filename} (Expected UUID: {expected_uuid})")
    
    try:
        report_ad_play(filename, "16-29", "Female", 10.0, False)
        print("🚀 Report triggered. Check your 'analytics_events' table for ad_id = " + str(expected_uuid))
    except Exception as e:
        print(f"❌ Report failed: {e}")

if __name__ == "__main__":
    mapping = test_mapping_generation()
    test_mapped_report(mapping)
    
    print("\nWaiting 2 seconds for background thread...")
    time.sleep(2)
    print("🏁 Verification Finished.")
