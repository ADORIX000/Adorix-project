#!/usr/bin/env python
"""
ADORIX - Integrated Kiosk System (v2.2)
Strict 3-Stage Workflow: Loop -> Personalized -> Interaction.
"""

import os
import time
import json
import cv2
import threading
import asyncio
import numpy as np
from typing import Set

# --- Services ---
from services.vision.detector import AgeGenderDetector
from services.ad_engine.selector import AdSelector
from services.avatar_interaction.wakeword import WakeWordService
from services.avatar_interaction.stt import listen_one_phrase
from services.avatar_interaction.tts import speak
from services.avatar_interaction.brain import adorix_brain

# ============ CONFIG ============
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(PROJECT_ROOT, "services", "ad_engine", "rules.json")
ADS_DIR = os.path.join(PROJECT_ROOT, "services", "ad_engine", "ads")
DATA_DIR = os.path.join(PROJECT_ROOT, "services", "ad_engine", "data")

# ============ GLOBAL STATE ============
class KioskState:
    def __init__(self):
        self.current_users = {}
        self.current_ad = None
        self.mode = "LOOP"  # LOOP, PERSONALIZED, INTERACTION
        self.avatar_status = "SLEEP"
        self.product_data = {}

kiosk = KioskState()
ws_clients: Set = set()
loop = None

# ============ UTILS ============
async def broadcast(message: dict):
    if not ws_clients: return
    json_msg = json.dumps(message)
    to_remove = []
    for ws in ws_clients:
        try:
            await ws.send_text(json_msg)
        except Exception:
            to_remove.append(ws)
    for ws in to_remove:
        ws_clients.discard(ws)

def sync_broadcast(message: dict):
    global loop
    if loop and ws_clients:
        asyncio.run_coroutine_threadsafe(broadcast(message), loop)

def update_avatar(status, subtitle=""):
    kiosk.avatar_status = status
    sync_broadcast({
        "action": "AVATAR_STATUS",
        "status": status,
        "subtitle": subtitle
    })

# ============ INTERACTION LOGIC ============
wake_word_service = None

def on_wake_word():
    if kiosk.mode == "INTERACTION": return
    print(">>> [Interaction] Wake Word Detected!")
    threading.Thread(target=run_interaction_flow, daemon=True).start()

def run_interaction_flow():
    global wake_word_service
    kiosk.mode = "INTERACTION"
    if wake_word_service: wake_word_service.pause()

    try:
        # 1. Greeting
        greeting = "Hello! Do you have a question about this product?"
        update_avatar("SPEAKING", greeting)
        speak(greeting)

        while True: # Interaction Loop
            update_avatar("LISTENING", "Listening...")
            user_text = listen_one_phrase(timeout=7)

            if user_text:
                print(f">>> User said: {user_text}")
                update_avatar("THINKING", f"You: {user_text}")
                
                # Context from the specific ad JSON
                context = json.dumps(kiosk.product_data)
                answer = adorix_brain.generate_answer(user_text, context)
                
                update_avatar("SPEAKING", answer)
                speak(answer)
                
                # Ask if there's anything else
                # (Optional: user can just say something again without prompt)
            else:
                break # No input for 7s -> Exit interaction

    except Exception as e:
        print(f"!!! Interaction Error: {e}")

    finally:
        kiosk.mode = "PERSONALIZED"
        update_avatar("SLEEP", "")
        if wake_word_service: wake_word_service.resume()

# ============ WEBSOCKET SERVER ============
async def websocket_server():
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        ws_clients.add(websocket)
        print("✅ Frontend Connected")
        try:
            await websocket.send_json({"action": "MODE_SWITCH", "mode": kiosk.mode, "ad": kiosk.current_ad})
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            ws_clients.discard(websocket)
            print("❌ Frontend Disconnected")

    import uvicorn
    server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="critical"))
    await server.serve()

