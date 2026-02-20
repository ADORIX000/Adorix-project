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
from interaction.tts_engine import speak
from vision_service import AdorixVision

# --- Global System State ---
system_state = {
    "system_id": 1,  # 1: Loop, 2: Personalized, 3: Interaction
    "mode": "IDLE",  # IDLE, INTERACTION
    "avatar_state": "SLEEP",
    "subtitle": "",
    "current_ad_json": "16-29_female.json", # Default to an existing JSON
    "product_data": {
        "product": "H&M Trend Capsule Outfit Set",
        "context": "A modern capsule collection that helps you style multiple trendy looks with a few essential pieces."
    }
}

connected_clients = []
wake_word_service = None
vision_service = None
main_loop = None # Added to capture the event loop from the main thread

async def broadcast_state():
    # Add a type field for the frontend to recognize the update
    payload = system_state.copy()
    payload["type"] = "SYSTEM_UPDATE"
    state_payload = json.dumps(payload)

    if not connected_clients:
        return
    
    # Create a list of tasks for broadcasting
    tasks = [client.send_text(state_payload) for client in connected_clients]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

def sync_broadcast():
    """Helper to broadcast state from synchronous code/threads"""
    global main_loop
    if main_loop:
        try:
            # Safely schedule the coroutine in the main loop
            asyncio.run_coroutine_threadsafe(broadcast_state(), main_loop)
        except Exception as e:
            print(f"!!! [Broadcast] Error: {e}")
    else:
        print("!!! [Broadcast] Main event loop not captured yet.")

def interaction_state_callback(avatar_state=None, subtitle=None):
    global system_state
    if avatar_state:
        system_state["avatar_state"] = avatar_state
    if subtitle is not None:
        system_state["subtitle"] = subtitle
    
    print(f">>> [System] State Update: {avatar_state} | {subtitle}")
    sync_broadcast()

def on_vision_update(data):
    """Callback for AdorixVision detections."""
    global system_state
    
    new_id = data.get("system_id")
    
    # ONLY allow switching to Personalized Mode (2) if we are in Loop Mode (1)
    if new_id == 2 and system_state["system_id"] == 1:
        print(f">>> [Vision] Triggering Personalized Mode: {data.get('ad_url')}")
        system_state["system_id"] = 2
        system_state["ad_url"] = data.get("ad_url")
        sync_broadcast()
    
    # If vision loses person (1) and we are in Personalized Mode (2), 
    # we DON'T revert immediately. We let the ad finish its loops.
    # Exception: if we are in Loop Mode (1) and vision is 1, keep it 1.
    elif new_id == 1 and system_state["system_id"] == 1:
        # Already in 1, no need to broadcast frequently if nothing changed
        pass

def on_wake_word():
    global system_state
    if system_state["mode"] == "IDLE":
        print(">>> [WAKE] Switching to INTERACTION mode")
        system_state["mode"] = "INTERACTION"
        system_state["system_id"] = 3
        system_state["avatar_state"] = "WAKE"
        system_state["subtitle"] = "Yes? I'm listening..."
        
        sync_broadcast()
        
        # Start the interaction loop in a SEPARATE thread to not block the wake word service
        threading.Thread(target=handle_interaction, daemon=True).start()

def handle_interaction():
    global system_state
    try:
        # This runs the interaction loop (STT -> LLM -> TTS)
        result = start_interaction_loop(
            system_state["current_ad_json"], 
            state_callback=interaction_state_callback
        )
        print(f">>> [Interaction] Loop ended with: {result}")
    except Exception as e:
        print(f"!!! [Interaction] Critical error in loop: {e}")
    finally:
        system_state["mode"] = "IDLE"
        system_state["system_id"] = 1
        system_state["avatar_state"] = "SLEEP"
        system_state["subtitle"] = ""
        sync_broadcast()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global wake_word_service, main_loop
    # Capture the main event loop
    main_loop = asyncio.get_running_loop()
    
    # Initialize wake word
    wake_word_service = WakeWordService(callback_function=on_wake_word)
    threading.Thread(target=wake_word_service.start, daemon=True).start()
    
    # Initialize vision service
    vision_service = AdorixVision(broadcast_callback=on_vision_update)
    threading.Thread(target=vision_service.start, daemon=True).start()
    
    print(">>> [System] Adorix Assistant Ready (Vision & Wake Word Active)")
    yield
    # Cleanup
    if wake_word_service:
        try:
            wake_word_service.stop()
        except Exception as e:
            print(f">>> [Cleanup] Wake Word stop error: {e}")

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
        await websocket.send_text(json.dumps(system_state))
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "AD_LOOP_TIMEOUT":
                    print(">>> [System] Ad Loop Timeout: Reverting to Loop Mode")
                    system_state["system_id"] = 1
                    await broadcast_state()
            except Exception as e:
                print(f"!!! [WS] Error parsing message: {e}")
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
    