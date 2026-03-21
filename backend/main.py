import os
import sys
import time
import json
import asyncio
import threading
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ─── VENV ISOLATION & PATHS ──────────────────────────────────────────────────
# Forcefully remove any AppData-related paths that poisoned the environment
sys.path = [p for p in sys.path if "appdata" not in p.lower()]

venv_base = r"C:\Users\deegh\OneDrive\Desktop\DEE\ADORIX\user detection\venv"
venv_site = os.path.join(venv_base, "Lib", "site-packages")

if os.path.exists(venv_site):
    if venv_site in sys.path: sys.path.remove(venv_site)
    sys.path.insert(0, venv_site)
    # CRITICAL: Add win32 paths for pywintypes/SAPI5 (Speech API)
    win32_path = os.path.join(venv_site, "win32")
    win32_lib_path = os.path.join(win32_path, "lib")
    if os.path.exists(win32_path): sys.path.insert(0, win32_path)
    if os.path.exists(win32_lib_path): sys.path.insert(0, win32_lib_path)

# Add local modules to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path: sys.path.append(current_dir)
modules_dir = os.path.join(current_dir, 'modules')
if modules_dir not in sys.path: sys.path.append(modules_dir)

ads_dir = os.path.join(current_dir, "ads")
# ─────────────────────────────────────────────────────────────────────────────

# ─── Local Modules ──────────────────────────────────────────────────────────────
from wake_word.wakeword import WakeWordService # Sherpa-ONNX implementation
from interaction.interaction_manager import start_interaction_loop
from vision_service import AdorixVision
from modules.ad_engine.selector import AdSelector
from modules.storage import start_background_sync

