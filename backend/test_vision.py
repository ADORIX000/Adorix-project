
import cv2
import time
import sys
import threading
from vision_service import AdorixVision

# Mock callback to print broadcast messages
def mock_broadcast(data):
    print(f"\n[BROADCAST] Data received: {data}")

def run_test():
    print("--------------------------------------------------")
    print("      Testing Adorix Vision Service Logic         ")
    print("--------------------------------------------------")
    print("[INFO] Initializing Vision Service...")
    print("[INFO] This will open your webcam.")
    print("[INFO] Press 'q' in the terminal to stop (or Ctrl+C).")
    
    # Initialize Service
    try:
        service = AdorixVision(mock_broadcast)
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
