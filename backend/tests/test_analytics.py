import os
import sys
import time

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.modules.analytics import report_ad_play
from backend.modules.tracker import AdSessionTracker

def test_tracker_logic():
    print("🧪 Testing AdSessionTracker Logic...")
    tracker = AdSessionTracker()
    
    # Simulate an ad session
    test_ad = "test_video_v1.mp4"
    test_viewer = {"age": "16-29", "gender": "Male"}
    
    tracker.start(test_ad, test_viewer)
    time.sleep(2)  # Simulate 2 seconds of watching
    tracker.set_engaged(True)  # Simulate an interaction
    
    event = tracker.stop()
    
    # Assertions
    assert event['ad_id'] == test_ad, f"Expected {test_ad}, got {event['ad_id']}"
    assert event['viewer_age_group'] == "16-29"
    assert event['viewer_gender'] == "Male"
    assert event['watch_time'] >= 2.0, f"Expected duration >= 2.0, got {event['watch_time']}"
    assert event['engaged'] is True
    
    print("✅ Tracker Logic: OK")
    return event

    # We use report_ad_play which handles UUID resolution from mapping.json
    try:
        from backend.modules.analytics import report_ad_play
        report_ad_play(
            filename=event_data['filename'],
            age=event_data['age'],
            gender=event_data['gender'],
            duration=event_data['duration'],
            engaged=event_data['engaged']
        )
        print("🚀 Reporting triggered in background. Check your Supabase console for a new row in 'analytics_events'.")
    except Exception as e:
        print(f"❌ Reporting failed: {e}")

if __name__ == "__main__":
    try:
        event = test_tracker_logic()
        test_supabase_reporting(event)
        
        # Keep alive briefly for background thread to finish
        print("\nWaiting 3 seconds for background reporting to finish...")
        time.sleep(3)
        print("🏁 Test Finished.")
    except Exception as e:
        print(f"❌ Test Failed: {e}")
