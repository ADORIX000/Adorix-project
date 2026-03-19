import os
import sys
import json
import time
import asyncio
import threading
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ─── Path Setup ────────────────────────────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
modules_dir = os.path.join(current_dir, 'modules')
if modules_dir not in sys.path:
    sys.path.append(modules_dir)

ads_dir = os.path.join(current_dir, "ads")

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
        self.ad_url       = ""
        self.play_count   = 0
        self.last_timeout_time = 0.0

        # Multi-person / Playlist support
        self.personalized_playlist = []
        self.playlist_index = 0
        self.last_vision_time = 0.0

        self.command_queue   = asyncio.Queue()
        self.wake_word_event = asyncio.Event()
        self._interaction_abort = threading.Event()

        self.clients: List[WebSocket] = []
        self.main_loop = None

        self.ad_selector       = None
        self.wake_word_service = None
        self.vision_service    = None

    def set_ad_selector(self, selector: AdSelector):
        self.ad_selector = selector
        self.ad_url = selector.get_next_idle_ad()

    async def broadcast_state(self):
        """Pushes the current state to the Next.js frontend instantly via WebSockets."""
        payload = json.dumps({
            "type":         "SYSTEM_UPDATE",
            "system_id":    self.system_id,
            "mode":         self.mode,
            "avatar_state": self.avatar_state,
            "subtitle":     self.subtitle,
            "ad_url":       self.ad_url,
        })
        if not self.clients: return
        tasks = [c.send_text(payload) for c in self.clients]
        await asyncio.gather(*tasks, return_exceptions=True)

    def sync_broadcast(self):
        if self.main_loop and not self.main_loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.broadcast_state(), self.main_loop)

    def on_vision_update(self, data: dict):
        if self.main_loop and not self.main_loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.command_queue.put({"type": "VISION", "data": data}), self.main_loop)

    def on_wake_word(self):
        print("\n!!! [S2] Wake Word Detected !!!")
        if self.main_loop and not self.main_loop.is_closed():
            self.main_loop.call_soon_threadsafe(self.wake_word_event.set)

    def on_ad_end(self):
        if self.main_loop and not self.main_loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.command_queue.put({"type": "AD_ENDED"}), self.main_loop)

    def _start_wake_word(self):
        if self.wake_word_service: self._stop_wake_word()
        self.wake_word_service = WakeWordService(callback_function=self.on_wake_word)
        threading.Thread(target=self.wake_word_service.start, daemon=True).start()

    def _stop_wake_word(self):
        if self.wake_word_service:
            try: self.wake_word_service.stop()
            except Exception: pass
            self.wake_word_service = None

    async def run(self):
        """The core heartbeat loop of the kiosk."""
        self.main_loop = asyncio.get_running_loop()
        print("\n" + "=" * 60)
        print("  ADORIX STATE MACHINE — ONLINE")
        print("=" * 60 + "\n")
        
        while True:
            if self.system_id == 1: await self._state_loop()
            elif self.system_id == 2: await self._state_personalized()
            elif self.system_id == 3: await self._state_interaction()
            await asyncio.sleep(0.05)

    # ══════════════════════════════════════════════════════════════════════════
    #  STATE 1 — LOOP MODE
    # ══════════════════════════════════════════════════════════════════════════
    async def _state_loop(self):
        print(">>> [S1] Entering LOOP MODE")
        self.system_id = 1
        self.avatar_state = "HIDDEN"
        self._stop_wake_word()

        self.ad_url = self.ad_selector.get_next_idle_ad()
        await self.broadcast_state()

        while not self.command_queue.empty(): self.command_queue.get_nowait()

        while self.system_id == 1:
            try: 
                msg = await asyncio.wait_for(self.command_queue.get(), timeout=1.0)
            except asyncio.TimeoutError: 
                continue

            if msg.get("type") == "VISION":
                data = msg.get("data", {})
                if data.get("system_id") == 2:
                    if (time.time() - self.last_timeout_time) < self.COOLDOWN_SECONDS:
                        continue
                        
                    demographics = data.get("demographics", [])
                    if demographics:
                        self.personalized_playlist = self.ad_selector.get_playlist_for_demographics(demographics)
                        self.playlist_index = 0
                        self.ad_url = self.personalized_playlist[self.playlist_index]
                        self.last_vision_time = time.time()
                        
                        self.system_id = 2
                        return

            elif msg.get("type") == "AD_ENDED":
                self.ad_url = self.ad_selector.get_next_idle_ad()
                await self.broadcast_state()

    # ══════════════════════════════════════════════════════════════════════════
    #  STATE 2 — PERSONALIZED MODE
    # ══════════════════════════════════════════════════════════════════════════
    async def _state_personalized(self):
        print(f">>> [S2] Entering PERSONALIZED MODE (Playlist: {self.personalized_playlist})")
        self.system_id = 2
        self.play_count = 0
        session_start_time = time.time()
        
        self.wake_word_event.clear()
        self._start_wake_word()
        await self.broadcast_state()

        while not self.command_queue.empty(): self.command_queue.get_nowait()

        while self.system_id == 2:
            if self.wake_word_event.is_set():
                print(">>> [S2] Wake word detected!")
                watch_time = int(time.time() - session_start_time)
                asyncio.create_task(self._push_analytics(self.ad_url, watch_time, engage_count=1))
                self.system_id = 3
                return

            if time.time() - self.last_vision_time > 5.0:
                print(">>> [S2] No vision detection for 5s. Returning to S1.")
                self.last_timeout_time = time.time()
                self.system_id = 1
                self._stop_wake_word()
                return

            try: 
                msg = await asyncio.wait_for(self.command_queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                continue

            if msg.get("type") == "VISION":
                data = msg.get("data", {})
                if data.get("system_id") == 2:
                    self.last_vision_time = time.time()

            elif msg.get("type") == "AD_ENDED":
                self.play_count += 1
                if self.personalized_playlist:
                    self.playlist_index = (self.playlist_index + 1) % len(self.personalized_playlist)
                    self.ad_url = self.personalized_playlist[self.playlist_index]
                
                if self.play_count >= max(self.MAX_PLAY_COUNT, len(self.personalized_playlist)):
                    print(">>> [S2] Personalized session complete. Returning to S1.")
                    self.last_timeout_time = time.time()
                    self.system_id = 1
                    self._stop_wake_word()
                    return
                else:
                    await self.broadcast_state()

    async def _push_analytics(self, ad_id: str, watch_time: int, engage_count: int):
        """Dummy helper to format and print Supabase payload without blocking."""
        payload = {
            "ad_id": ad_id,
            "watch_time_seconds": watch_time,
            "engage_count": engage_count,
            "timestamp": time.time()
        }
        print(f"[ANALYTICS] Ready for Supabase -> {json.dumps(payload)}")
        # In the future, the Supabase insert call goes here

    # ══════════════════════════════════════════════════════════════════════════
    #  STATE 3 — INTERACTION MODE
    # ══════════════════════════════════════════════════════════════════════════
    async def _state_interaction(self):
        print(">>> [S3] Entering INTERACTION MODE")
        self.system_id = 3
        self.avatar_state = "wakeup.webm"
        session_start_time = time.time()
        
        # Stop wake word engine so STT can use the microphone
        self._stop_wake_word()
        self._interaction_abort.clear()
        await self.broadcast_state()

        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(None, self._run_interaction_sync, self.ad_url)

        try: 
            await asyncio.wait_for(future, timeout=self.INTERACTION_TIMEOUT)
        except asyncio.TimeoutError: 
            print(">>> [S3] Interaction timeout reached. Aborting.")
            self._interaction_abort.set()

        print(">>> [S3] Conversation ended. Returning to S1.")
        
        # Track analytics for the total duration of the conversation
        watch_time = int(time.time() - session_start_time)
        asyncio.create_task(self._push_analytics(self.ad_url, watch_time, engage_count=1))
        
        self.system_id = 1
        self.avatar_state = "HIDDEN"
        self.ad_url = self.ad_selector.get_next_idle_ad()
        await self.broadcast_state()

    def _run_interaction_sync(self, ad_url: str):
        try:
            def is_active(): return self.system_id == 3 and not self._interaction_abort.is_set()
            def state_cb(avatar_state=None, subtitle=None):
                if avatar_state: self.avatar_state = avatar_state
                if subtitle: self.subtitle = subtitle
                self.sync_broadcast()

            # Execute your TinyLlama / TTS Logic
            start_interaction_loop(current_ad_name=ad_url, state_callback=state_cb, is_active_callback=is_active)
        except Exception as exc: print(f"Error in S3: {exc}")

manager = AdorixStateManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("LIFESPAN: Starting...")
    asyncio.create_task(start_background_sync(interval_seconds=300))
    print("LIFESPAN: Background sync task created.")
    
    rules_path = os.path.join(current_dir, "modules", "ad_engine", "rules.json")
    selector = AdSelector(rules_path, ads_dir)
    print("LIFESPAN: Ad selector initialized.")
    manager.set_ad_selector(selector)
    print("LIFESPAN: Manager ad selector set.")
    asyncio.create_task(manager.run())
    print("LIFESPAN: Manager run task created.")
    
    print("LIFESPAN: Initializing AdorixVision...")
    try:
        manager.vision_service = AdorixVision(broadcast_callback=manager.on_vision_update, selector=selector)
        print("LIFESPAN: AdorixVision initialized, starting thread...")
        threading.Thread(target=manager.vision_service.start, daemon=True).start()
        print("LIFESPAN: Thread started. Yielding to uvicorn...")
    except Exception as vision_err:
        print(f"LIFESPAN: ERROR starting AdorixVision: {vision_err}")
    yield
    print("LIFESPAN: Shutting down...")
    manager._stop_wake_word()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

from fastapi import Request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # print(f"MIDDLEWARE: Received request {request.method} {request.url}")
    response = await call_next(request)
    # print(f"MIDDLEWARE: Returning response {response.status_code}")
    return response

if os.path.exists(ads_dir):
    app.mount("/ads", StaticFiles(directory=ads_dir), name="ads")

@app.get("/api/status")
async def get_status():
    return {
        "system_id": manager.system_id,
        "mode":      manager.mode,
        "ad_url":    manager.ad_url,
    }

@app.get("/api/ads")
async def list_ads():
    if not os.path.exists(ads_dir):
        return []
    return [f for f in os.listdir(ads_dir) if f.lower().endswith(('.mp4', '.webm'))]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    manager.clients.append(websocket)
    try:
        await manager.broadcast_state()
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
                if msg.get("type") == "AD_ENDED":
                    manager.on_ad_end()
                elif msg.get("type") == "WAKE_WORD_DETECTED":
                    manager.on_wake_word()
            except Exception: pass
    except WebSocketDisconnect:
        manager.clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
