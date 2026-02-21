from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import json
import asyncio
import threading
import time
import os
import sys

# Add the backend and modules directories to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
modules_dir = os.path.join(current_dir, 'modules')
if modules_dir not in sys.path:
    sys.path.append(modules_dir)

# Local modules
from wake_word import WakeWordService
from interaction.interaction_manager import start_interaction_loop
from vision_service import AdorixVision

# --- Global System State ---
class SystemState:
    def __init__(self):
        self.system_id = 1             # 1: Loop, 2: Personalized, 3: Interaction
        self.mode = "IDLE"             # IDLE, INTERACTION
        self.avatar_state = "HIDDEN"
        self.subtitle = ""
        self.ad_url = ""               # Current ad URL
        
        # Thread locks
        self.lock = threading.Lock()

state = SystemState()
connected_clients = []
main_loop = None 
wake_word_service = None
vision_service = None
  
# --- Hardware Services Reset Helpers ---
def restart_wake_word_service():
    """Safely stop and restart the wake word service."""
    global wake_word_service
    
    if wake_word_service:
        try:
            wake_word_service.stop()
        except:
            pass
            
    print(">>> [System] Starting Wake Word Service...")
    wake_word_service = WakeWordService(callback_function=on_wake_word)
    threading.Thread(target=wake_word_service.start, daemon=True).start()

def stop_wake_word_service():
    global wake_word_service
    if wake_word_service:
        print(">>> [System] Stopping Wake Word Service (Microphone released for STT)")
        try:
            wake_word_service.stop()
        except:
            pass
        wake_word_service = None

# --- WebSocket Broadcast ---
async def broadcast_state():
    with state.lock:
        payload = {
            "type": "SYSTEM_UPDATE",
            "system_id": state.system_id,
            "mode": state.mode,
            "avatar_state": state.avatar_state,
            "subtitle": state.subtitle,
            "ad_url": state.ad_url
        }
    
    state_payload = json.dumps(payload)
    if not connected_clients: return
    
    tasks = [client.send_text(state_payload) for client in connected_clients]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

def sync_broadcast():
    global main_loop
    if main_loop:
        try:
            asyncio.run_coroutine_threadsafe(broadcast_state(), main_loop)
        except Exception as e:
            print(f"!!! [Broadcast] Error: {e}")

# --- Callbacks ---
def interaction_state_callback(avatar_state=None, subtitle=None):
    with state.lock:
        if avatar_state: state.avatar_state = avatar_state
        if subtitle is not None: state.subtitle = subtitle
    sync_broadcast()

def on_vision_update(data):
    """
    Central State Machine rules defined here in the Vision Callback.
    Rules: 
      Loop(1) -> Personalized(2) [If face detected]
      Personalized(2) -> Loop(1) [Triggered by frontend AD_LOOP_TIMEOUT after 2 loops]
      Interaction(3) -> Loop(1)  [If face lost - Immediately, aborts Interaction Thread]
    """
    new_id = data.get("system_id")
    ad_url = data.get("ad_url", "")
    
    with state.lock:
        current_id = state.system_id
        
        # 1 -> 2: Transition from Loop to Personalized Ad
        if current_id == 1 and new_id == 2:
            print(f"\n>>> [State Machine] Loop -> Personalized (Ad: {ad_url})")
            state.system_id = 2
            state.ad_url = ad_url
            sync_broadcast()
            
        # 3 -> 1: Transition back to Loop Mode (Face Lost)
        # Note: Personalized(2) ignores Face Lost; it waits for frontend AD_LOOP_TIMEOUT after 2 loops.
        elif new_id == 1 and current_id == 3:
            print("\n>>> [State Machine] User Left Frame. Reverting -> Loop Mode")
            state.system_id = 1
            state.mode = "IDLE"
            state.avatar_state = "SLEEP"
            state.subtitle = ""
            state.ad_url = ""
            sync_broadcast()
            
            # If we were in interaction mode, the mic was locked for STT. 
            # We must restart the wake word scanner so the next person can use it.
            restart_wake_word_service()