# ═══════════════════════════════════════════════════════════════════════════════
#  ADORIX ASYNC STATE MACHINE
# ═══════════════════════════════════════════════════════════════════════════════
class AdorixStateManager:

    MAX_PLAY_COUNT   = 2          # Limit personalized ad to exactly 2 plays
    COOLDOWN_SECONDS = 10         # Prevent rapid re-triggering after exiting State 2
    INTERACTION_TIMEOUT = 180.0   # Allow up to 3 minutes for a conversation

    def __init__(self):
        self.system_id    = 1     # Boot into Loop Mode
        self.mode         = "IDLE"
        self.avatar_state = "HIDDEN"
        self.subtitle     = ""
        self.ad_url       = ""    # Will be set after selector is loaded below
        self.play_count   = 0
        self.last_timeout_time = 0.0

        # Consensus Buffer (3-second stabilization)
        self.detection_buffer = []
        self.buffer_start_time = 0.0
        self.last_sight_time   = 0.0
        self.last_personalized_ad = None
        
        # Async loop reference for thread-safe calls
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = None

        # WebSocket management
        self.active_websockets: List[WebSocket] = []

        # Engines & Services
        rules_path = os.path.join(current_dir, "modules", "ad_engine", "rules.json")
        self.selector = AdSelector(rules_path, ads_dir)
        self.wake_word_service = None
        self._start_wake_word()

        # Pre-load the first idle ad so the very first WS broadcast has a real URL.
        # This prevents the frontend from showing 'Syncing with Loop Engine...' on startup.
        self.ad_url = self.selector.get_next_idle_ad()

        # Initialize Vision Service
        self.vision = AdorixVision(self.broadcast_state, self.selector)
        self.vision_thread = threading.Thread(target=self.run_vision, daemon=True)
        self.vision_thread.start()

    def _start_wake_word(self):
        if self.wake_word_service: self._stop_wake_word()
        self.wake_word_service = WakeWordService(callback_function=self.on_wake_word)
        threading.Thread(target=self.wake_word_service.start, daemon=True).start()

    def _stop_wake_word(self):
        if self.wake_word_service:
            # We assume WakeWordService has a stop method or can be safely orphaned
            self.wake_word_service = None

    async def broadcast_state(self, message: str = None):
        """Broadcasts current state to all connected frontends."""
        state_data = {
            "system_id": self.system_id,
            "mode": self.mode,
            "avatar_state": self.avatar_state,
            "subtitle": self.subtitle or message or "",
            "ad_url": self.ad_url,
            "show_listing": getattr(self, 'show_listing', False),
            "product_data": getattr(self, 'current_product_data', {}),
            "timestamp": time.time()
        }
        msg = json.dumps(state_data)
        for ws in self.active_websockets[:]:
            try:
                await ws.send_text(msg)
            except:
                self.active_websockets.remove(ws)

    def on_wake_word(self):
        """Callback from WakeWordService."""
        print("[WAKE] Wake word detected!")
        # Wake word only transitions to Interaction from State 2 (Personalized)
        if self.system_id == 2:
            asyncio.run_coroutine_threadsafe(
                self.transition_to_interaction(), 
                self.loop or asyncio.get_event_loop()
            )

    async def transition_to_personalized(self, age_gender: str):
        """State 1 -> State 2 Transition."""
        if self.system_id != 1: return
        
        # Check cooldown
        if time.time() - self.last_timeout_time < self.COOLDOWN_SECONDS:
            print("[STATE] Cooldown active. Ignoring detection.")
            return

        print(f"[STATE] Transitioning to State 2 (Personalized) for {age_gender}")
        
        # Select ad based on detected traits
        ad_url = self.selector.get_personalized_ad(age_gender)
        
        self.system_id = 2
        self.mode = "PERSONALIZED"
        self.avatar_state = "VISIBLE"
        self.ad_url = ad_url
        self.play_count = 0
        self.subtitle = f"Detected: {age_gender}. Playing personalized ad."
        
        await self.broadcast_state()

    async def handle_ad_ended(self):
        """Called when the frontend reports a video ended."""
        if self.system_id == 1:
            # Advance to the next ad in the idle rotation
            print("[STATE] Loop ad ended. Advancing to next idle ad.")
            self.ad_url = self.selector.get_next_idle_ad()
            await self.broadcast_state()

        elif self.system_id == 2:
            self.play_count += 1
            print(f"[STATE] Ad play count: {self.play_count}/{self.MAX_PLAY_COUNT}")
            
            if self.play_count >= self.MAX_PLAY_COUNT:
                print("[STATE] Ad limit reached. Returning to Loop Mode.")
                await self.transition_to_loop()
            else:
                self.subtitle = f"Playing ad (Repeat {self.play_count+1})"
                await self.broadcast_state()

    async def transition_to_interaction(self):
        """State 2 -> State 3 Transition."""
        if self.system_id != 2: return
        
        print("[STATE] Transitioning to State 3 (Interaction)")
        # Store context for RAG before clearing ad_url
        self.last_personalized_ad = self.ad_url
        
        # Load product data for the frontend listing
        self.current_product_data = {}
        if self.last_personalized_ad:
            json_name = self.last_personalized_ad.replace(".mp4", ".json")
            json_path = os.path.join(current_dir, "modules", "ad_engine", "data", json_name)
            try:
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        self.current_product_data = json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load product data: {e}")

        self.system_id = 3
        self.mode = "INTERACTIVE"
        self.avatar_state = "wakeup.webm"  # Trigger the waving animation
        self.ad_url = ""
        self.subtitle = "Initializing..."
        self.show_listing = False  # Initially hidden until after greeting
        
        await self.broadcast_state()
        
        # Hand off to the RAG/TTS/STT loop
        threading.Thread(target=self.run_interaction_loop, daemon=True).start()

    def run_interaction_loop(self):
        """Runs the blocking Interaction Manager."""
        try:
            # Helper to update frontend state from the blocking loop
            def update_ui(avatar_state=None, subtitle=None, show_listing=None):
                if avatar_state is not None: self.avatar_state = avatar_state
                if subtitle is not None:     self.subtitle = subtitle
                if show_listing is not None:  self.show_listing = show_listing
                asyncio.run_coroutine_threadsafe(
                    self.broadcast_state(), 
                    self.loop or asyncio.get_event_loop()
                )

            start_interaction_loop(
                current_ad_name=self.last_personalized_ad,
                state_callback=update_ui
            )
            # When interaction ends naturally:
            asyncio.run_coroutine_threadsafe(self.transition_to_loop(), self.loop or asyncio.get_event_loop())
        except Exception as e:
            print(f"[ERROR] Interaction loop crashed: {e}")
            asyncio.run_coroutine_threadsafe(self.transition_to_loop(), self.loop or asyncio.get_event_loop())

    async def transition_to_loop(self):
        """Transition back to State 1 (Loop Mode)."""
        print("[STATE] Transitioning to State 1 (Loop)")
        
        # Reset vision consensus buffers to ensure a clean start for State 1
        self.detection_buffer = []
        self.buffer_start_time = 0.0
        self.last_sight_time   = 0.0
        
        self.system_id = 1
        self.mode = "IDLE"
        self.avatar_state = "HIDDEN"
        # Always provide a real ad filename so the frontend LoopView has something to play.
        # Use the selector's round-robin idle rotation instead of empty string.
        self.ad_url = self.selector.get_next_idle_ad()
        self.subtitle = ""
        self.play_count = 0
        
        # Set to 0.0 to match the "normal" State 1 (boot) behavior, 
        # allowing face detection to trigger State 2 immediately.
        self.last_timeout_time = 0.0
        
        print(f"[STATE] State 1 synchronized. Camera is processing for {self.ad_url}")
        await self.broadcast_state()

    def run_vision(self):
        """Blocking Vision thread."""
        import cv2
        cap = cv2.VideoCapture(0)
        
        # Optional: Set camera backend (700 = MSMF on Windows)
        # cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

        if not cap.isOpened():
            print("[VISION] Error: Could not open camera.")
            return

        print("[VISION] Camera online.")
        while True:
            ret, frame = cap.read()
            if not ret: break

            # Process vision logic via the service
            # 1. Trigger non-blocking analyze (it spawns its own thread if not already mapping)
            self.vision.analyze(frame)
            
            # 2. Poll for the latest result (the service updates last_result when thread finishes)
            age_gender = self.vision.get_latest_result()
            
            # --- ROBUST CONSENSUS LOGIC ---
            if self.system_id == 1:
                now = time.time()
                
                if age_gender:
                    # We have a detection! Update last sight and add to buffer.
                    self.last_sight_time = now
                    if not self.detection_buffer:
                        self.buffer_start_time = now
                        print("[CONSENSUS] Starting 3s observation window...")
                    
                    self.detection_buffer.append(age_gender)
                    
                    # Check if 3s window is complete
                    if now - self.buffer_start_time >= 3.0:
                        from collections import Counter
                        counts = Counter(self.detection_buffer)
                        winner, freq = counts.most_common(1)[0]
                        total = len(self.detection_buffer)
                        
                        print(f"[CONSENSUS] Window complete. Winner: {winner} ({freq}/{total} samples)")
                        
                        # Reset buffer before transition to avoid re-triggering
                        self.detection_buffer = []
                        self.buffer_start_time = 0.0
                        
                        asyncio.run_coroutine_threadsafe(
                            self.transition_to_personalized(winner), 
                            self.loop or asyncio.get_event_loop()
                        )
                else:
                    # No face seen in this frame. Check for timeout.
                    # We allow up to 1.5s of "lost face" before we give up on the consensus.
                    if self.detection_buffer and (now - self.last_sight_time > 1.5):
                        print("[CONSENSUS] User lost for > 1.5s. Resetting buffer.")
                        self.detection_buffer = []
                        self.buffer_start_time = 0.0
            
            # Control loop speed (roughly 10 FPS)
            time.sleep(0.1)
        
        cap.release()

