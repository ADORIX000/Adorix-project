import os
import cv2
import time
import sys
import threading

# --- Path Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
modules_dir = os.path.join(current_dir, 'modules')
if modules_dir not in sys.path:
    sys.path.append(modules_dir)

from vision_service import AdorixVision
from modules.ad_engine.selector import AdSelector

# Mock callback to print broadcast messages
def mock_broadcast(data):
    sid = data.get("system_id")
    if sid == 1:
        # Loop Mode - optionally silent or just a dot
        sys.stdout.write(".")
        sys.stdout.flush()
    elif sid == 2:
        demo_list = data.get("demographics", [])
        ad = data.get("ad_url", "N/A")
        is_multi = data.get("all_people", False)
        
        print("\n" + "="*50)
        print(f" ANALYSIS RESULT ({'MULTI' if is_multi else 'SINGLE'})")
        print(f" All Detected: {demo_list}")
        print(f" Currently Playing Ad: {ad}")
        print("="*50 + "\n")

def run_test():
    print("--------------------------------------------------")
    print("      Testing Adorix Vision Service Logic         ")
    print("--------------------------------------------------")
    print("[INFO] Initializing Vision Service...")
    print("[INFO] This will open your webcam.")
    print("[INFO] Press 'q' in the terminal to stop (or Ctrl+C).")
    
    # Initialize Service
    try:
        # Dummy paths for testing
        current_dir = os.path.dirname(os.path.abspath(__file__))
        rules_path = os.path.join(current_dir, "modules", "ad_engine", "rules.json")
        ads_dir = os.path.join(current_dir, "ads")
        selector = AdSelector(rules_path, ads_dir)
        
        service = AdorixVision(mock_broadcast, selector=selector)
    except Exception as e:
        print(f"[ERROR] Failed to initialize AdorixVision: {e}")
        return

    # Run in a separate thread so we can keep the main thread for control/input if needed
    # But AdorixVision.start() is blocking (loops forever), so we just call it.
    
    print("[INFO] Starting service... Look at the camera!")
    try:
        service.start()
    except KeyboardInterrupt:
        print("\n[INFO] Test stopped by user.")
    except Exception as e:
        print(f"\n[ERROR] Runtime error: {e}")

if __name__ == "__main__":
    run_test()
