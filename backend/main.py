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

# --- Global System State ---
system_state = {
    "mode": "IDLE",  # IDLE, INTERACTION
    "avatar_state": "SLEEP",
    "subtitle": "",
    "current_ad_json": "gaming_ad.json", # Default JSON to load for RAG
    "product_data": {
        "product": "Adorix Assistant",
        "context": "I am Adorix, your intelligent AI assistant. I can answer questions about our services and help you navigate the system."
    }
}

connected_clients = []
wake_word_service = None
main_loop = None # Added to capture the event loop from the main thread

async def broadcast_state():
    state_payload = json.dumps(system_state)
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

def on_wake_word():
    global system_state
    if system_state["mode"] == "IDLE":
        print(">>> [WAKE] Switching to INTERACTION mode")
        system_state["mode"] = "INTERACTION"
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
    print(">>> [System] Adorix Assistant Ready (Wake Word Active)")
    yield
    # Cleanup
    if wake_word_service:
        wake_word_service.stop()

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
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
    