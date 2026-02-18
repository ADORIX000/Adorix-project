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
import hashlib
from gtts import gTTS # Ensure you run: pip install gTTS

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
# Note: get_tts_file now replaces or supplements your local tts_engine.speak

# --- TTS Cache Configuration (Task #25) ---
TTS_CACHE_DIR = os.path.join(current_dir, "static/tts_cache")
os.makedirs(TTS_CACHE_DIR, exist_ok=True)

def get_tts_file(text: str, lang: str = 'en') -> str:
    """
    Requirement #25: Checks if a TTS file exists via hash. 
    If not, creates it and returns the path.
    """
    # Create a unique filename based on the text hash (Check requirement)
    text_hash = hashlib.md5(text.encode()).hexdigest()
    file_name = f"{text_hash}.mp3"
    file_path = os.path.join(TTS_CACHE_DIR, file_name)

    # Check if file already exists
    if os.path.exists(file_path):
        print(f"✅ [TTS] Cache Hit: {file_name}")
        return f"static/tts_cache/{file_name}"

    # If not, create it (Create requirement)
    try:
        print(f"🎙️ [TTS] Generating new file for: '{text[:20]}...'")
        tts = gTTS(text=text, lang=lang)
        tts.save(file_path)
        return f"static/tts_cache/{file_name}"
    except Exception as e:
        print(f"❌ [TTS] Error: {e}")
        return ""

# --- Global System State ---
system_state = {
    "mode": "IDLE", 
    "avatar_state": "SLEEP",
    "subtitle": "",
    "audio_url": "", # New field for TTS audio delivery
    "current_ad_json": "gaming_ad.json",
    "product_data": {
        "product": "Adorix Assistant",
        "context": "I am Adorix, your intelligent AI assistant."
    }
}

connected_clients = []
wake_word_service = None
main_loop = None 

async def broadcast_state():
    state_payload = json.dumps(system_state)
    if not connected_clients:
        return
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

def interaction_state_callback(avatar_state=None, subtitle=None):
    global system_state
    if avatar_state:
        system_state["avatar_state"] = avatar_state
    if subtitle is not None:
        system_state["subtitle"] = subtitle
        # When a subtitle is generated, check/create the TTS file
        if avatar_state == "SPEAKING" or subtitle != "":
            audio_path = get_tts_file(subtitle)
            # Prepend host info for frontend
            system_state["audio_url"] = f"http://localhost:8001/{audio_path}"
    
    sync_broadcast()

def on_wake_word():
    global system_state
    if system_state["mode"] == "IDLE":
        print(">>> [WAKE] Switching to INTERACTION mode")
        system_state["mode"] = "INTERACTION"
        system_state["avatar_state"] = "WAKE"
        system_state["subtitle"] = "Yes? I'm listening..."
        sync_broadcast()
        threading.Thread(target=handle_interaction, daemon=True).start()

def handle_interaction():
    global system_state
    try:
        result = start_interaction_loop(
            system_state["current_ad_json"], 
            state_callback=interaction_state_callback
        )
    except Exception as e:
        print(f"!!! [Interaction] Critical error: {e}")
    finally:
        system_state["mode"] = "IDLE"
        system_state["avatar_state"] = "SLEEP"
        system_state["subtitle"] = ""
        system_state["audio_url"] = ""
        sync_broadcast()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global wake_word_service, main_loop
    main_loop = asyncio.get_running_loop()
    wake_word_service = WakeWordService(callback_function=on_wake_word)
    threading.Thread(target=wake_word_service.start, daemon=True).start()
    yield
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

# --- Serving Static Files (Ads and TTS Cache) ---
if os.path.exists("backend/ads"):
    app.mount("/ads", StaticFiles(directory="backend/ads"), name="ads")

# Serves the TTS cache folder so the frontend can play the .mp3 files
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

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