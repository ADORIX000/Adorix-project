#!/usr/bin/env python
"""
User Detection Runner
Starts the camera and runs face/age/gender detection
Exports detected users to shared/current_users.json
"""

import sys
import time
import signal
import traceback
from modules.detection import AgeGenderDetector

detector = None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n⏹️  Stopping detection...")
    if detector:
        detector.stop()
    print("✓ Detection stopped")
    print("="*60 + "\n")
    sys.exit(0)

def main():
    global detector
    
    print("\n" + "="*60)
    print("🎬 User Detection System - Starting...")
    print("="*60)
    
    detector = AgeGenderDetector()
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start camera (index=0 is default webcam)
        print("\n📹 Initializing camera...")
        detector.start(index=0, width=640, height=480)
        print("✓ Camera started successfully")
        
        print("\n🔍 Running user detection...")
        print("Press Ctrl+C to stop\n")
        
        frame_count = 0
        start_time = time.time()
        
        while True:
            # Process one frame
            frame = detector.update()
            
            if frame is not None:
                frame_count += 1
                
                # Print status every 30 frames (~1 sec at 30fps)
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    
                    # Get current detected people
                    now_ts = time.time()
                    people = detector.get_committed_people(now_ts)
                    
                    print(f"[Frame {frame_count}] FPS: {fps:.1f} | Tracked: {len(detector.tracks)} | Detected: {len(people)}")
                    
                    if people:
                        for person in people:
                            print(f"  → Person ID {person['id']}: {person['gender']} (age {person['age']})")
            
            time.sleep(0.01)  # 10ms to prevent CPU spinning
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        traceback.print_exc()
    
    finally:
        if detector:
            detector.stop()
        print("✓ Detection stopped")
        print("="*60 + "\n")

if __name__ == "__main__":
    main()