# ═══════════════════════════════════════════════════════════════════════════════
#  FASTAPI APP & ROUTES
# ═══════════════════════════════════════════════════════════════════════════════
state_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global state_manager
    print("\n" + "="*50)
    print(" SYSTEM BOOT: ADORIX AI KIOSK v2.1")
    print("="*50)
    
    # Initialize State Manager
    state_manager = AdorixStateManager()
    
    # Start background tasks
    # Fix: start_background_sync is async, so use create_task instead of threading.Thread
    asyncio.create_task(start_background_sync())
    
    yield
    print("[SYSTEM] Shutting down...")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve ads statically so frontend can access local files
if os.path.exists(ads_dir):
    app.mount("/ads", StaticFiles(directory=ads_dir), name="ads")

@app.get("/")
async def root():
    return {"status": "Adorix Backend Online", "state": state_manager.mode}

@app.get("/api/ads")
async def list_ads():
    """Returns a list of available .mp4 ad filenames from the ads directory.
    Used by the frontend to populate its offline fallback playlist.
    """
    try:
        files = sorted([
            f for f in os.listdir(ads_dir)
            if f.lower().endswith(".mp4")
        ])
        return files
    except Exception as e:
        return []

@app.post("/api/sync")
async def trigger_sync():
    """Triggers an immediate synchronization of ads from Supabase Storage & Database."""
    from modules.storage import async_sync_ads
    try:
        await async_sync_ads()
        # After sync, we should also refresh the selector's rules and file list
        if state_manager and state_manager.selector:
            state_manager.selector.rules = state_manager.selector._load()
            state_manager.selector.idle_ads = state_manager.selector._load_ads()
        return {"status": "Sync completed successfully"}
    except Exception as e:
        return {"status": "Sync failed", "error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state_manager.active_websockets.append(websocket)
    
    # Send initial state
    await state_manager.broadcast_state()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "AD_ENDED":
                await state_manager.handle_ad_ended()
            
            elif message.get("type") in ["WAKE_WORD_DETECTED", "SIMULATE_WAKE_WORD"]:
                print(">>> [WebSocket] Received simulation/wake word from frontend")
                if state_manager.system_id == 2:
                    await state_manager.transition_to_interaction()
                else:
                    print(f"[WS] Simulation ignored: System is in State {state_manager.system_id}")
                
    except Exception as e:
        print(f"[WS] Connection closed: {e}")
    finally:
        if websocket in state_manager.active_websockets:
            state_manager.active_websockets.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    # Use port 8002 as expected by frontend
    uvicorn.run(app, host="0.0.0.0", port=8002)
