#!/usr/bin/env python
"""
ADORIX - Integrated Kiosk System
Simplified version with proper threading
"""

import os
import time
import json
import cv2
import threading
import numpy as np
from collections import Counter
from typing import Set
import asyncio
from concurrent.futures import ThreadPoolExecutor

from services.vision.detector import AgeGenderDetector
from services.ad_engine.selector import AdSelector

# ============ CONFIG ============
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SHARED_JSON = os.path.join(PROJECT_ROOT, "shared", "current_users.json")
RULES_PATH = os.path.join(PROJECT_ROOT, "services", "ad_engine", "rules.json")
ADS_DIR = os.path.join(PROJECT_ROOT, "services", "ad_engine", "ads")

# ============ GLOBAL STATE ============
class KioskState:
    def __init__(self):
        self.current_users = {}
        self.current_ad = None
        self.detector = None
        self.selector = None

kiosk = KioskState()
ws_clients: Set = set()

# ============ WEBSOCKET - Proper Async Version ============
async def websocket_server():
    """Async WebSocket server using built-in asyncio"""
    from fastapi import FastAPI, WebSocket
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    def health():
        return {"status": "ADORIX running", "version": "1.0"}
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        ws_clients.add(websocket)
        print("✅ Frontend connection received")
        
        try:
            while True:
                # Send state updates every 100ms
                if kiosk.current_ad or kiosk.current_users:
                    msg = {
                        "action": "update",
                        "ad": kiosk.current_ad,
                        "users": kiosk.current_users
                    }
                    await websocket.send_json(msg)
                
                await asyncio.sleep(0.1)
        except Exception as e:
            pass
        finally:
            ws_clients.discard(websocket)
    
    # Run with uvicorn
    import uvicorn
    server = uvicorn.Server(uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="critical",
        access_log=False
    ))
    await server.serve()

# ============ RUN WEBSOCKET IN THREAD ============
def run_websocket_in_thread():
    """Start WebSocket server in a thread"""
    def run_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(websocket_server())
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    print("🚀 WebSocket server started (port 8000)")
    time.sleep(1)

# ============ VISION & AD LOOP ============
def vision_ad_loop():
    """Main loop - detect users and show ads"""
    print("📹 Initializing vision system...")
    
    try:
        # Start detector
        kiosk.detector = AgeGenderDetector().start(index=0, width=640, height=480)
        kiosk.selector = AdSelector(RULES_PATH, ADS_DIR)
        
        print("✅ Vision system ready")
        print("📺 Opening display window...")
        
        # OpenCV window
        WIN_NAME = "ADORIX KIOSK"
        cv2.namedWindow(WIN_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WIN_NAME, 1024, 768)
        
        # Ad playback
        current_video_file = None
        video_cap = None
        
        print("\n🎬 Starting main loop (Press Q to quit)\n")
        
        while True:
            # GET FRAME
            frame = kiosk.detector.update()
            if frame is None:
                time.sleep(0.01)
                continue
            
            # DETECT USERS
            now_ts = time.time()
            users = kiosk.detector.get_committed_people(now_ts)
            kiosk.current_users = {
                "count": len(users),
                "data": users
            }
            
            # SELECT AD
            payload = {
                "status": "ACTIVE" if users else "IDLE",
                "presence": len(kiosk.detector.tracks) > 0,
                "primary": users[0] if users else None,
                "people": users
            }
            
            selected_ad = kiosk.selector.choose_ad_filename(payload)
            kiosk.current_ad = selected_ad
            
            # DISPLAY LOGIC
            display_frame = None
            
            if users:  # DETECTING - Show camera
                display_frame = frame.copy()
                h, w = display_frame.shape[:2]
                
                # Draw user info
                text = f"Detected {len(users)} user(s)"
                cv2.putText(display_frame, text, (20, 40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
                
                for i, user in enumerate(users):
                    y = 80 + (i * 40)
                    info = f"{user['gender']} - Age {user['age']}"
                    cv2.putText(display_frame, info, (20, y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                # Close video
                if video_cap:
                    video_cap.release()
                    video_cap = None
                    current_video_file = None
            
            else:  # IDLE - Play ad video
                if selected_ad != current_video_file:
                    if video_cap:
                        video_cap.release()
                    
                    ad_path = os.path.join(ADS_DIR, selected_ad)
                    if os.path.exists(ad_path):
                        video_cap = cv2.VideoCapture(ad_path)
                        current_video_file = selected_ad
                        print(f"▶️  Playing: {selected_ad}")
                    else:
                        print(f"⚠️  Ad not found: {ad_path}")
                
                if video_cap and video_cap.isOpened():
                    ret, ad_frame = video_cap.read()
                    if ret:
                        display_frame = ad_frame
                    else:
                        # Loop video
                        video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, ad_frame = video_cap.read()
                        if ret:
                            display_frame = ad_frame
                        else:
                            display_frame = frame
                else:
                    display_frame = frame
            
            # SHOW WINDOW
            if display_frame is not None:
                cv2.imshow(WIN_NAME, display_frame)
            
            # CHECK FOR EXIT
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                print("\n👋 User quit")
                break
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error in vision loop: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n🛑 Cleaning up...")
        if video_cap:
            video_cap.release()
        if kiosk.detector:
            kiosk.detector.stop()
        cv2.destroyAllWindows()
        print("✅ Cleanup complete")

# ============ MAIN ============
def main():
    print("\n" + "="*70)
    print("  " + "🎬 ADORIX KIOSK SYSTEM".center(66) + "  ")
    print("="*70)
    print()
    print("  Starting components:")
    print("    1. Vision detector (camera + face detection)")
    print("    2. WebSocket server (port 8000)")
    print("    3. Ad display loop")
    print()
    
    # Start WebSocket
    try:
        run_websocket_in_thread()
    except Exception as e:
        print(f"⚠️  WebSocket startup issue: {e}")
    
    # Run vision loop (blocking)
    vision_ad_loop()
    
    print("\n" + "="*70)
    print("  " + "ADORIX KIOSK - STOPPED".center(66) + "  ")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
