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
# Note: WakeWordService is now powered by Sherpa-ONNX under the hood
from wake_word.wakeword import WakeWordService 
from interaction.interaction_manager import start_interaction_loop
from vision_service import AdorixVision
from modules.ad_engine.selector import AdSelector
from modules.storage import sync_ads


# ═══════════════════════════════════════════════════════════════════════════════
#  ADORIX ASYNC STATE MACHINE (The Brain)
#  States:
#    1 — Loop Mode       (default ad playlist, OpenCV face detection active)
#    2 — Personalized    (targeted ad × 3, Sherpa-ONNX wake word active)
#    3 — Interaction     (avatar UI + TinyLlama LLM + Edge-TTS conversation)
# ═══════════════════════════════════════════════════════════════════════════════
class AdorixStateManager:

    MAX_PLAY_COUNT   = 3          # Transition State-2 → State-1 after this many ad plays
    COOLDOWN_SECONDS = 10         # Ignore OpenCV re-triggers immediately after exiting State-2
    INTERACTION_TIMEOUT = 8.0     # Max seconds to wait for interaction thread to cleanly abort

    def __init__(self):
        # ── Core State ──────────────────────────────────────────────────────
        self.system_id    = 1       # Boot into default Loop Mode
        self.mode         = "IDLE"
        self.avatar_state = "HIDDEN"
        self.subtitle     = ""
        self.ad_url       = ""
        self.play_count   = 0
        self.last_timeout_time = 0.0

        # ── Async Primitives (Thread Safety) ────────────────────────────────
        # command_queue: Receives hardware events safely into the async loop
        self.command_queue   = asyncio.Queue()
        
        # wake_word_event: Tripped by the Sherpa-ONNX thread, cleared on State-2 entry
        self.wake_word_event = asyncio.Event()
        
        # _interaction_abort: Allows the sync interaction thread to exit if user walks away
        self._interaction_abort = threading.Event()

        # ── Network ─────────────────────────────────────────────────────────
        self.clients: List[WebSocket] = []  # Connected React Dashboards/Kiosks
        self.main_loop = None               # Reference to FastAPI's event loop

        # ── Hardware Services ───────────────────────────────────────────────
        self.ad_selector       = None
        self.wake_word_service = None
        self.vision_service    = None

    def set_ad_selector(self, selector: AdSelector):
        """Initializes the ad logic and grabs the first default video."""
        self.ad_selector = selector
        self.ad_url = selector.get_next_idle_ad()

    # ──────────────────────────────────────────────────────────────────────────
    #  WebSocket Broadcasters (Backend → Frontend)
    # ──────────────────────────────────────────────────────────────────────────
    async def broadcast_state(self):
        """Pushes the current state to the React frontend instantly."""
        payload = json.dumps({
            "type":         "SYSTEM_UPDATE",
            "system_id":    self.system_id,
            "mode":         self.mode,
            "avatar_state": self.avatar_state,
            "subtitle":     self.subtitle,
            "ad_url":       self.ad_url,
        })
        if not self.clients:
            return
        tasks = [c.send_text(payload) for c in self.clients]
        await asyncio.gather(*tasks, return_exceptions=True)

    def sync_broadcast(self):
        """Allows blocking threads (like interaction) to trigger a WebSocket update."""
        if self.main_loop and not self.main_loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.broadcast_state(), self.main_loop)

    # ──────────────────────────────────────────────────────────────────────────
    #  Hardware Event Handlers (Called by external threads)
    # ──────────────────────────────────────────────────────────────────────────
    def on_vision_update(self, data: dict):
        """OpenCV thread pushes face detection results here."""
        if self.main_loop and not self.main_loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.command_queue.put({"type": "VISION", "data": data}),
                self.main_loop,
            )

    def on_wake_word(self):
        """Sherpa-ONNX thread signals the wake word was detected."""
        print("\n!!! [S2] Sherpa-ONNX Wake Word Detected !!!")
        if self.main_loop and not self.main_loop.is_closed():
            self.main_loop.call_soon_threadsafe(self.wake_word_event.set)

    def on_ad_end(self):
        """React frontend signals via WS that the HTML5 video finished playing."""
        if self.main_loop and not self.main_loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.command_queue.put({"type": "AD_ENDED"}),
                self.main_loop,
            )

    # ──────────────────────────────────────────────────────────────────────────
    #  Audio Microphone Lifecycle
    # ──────────────────────────────────────────────────────────────────────────
    def _start_wake_word(self):
        """Boots up the Sherpa-ONNX listening thread."""
        if self.wake_word_service:
            self._stop_wake_word()
        print(">>> [System] Starting Sherpa-ONNX Wake Word Service...")
        self.wake_word_service = WakeWordService(callback_function=self.on_wake_word)
        threading.Thread(target=self.wake_word_service.start, daemon=True).start()

    def _stop_wake_word(self):
        """Kills the Sherpa-ONNX thread to free the mic for Interaction Mode."""
        if self.wake_word_service:
            print(">>> [System] Stopping Sherpa-ONNX Wake Word Service...")
            try:
                self.wake_word_service.stop()
            except Exception as e:
                print(f"!!! [System] Error stopping wake word: {e}")
            self.wake_word_service = None

    # ──────────────────────────────────────────────────────────────────────────
    #  Main Orchestration Loop
    # ──────────────────────────────────────────────────────────────────────────
    async def run(self):
        """The core heartbeat of the kiosk state machine."""
        self.main_loop = asyncio.get_running_loop()
        print("\n" + "=" * 60)
        print("  ADORIX STATE MACHINE — ONLINE")
        print("=" * 60 + "\n")

        while True:
            if self.system_id == 1:
                await self._state_loop()
            elif self.system_id == 2:
                await self._state_personalized()
            elif self.system_id == 3:
                await self._state_interaction()
            
            # Prevents 100% CPU lockup if a state exits too quickly
            await asyncio.sleep(0.05)

    # ══════════════════════════════════════════════════════════════════════════
    #  STATE 1 — LOOP MODE (Passive Video, Active Vision)
    # ══════════════════════════════════════════════════════════════════════════
    async def _state_loop(self):
        print(">>> [S1] Entering LOOP MODE")
        self.system_id    = 1
        self.mode         = "IDLE"
        self.avatar_state = "HIDDEN"
        self.subtitle     = ""

        # Ensure mic is not listening to save Pi CPU
        self._stop_wake_word()

        if not self.ad_url:
            self.ad_url = self.ad_selector.get_next_idle_ad()
        await self.broadcast_state()

        # Clear old events
        while not self.command_queue.empty():
            self.command_queue.get_nowait()

        while self.system_id == 1:
            try:
                msg = await asyncio.wait_for(self.command_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            msg_type = msg.get("type")

            if msg_type == "VISION":
                data   = msg.get("data", {})
                new_id = data.get("system_id")

                if new_id == 2:
                    # Prevent rapid re-triggering if user just finished an interaction
                    elapsed = time.time() - self.last_timeout_time
                    if elapsed < self.COOLDOWN_SECONDS:
                        continue

                    ad_url = data.get("ad_url", "")
                    print(f">>> [S1] Face confirmed → Transition S1→S2 (ad={ad_url})")
                    self.system_id = 2
                    self.ad_url    = ad_url
                    self.play_count = 0
                    return  # Route to State 2

            elif msg_type == "AD_ENDED":
                self.ad_url = self.ad_selector.get_next_idle_ad()
                print(f">>> [S1] Advancing playlist → {self.ad_url}")
                await self.broadcast_state()

    # ══════════════════════════════════════════════════════════════════════════
    #  STATE 2 — PERSONALIZED MODE (Targeted Video, Active Wake Word)
    # ══════════════════════════════════════════════════════════════════════════
    async def _state_personalized(self):
        print(f">>> [S2] Entering PERSONALIZED MODE  (ad={self.ad_url})")
        self.system_id    = 2
        self.play_count   = 0
        
        self.wake_word_event.clear()
        self._start_wake_word() # Boot up Sherpa-ONNX
        await self.broadcast_state()

        while not self.command_queue.empty():
            self.command_queue.get_nowait()

        while self.system_id == 2:
            # PRIORITY CHECK: Did Sherpa-ONNX hear the wake word?
            if self.wake_word_event.is_set():
                print(">>> [S2] PATH A — Wake word! Transition S2→S3")
                self.system_id = 3
                return

            try:
                msg = await asyncio.wait_for(self.command_queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                await asyncio.sleep(0.01)
                continue

            msg_type = msg.get("type")

            if msg_type == "AD_ENDED":
                self.play_count += 1
                print(f">>> [S2] Ad play count: {self.play_count}/{self.MAX_PLAY_COUNT}")

                if self.play_count >= self.MAX_PLAY_COUNT:
                    print(">>> [S2] PATH B — Max plays reached. Transition S2→S1")
                    self.last_timeout_time = time.time()
                    self.system_id = 1
                    self._stop_wake_word()
                    return
                else:
                    await self.broadcast_state() # Trigger replay on frontend

            elif msg_type == "VISION":
                if msg.get("data", {}).get("system_id") == 1:
                    print(">>> [S2] PATH C — User walked away. Transition S2→S1")
                    self.system_id = 1
                    self._stop_wake_word()
                    return

    # ══════════════════════════════════════════════════════════════════════════
    #  STATE 3 — INTERACTION MODE (Avatar UI, Active LLM/TTS)
    # ══════════════════════════════════════════════════════════════════════════
    async def _state_interaction(self):
        print(">>> [S3] Entering INTERACTION MODE")
        self.system_id    = 3
        self.mode         = "INTERACTION"
        self.avatar_state = "wakeup.webm"
        self.subtitle     = "Yes? I'm listening..."

        # CRITICAL: Free the mic for the speech recognition module
        self._stop_wake_word()
        self._interaction_abort.clear()
        await self.broadcast_state()

        # Run the heavy LLM/TTS interaction in a separate thread so FastAPI doesn't freeze
        loop   = asyncio.get_running_loop()
        future = loop.run_in_executor(None, self._run_interaction_sync, self.ad_url)

        user_lost = False
        while not future.done():
            try:
                msg = await asyncio.wait_for(self.command_queue.get(), timeout=0.3)
            except asyncio.TimeoutError:
                continue

            if msg.get("type") == "VISION":
                if msg["data"].get("system_id") == 1:
                    print(">>> [S3] User lost during interaction — sending abort signal!")
                    self._interaction_abort.set()
                    user_lost = True
                    break

        if not future.done():
            try:
                await asyncio.wait_for(asyncio.shield(future), timeout=self.INTERACTION_TIMEOUT)
            except asyncio.TimeoutError:
                print(f">>> [S3] Interaction thread timeout ({self.INTERACTION_TIMEOUT}s). Forcing exit.")
        else:
            try:
                future.result()
            except Exception:
                pass

        print(f">>> [S3] Interaction finished. Transition S3→S1")
        self.system_id    = 1
        self.mode         = "IDLE"
        self.avatar_state = "SLEEP"
        self.subtitle     = ""
        self.ad_url       = self.ad_selector.get_next_idle_ad()
        await self.broadcast_state()

    def _run_interaction_sync(self, ad_url: str):
        """Thread-safe wrapper for the blocking interaction logic."""
        try:
            def is_active() -> bool:
                return self.system_id == 3 and not self._interaction_abort.is_set()

            def state_callback(avatar_state=None, subtitle=None):
                if avatar_state is not None:
                    self.avatar_state = avatar_state
                if subtitle is not None:
                    self.subtitle = subtitle
                self.sync_broadcast()

            start_interaction_loop(
                current_ad_name=ad_url,
                state_callback=state_callback,
                is_active_callback=is_active,
            )
        except Exception as exc:
            print(f"!!! [S3] Interaction error: {exc}")


# ─── Global Manager ────────────────────────────────────────────────────────────
manager = AdorixStateManager()


# ═══════════════════════════════════════════════════════════════════════════════
#  FASTAPI SERVER LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("  ADORIX BACKEND — INITIALIZING")
    print("=" * 60 + "\n")

    # 1. Init Ad Engine
    rules_path = os.path.join(current_dir, "modules", "ad_engine", "rules.json")
    selector   = AdSelector(rules_path, ads_dir)
    manager.set_ad_selector(selector)

    # 2. Boot State Machine Task
    asyncio.create_task(manager.run())

    # 3. Boot Vision Thread (OpenCV)
    manager.vision_service = AdorixVision(
        broadcast_callback=manager.on_vision_update,
        selector=selector,
    )
    threading.Thread(target=manager.vision_service.start, daemon=True).start()

    # 4. Cloud Sync (Initial boot + periodic checks)
    threading.Thread(target=sync_ads, daemon=True).start()

    async def _periodic_sync():
        while True:
            await asyncio.sleep(600) # Check Backblaze every 10 min
            await asyncio.to_thread(sync_ads)

    asyncio.create_task(_periodic_sync())

    yield # Let FastAPI handle requests

    # Cleanup on exit
    manager._stop_wake_word()
    print(">>> [System] Shutdown complete.")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists(ads_dir):
    app.mount("/ads", StaticFiles(directory=ads_dir), name="ads")


# ─── REST & WebSocket Endpoints ────────────────────────────────────────────────
@app.get("/api/status")
async def get_status():
    return {
        "system_id": manager.system_id,
        "mode":      manager.mode,
        "ad_url":    manager.ad_url,
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    manager.clients.append(websocket)
    print(f">>> [WS] Client connected. Total: {len(manager.clients)}")

    try:
        # Push initial state immediately
        await manager.broadcast_state()

        while True:
            raw  = await websocket.receive_text()
            try:
                msg = json.loads(raw)
                # Next.js tells us the video is done
                if msg.get("type") in ("AD_LOOP_TIMEOUT", "NEXT_AD", "AD_ENDED"):
                    manager.on_ad_end()
            except Exception as exc:
                print(f"!!! [WS] Message parse error: {exc}")

    except WebSocketDisconnect:
        manager.clients.remove(websocket)
        print(f">>> [WS] Client disconnected. Total: {len(manager.clients)}")


# ─── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("\n>>> [System] Starting uvicorn on port 8002...")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8002)
    except Exception as e:
        print(f"!!! [System] Uvicorn failed to start: {e}")