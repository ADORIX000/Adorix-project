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
from interaction_manager import start_interaction_loop
from tts_engine import speak

# --- Global System State ---
system_state = {
    "mode": "IDLE",  # IDLE, INTERACTION
    "avatar_state": "SLEEP",
    "subtitle": "",
    "product_data": {
        "product": "Adorix Assistant",
        "context": "I am Adorix, your intelligent AI assistant. I can answer questions about our services and help you navigate the system."
    }
}

connected_clients = []
wake_word_service = None

async def broadcast_state():
    state_payload = json.dumps(system_state)
    for client in connected_clients:
        try:
            await client.send_text(state_payload)
        except:
            pass

def on_wake_word():
    global system_state
    if system_state["mode"] == "IDLE":
        print(">>> [WAKE] Switching to INTERACTION mode")
        system_state["mode"] = "INTERACTION"
        system_state["avatar_state"] = "WAKE"
        
        # Broadcasting state update
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(broadcast_state())
        
        # Start the interaction loop
        handle_interaction()

def handle_interaction():
    global system_state
    # This runs the interaction loop (STT -> LLM -> TTS)
    result = start_interaction_loop(system_state["product_data"])
    if result == "TIMEOUT":
        system_state["mode"] = "IDLE"
        system_state["avatar_state"] = "SLEEP"
    
    # Final broadcast
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(broadcast_state())

@asynccontextmanager
async def lifespan(app: FastAPI):
    global wake_word_service
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
    uvicorn.run(app, host="0.0.0.0", port=8000)