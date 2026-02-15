#!/usr/bin/env python
"""
ADORIX - Integrated Kiosk System
Combines vision detection + ad selection + frontend communication
"""

import os
import time
import json
import cv2
import asyncio
import threading
import numpy as np
from collections import Counter

from services.vision.detector import AgeGenderDetector
from services.ad_engine.selector import AdSelector

# ============ CONFIG ============
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SHARED_JSON = os.path.join(PROJECT_ROOT, "shared", "current_users.json")
RULES_PATH = os.path.join(PROJECT_ROOT, "services", "ad_engine", "rules.json")
ADS_DIR = os.path.join(PROJECT_ROOT, "services", "ad_engine", "ads")

# ============ SHARED STATE ============
class KioskState:
    def __init__(self):
        self.current_users = {}
        self.current_ad = None
        self.detector = None
        self.selector = None
        self.server_ready = False

kiosk = KioskState()

# ============ WEBSOCKET SERVER ============
def start_websocket_server():
    """Start WebSocket server for frontend communication"""
    try:
        from fastapi import FastAPI, WebSocket
        from fastapi.middleware.cors import CORSMiddleware
        import uvicorn
        
        app = FastAPI()
        
        # CORS for frontend
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        clients = set()
        
        @app.get("/")
        def health():
            return {"status": "ADORIX Kiosk Running"}
        
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            clients.add(websocket)
            print("✅ Frontend connected to WebSocket")
            
            try:
                while True:
                    # Read from frontend
                    data = await websocket.receive_text()
                    
                    # Send current ad to frontend
                    if kiosk.current_ad:
                        response = {
                            "action": "play_ad",
                            "ad": kiosk.current_ad,
                            "users": kiosk.current_users
                        }
                        await websocket.send_json(response)
                    
                    await asyncio.sleep(0.5)
            except Exception as e:
                print(f"❌ WebSocket error: {e}")
            finally:
                clients.discard(websocket)
        
        # Broadcast function
        async def broadcast_ad(ad_name):
            for client in clients:
                try:
                    await client.send_json({"action": "play_ad", "ad": ad_name})
                except:
                    pass
        
        print("🚀 Starting WebSocket server on 0.0.0.0:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="critical")
    
    except Exception as e:
        print(f"❌ WebSocket server error: {e}")

# ============ VISION & AD LOOP ============
def vision_ad_loop():
    """Main loop: detect users, select ads, show in CV2 window"""
    try:
        print("📹 Starting vision detector...")
        kiosk.detector = AgeGenderDetector().start(index=0, width=640, height=480)
        kiosk.selector = AdSelector(RULES_PATH, ADS_DIR)
        
        print("✅ Vision detector started")
        cv2.namedWindow("ADORIX KIOSK", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("ADORIX KIOSK", 800, 600)
        
        current_video = None
        video_cap = None
        
        while True:
            # Step 1: Update detection
            frame = kiosk.detector.update()
            if frame is None:
                time.sleep(0.01)
                continue
            
            # Step 2: Get current users
            now_ts = time.time()
            users = kiosk.detector.get_committed_people(now_ts)
            kiosk.current_users = {
                "count": len(users),
                "primary": users[0] if users else None,
                "all": users
            }
            
            # Step 3: Select ad based on users
            payload = {
                "status": "ACTIVE" if users else "IDLE",
                "presence": len(kiosk.detector.tracks) > 0,
                "primary": users[0] if users else None,
                "people": users
            }
            
            selected_ad = kiosk.selector.choose_ad_filename(payload)
            kiosk.current_ad = selected_ad
            
            # Step 4: Show either camera (detecting) or ad (idle/active)
            if users:  # ACTIVE: Show camera with detection
                frame_display = frame.copy()
                h, w = frame_display.shape[:2]
                
                # Draw detected users
                for user in users:
                    # Draw a green box (simplified - ideally track bbox)
                    y = 50
                    text = f"Detected: {user.get('gender', '?')} - Age {user.get('age', '?')}"
                    cv2.putText(frame_display, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                cv2.imshow("ADORIX KIOSK", frame_display)
                if video_cap:
                    video_cap.release()
                    video_cap = None
            
            else:  # IDLE: Show ad video
                if selected_ad and selected_ad != current_video:
                    if video_cap:
                        video_cap.release()
                    
                    ad_path = os.path.join(ADS_DIR, selected_ad)
                    if os.path.exists(ad_path):
                        video_cap = cv2.VideoCapture(ad_path)
                        current_video = selected_ad
                        print(f"▶️  Playing ad: {selected_ad}")
                
                if video_cap and video_cap.isOpened():
                    ret, ad_frame = video_cap.read()
                    if ret:
                        cv2.imshow("ADORIX KIOSK", ad_frame)
                    else:
                        # Video ended, loop it
                        video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                else:
                    # No ad or file not found - show camera
                    cv2.imshow("ADORIX KIOSK", frame)
            
            # Exit on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("👋 Exiting...")
                break
            
            time.sleep(0.01)
    
    except Exception as e:
        print(f"❌ Vision loop error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if video_cap:
            video_cap.release()
        if kiosk.detector:
            kiosk.detector.stop()
        cv2.destroyAllWindows()

# ============ MAIN ============
def main():
    print("\n" + "="*60)
    print("🎬 ADORIX KIOSK - Starting")
    print("="*60 + "\n")
    
    # Start WebSocket server in background thread
    import threading
    ws_thread = threading.Thread(target=start_websocket_server, daemon=True)
    ws_thread.start()
    
    # Give server time to start
    time.sleep(2)
    
    print("\n📹 Starting vision and ad playback loop...")
    vision_ad_loop()
    
    print("\n" + "="*60)
    print("✓ ADORIX KIOSK - Stopped")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