def start_websocket_thread():
    def run():
        global loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(websocket_server())
    threading.Thread(target=run, daemon=True).start()
    print("🚀 WebSocket Server Started (Port 8000)")
    time.sleep(1)

# ============ VIDEO PLAYER ============
class VideoPlayer:
    def __init__(self, window_name):
        self.window_name = window_name
        self.cap = None
        self.current_file = None
        self.lock = threading.Lock()
    
    def play(self, filename):
        with self.lock:
            if self.current_file == filename and self.cap and self.cap.isOpened(): return
            if self.cap: self.cap.release()
            
            path = os.path.join(ADS_DIR, filename)
            if os.path.exists(path):
                self.cap = cv2.VideoCapture(path)
                self.current_file = filename
                print(f"▶️  Playing: {filename}")
                # Load context
                data_path = os.path.join(DATA_DIR, filename.replace(".mp4", ".json"))
                if os.path.exists(data_path):
                    with open(data_path, "r") as f:
                        kiosk.product_data = json.load(f)
                else: kiosk.product_data = {}
            else: print(f"⚠️  Video not found: {filename}")

    def update(self):
        with self.lock:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret: return frame
                else: self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        return None

    def stop(self):
        with self.lock:
            if self.cap: self.cap.release()

# ============ MAIN LOOP ============
def main_loop():
    print("📹 Initializing Vision system...")
    detector = AgeGenderDetector().start()
    selector = AdSelector(RULES_PATH, ADS_DIR)
    
    global wake_word_service
    wake_word_service = WakeWordService(callback_function=on_wake_word)
    threading.Thread(target=wake_word_service.start, daemon=True).start()

    WIN_NAME = "ADORIX KIOSK"
    cv2.namedWindow(WIN_NAME, cv2.WINDOW_NORMAL)
    player = VideoPlayer(WIN_NAME)
    
    last_user_ts = 0
    kiosk.mode = "LOOP"

    print("✅ System Ready (3-Stage Workflow)")

    try:
        while True:
            frame = detector.update()
            if frame is None: time.sleep(0.01); continue

            now_ts = time.time()
            users = detector.get_committed_people(now_ts)
            
            # --- State Machine ---
            if kiosk.mode == "LOOP":
                if users:
                    print(">>> [State] LOOP -> PERSONALIZED")
                    kiosk.mode = "PERSONALIZED"
                    last_user_ts = now_ts
                    ad = selector.choose_ad_filename({"primary": users[0], "status": "ACTIVE"})
                    kiosk.current_ad = ad
                    player.play(ad)
                    sync_broadcast({"action": "MODE_SWITCH", "mode": "PERSONALIZED", "ad": ad})
                    wake_word_service.resume()
                else:
                    if not kiosk.current_ad:
                        kiosk.current_ad = selector.choose_ad_filename({"status": "IDLE"})
                        player.play(kiosk.current_ad)
            
            elif kiosk.mode == "PERSONALIZED":
                if not users:
                    if now_ts - last_user_ts > 5.0:
                        print(">>> [State] PERSONALIZED -> LOOP")
                        kiosk.mode = "LOOP"
                        kiosk.current_ad = None
                        wake_word_service.pause()
                        sync_broadcast({"action": "MODE_SWITCH", "mode": "LOOP"})
                else:
                    last_user_ts = now_ts

            # --- Render ---
            display_frame = None
            if kiosk.mode == "INTERACTION":
                display_frame = frame.copy()
                cv2.putText(display_frame, "INTERACTION MODE", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                video_frame = player.update()
                display_frame = video_frame if video_frame is not None else frame
                if users:
                    cv2.putText(display_frame, f"Detected: {len(users)}", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            cv2.imshow(WIN_NAME, display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break
            time.sleep(0.01)

    except KeyboardInterrupt: pass
    finally:
        detector.stop()
        player.stop()
        if wake_word_service: wake_word_service.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    start_websocket_thread()
    main_loop()