def on_wake_word():
    """
    Called when Wake Word is detected.
    Transitions: 2 -> 3 (Personalized -> Interaction)
    """
    with state.lock:
        if state.system_id != 2:
            # According to rules, Wake Word is only valid when in Personalized Mode
            return
            
        print("\n>>> [State Machine] Wake Word Detected! Personalized -> Interaction")
        state.system_id = 3
        state.mode = "INTERACTION"
        state.avatar_state = "WAKE"
        state.subtitle = "Yes? I'm listening..."
        current_ad = state.ad_url
        
    sync_broadcast()
    
    # Instantly stop wake word to free the Microphone for the STT engine
    stop_wake_word_service()
    
    # Spawn the LLM/QA Interaction loop in a separate thread so vision stays non-blocking
    threading.Thread(target=handle_interaction, args=(current_ad,), daemon=True).start()

def handle_interaction(ad_url):
    """
    Runs the full Interaction Loop (STT -> LLM -> TTS).
    Aborts instantly if state.system_id changes away from 3 (User walked away).
    """
    try:
        # Pass the abort checker function to the loop
        is_active = lambda: state.system_id == 3
        
        result = start_interaction_loop(
            current_ad_name=ad_url, 
            state_callback=interaction_state_callback,
            is_active_callback=is_active
        )
        print(f"\n>>> [Interaction Thread] Finished with reason: {result}")
        
    except Exception as e:
        print(f"\n!!! [Interaction Thread] Critical Error: {e}")
        
    finally:
        # Only transition back to LOOP if we are STILL in Interaction mode.
        # If the user already walked away, vision sets it to 1, and we just quietly die.
        with state.lock:
            if state.system_id == 3:
                print("\n>>> [State Machine] Interaction Finished natively. Reverting -> Loop Mode")
                state.system_id = 1
                state.mode = "IDLE"
                state.avatar_state = "SLEEP"
                state.subtitle = ""
                state.ad_url = ""
                sync_broadcast()
                
                # Restart the wake word service for the next cycle
                restart_wake_word_service()

# --- Server Lifecycle Integration ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_loop, vision_service
    # Capture the main asyncio event loop so threads can broadcast safely
    main_loop = asyncio.get_running_loop()
    
    print("\n" + "="*50)
    print("🚀 ADORIX INTEGRATED SYSTEM INITIALIZING")
    print("="*50)
    
    # 1. Start Wake Word listener
    restart_wake_word_service()
    
    # 2. Start Vision camera thread
    vision_service = AdorixVision(broadcast_callback=on_vision_update)
    threading.Thread(target=vision_service.start, daemon=True).start()
    
    yield
    
    # Cleanup on shutdown
    print(">>> [Cleanup] Shutting down Adorix gracefully...")
    stop_wake_word_service()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists("backend/ads"):
    app.mount("/ads", StaticFiles(directory="backend/ads"), name="ads")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        # Send initial state
        with state.lock:
            init_payload = {
                "type": "SYSTEM_UPDATE",
                "system_id": state.system_id,
                "mode": state.mode,
                "avatar_state": state.avatar_state,
                "subtitle": state.subtitle,
                "ad_url": state.ad_url
            }
        await websocket.send_text(json.dumps(init_payload))
        
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                # AD_LOOP_TIMEOUT from frontend
                if msg.get("type") == "AD_LOOP_TIMEOUT":
                    with state.lock:
                        if state.system_id == 2:
                            print("\n>>> [State Machine] Personalized Ad Timeout (Played twice). Reverting -> Loop Mode")
                            state.system_id = 1
                            state.mode = "IDLE"
                            state.avatar_state = "SLEEP"
                            state.subtitle = ""
                            state.ad_url = ""
                    sync_broadcast()
            except Exception as e:
                print(f"!!! [WS] Error parsing message: {e}")
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
    