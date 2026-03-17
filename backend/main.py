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
from typing import List

# ─── Path Setup ────────────────────────────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
modules_dir = os.path.join(current_dir, 'modules')
if modules_dir not in sys.path:
    sys.path.append(modules_dir)

ads_dir = os.path.join(current_dir, "ads")

# ─── Local Modules ──────────────────────────────────────────────────────────────
from wake_word import WakeWordService
from interaction.interaction_manager import start_interaction_loop
from vision_service import AdorixVision
from modules.ad_engine.selector import AdSelector


# ═══════════════════════════════════════════════════════════════════════════════
#  ADORIX ASYNC STATE MACHINE
#  States:
#    1 — Loop Mode       (default ad playlist, face detection running)
#    2 — Personalized    (targeted ad × 3, wake word active)
#    3 — Interaction     (avatar + LLM + TTS conversation)
# ═══════════════════════════════════════════════════════════════════════════════
class AdorixStateManager:

    MAX_PLAY_COUNT   = 3          # State-2 → State-1 after this many plays
    COOLDOWN_SECONDS = 10         # Ignore re-trigger after State-2 timeout
    INTERACTION_TIMEOUT = 8.0     # Seconds to wait for interaction thread on abort

    def __init__(self):
        # ── Core State ──────────────────────────────────────────────────────
        self.system_id    = 1       # Current FSM state
        self.mode         = "IDLE"
        self.avatar_state = "HIDDEN"
        self.subtitle     = ""
        self.ad_url       = ""
        self.play_count   = 0
        self.last_timeout_time = 0.0

        # ── Async Primitives ────────────────────────────────────────────────
        # command_queue: receives events from hardware threads
        #   {"type": "VISION",   "data": {...}}
        #   {"type": "AD_ENDED"}
        self.command_queue   = asyncio.Queue()

        # wake_word_event: set() by the Picovoice thread, cleared on State-2 entry
        self.wake_word_event = asyncio.Event()

        # _interaction_abort: threading.Event checked by the sync interaction
        # thread so it can exit cleanly when the user walks away mid-conversation
        self._interaction_abort = threading.Event()

        # ── WebSocket Clients ────────────────────────────────────────────────
        self.clients: List[WebSocket] = []

        # ── Reference to the running asyncio loop (set in run()) ─────────────
        self.main_loop = None

        # ── Service references ────────────────────────────────────────────────
        self.ad_selector      = None
        self.wake_word_service = None
        self.vision_service    = None

    # ──────────────────────────────────────────────────────────────────────────
    #  Setup helpers
    # ──────────────────────────────────────────────────────────────────────────
    def set_ad_selector(self, selector: AdSelector):
        self.ad_selector = selector
        self.ad_url = selector.get_next_idle_ad()

    # ──────────────────────────────────────────────────────────────────────────
    #  WebSocket broadcast
    # ──────────────────────────────────────────────────────────────────────────
    async def broadcast_state(self):
        """Push current state to every connected WebSocket client."""
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
        """Thread-safe broadcast helper (call from any non-async thread)."""
        if self.main_loop and not self.main_loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.broadcast_state(), self.main_loop)

    # ──────────────────────────────────────────────────────────────────────────
    #  External event handlers — called from hardware threads
    # ──────────────────────────────────────────────────────────────────────────
    def on_vision_update(self, data: dict):
        """Vision thread pushes detection results here (thread-safe)."""
        if self.main_loop and not self.main_loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.command_queue.put({"type": "VISION", "data": data}),
                self.main_loop,
            )

    def on_wake_word(self):
        """Picovoice thread signals wake word detection (thread-safe)."""
        print("\n!!! [S2] Wake Word Detected !!!")
        if self.main_loop and not self.main_loop.is_closed():
            self.main_loop.call_soon_threadsafe(self.wake_word_event.set)

    def on_ad_end(self):
        """Frontend signals that the current ad finished playing (thread-safe)."""
        if self.main_loop and not self.main_loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.command_queue.put({"type": "AD_ENDED"}),
                self.main_loop,
            )

    # ──────────────────────────────────────────────────────────────────────────
    #  Hardware lifecycle helpers
    # ──────────────────────────────────────────────────────────────────────────
    def _start_wake_word(self):
        if self.wake_word_service:
            self._stop_wake_word()
        print(">>> [System] Starting Wake Word Service...")
        self.wake_word_service = WakeWordService(callback_function=self.on_wake_word)
        threading.Thread(target=self.wake_word_service.start, daemon=True).start()

    def _stop_wake_word(self):
        if self.wake_word_service:
            print(">>> [System] Stopping Wake Word Service...")
            try:
                self.wake_word_service.stop()
            except Exception:
                pass
            self.wake_word_service = None

    # ──────────────────────────────────────────────────────────────────────────
    #  Main orchestration loop
    # ──────────────────────────────────────────────────────────────────────────
    async def run(self):
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
            # Safety yield — prevents 100% CPU if a state exits immediately
            await asyncio.sleep(0.05)

    # ══════════════════════════════════════════════════════════════════════════
    #  STATE 1 — LOOP MODE
    # ══════════════════════════════════════════════════════════════════════════
    async def _state_loop(self):
        """
        Continuously cycle through generic ads.
        Watches for a confirmed face detection to transition → State 2.
        Wake word service is OFF in this state (nothing to wake).
        """
        print(">>> [S1] Entering LOOP MODE")
        self.system_id    = 1
        self.mode         = "IDLE"
        self.avatar_state = "HIDDEN"
        self.subtitle     = ""

        # Ensure wake word is stopped when we arrive (could be coming from S3)
        self._stop_wake_word()

        if not self.ad_url:
            self.ad_url = self.ad_selector.get_next_idle_ad()
        await self.broadcast_state()

        # Drain any stale messages left in the queue from the previous state
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
                    # ── Cooldown guard ───────────────────────────────────────
                    elapsed = time.time() - self.last_timeout_time
                    if elapsed < self.COOLDOWN_SECONDS:
                        remaining = round(self.COOLDOWN_SECONDS - elapsed, 1)
                        print(f">>> [S1] Cooldown active ({remaining}s left). Ignoring.")
                        # Vision re-sends ~1×/sec so we don't need to preserve the msg
                        continue

                    ad_url = data.get("ad_url", "")
                    print(f">>> [S1] Face confirmed → Transition S1→S2 (ad={ad_url})")
                    self.system_id = 2
                    self.ad_url    = ad_url
                    self.play_count = 0
                    return  # back to main loop → _state_personalized()

                # new_id == 1 while already in State 1 — ignore

            elif msg_type == "AD_ENDED":
                # Advance to the next idle ad in the playlist
                self.ad_url = self.ad_selector.get_next_idle_ad()
                print(f">>> [S1] Advancing playlist → {self.ad_url}")
                await self.broadcast_state()

    # ══════════════════════════════════════════════════════════════════════════
    #  STATE 2 — PERSONALIZED MODE
    # ══════════════════════════════════════════════════════════════════════════
    async def _state_personalized(self):
        """
        Play the targeted ad up to MAX_PLAY_COUNT times.

        Path A: Wake word detected → State 3  (highest priority)
        Path B: Ad plays N times without wake word → State 1 (cooldown set)
        Path C: Vision loses the user mid-play → State 1
        """
        print(f">>> [S2] Entering PERSONALIZED MODE  (ad={self.ad_url})")
        self.system_id    = 2
        self.play_count   = 0
        self.mode         = "IDLE"
        self.avatar_state = "HIDDEN"

        # ── Clear wake-word event from any previous trigger ──────────────────
        self.wake_word_event.clear()

        # ── Start mic listener ───────────────────────────────────────────────
        self._start_wake_word()

        await self.broadcast_state()

        # Drain stale queue messages from State 1
        while not self.command_queue.empty():
            self.command_queue.get_nowait()

        while self.system_id == 2:

            # ── Priority 1: check wake word event (set by Picovoice thread) ──
            # This is polled at the top of every loop tick so it is never
            # delayed by a long queue.get() call.
            if self.wake_word_event.is_set():
                print(">>> [S2] PATH A — Wake word! Transition S2→S3")
                self.system_id = 3
                # Wake word service is stopped inside _state_interaction()
                return

            # ── Priority 2: check command queue (non-blocking, short timeout) ─
            try:
                msg = await asyncio.wait_for(self.command_queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                # No message — loop back and re-check wake_word_event
                await asyncio.sleep(0.01)
                continue

            msg_type = msg.get("type")

            if msg_type == "AD_ENDED":
                self.play_count += 1
                print(f">>> [S2] Ad play count: {self.play_count}/{self.MAX_PLAY_COUNT}")

                if self.play_count >= self.MAX_PLAY_COUNT:
                    # ── Path B ────────────────────────────────────────────────
                    print(">>> [S2] PATH B — Max plays reached. Transition S2→S1")
                    self.last_timeout_time = time.time()
                    self.system_id = 1
                    self._stop_wake_word()     # ← was missing in original code
                    return
                else:
                    # Replay the same ad (frontend uses play_count to decide)
                    await self.broadcast_state()

            elif msg_type == "VISION":
                data   = msg.get("data", {})
                new_id = data.get("system_id")

                if new_id == 1:
                    # ── Path C: user walked away ──────────────────────────────
                    print(">>> [S2] PATH C — User lost. Transition S2→S1")
                    self.system_id = 1
                    self._stop_wake_word()
                    return
                # new_id == 2 while in State 2 — fresh detection, ignore

    # ══════════════════════════════════════════════════════════════════════════
    #  STATE 3 — INTERACTION MODE
    # ══════════════════════════════════════════════════════════════════════════
    async def _state_interaction(self):
        """
        Full avatar conversation loop (speech → LLM → TTS).

        Transition back to State 1 when:
          • The interaction concludes naturally, OR
          • Vision loses the user (abort path)
        """
        print(">>> [S3] Entering INTERACTION MODE")
        self.system_id    = 3
        self.mode         = "INTERACTION"
        self.avatar_state = "wakeup.webm"
        self.subtitle     = "Yes? I'm listening..."

        # ── Stop mic listener to free the audio device ───────────────────────
        self._stop_wake_word()

        # ── Reset abort signal ───────────────────────────────────────────────
        self._interaction_abort.clear()

        await self.broadcast_state()

        # Drain stale queue messages (e.g. leftover AD_ENDED from State 2)
        while not self.command_queue.empty():
            self.command_queue.get_nowait()

        # ── Run blocking interaction in a thread executor ────────────────────
        loop   = asyncio.get_running_loop()
        future = loop.run_in_executor(None, self._run_interaction_sync, self.ad_url)

        # ── While interaction runs, watch for "user walked away" ─────────────
        user_lost = False
        while not future.done():
            try:
                msg = await asyncio.wait_for(self.command_queue.get(), timeout=0.3)
            except asyncio.TimeoutError:
                continue

            if msg.get("type") == "VISION":
                if msg["data"].get("system_id") == 1:
                    print(">>> [S3] User lost during interaction — aborting!")
                    # Signal the sync thread to stop its next turn
                    self._interaction_abort.set()
                    user_lost = True
                    break  # Exit monitor loop immediately

        # ── Wait for the sync thread to finish (with a hard timeout) ─────────
        # FIX: never await an already-completed or non-aborted future blindly;
        # use asyncio.shield to prevent cancellation of the running executor task
        # and apply a timeout so we never block longer than INTERACTION_TIMEOUT.
        if not future.done():
            try:
                await asyncio.wait_for(asyncio.shield(future), timeout=self.INTERACTION_TIMEOUT)
            except asyncio.TimeoutError:
                print(f">>> [S3] Interaction thread did not exit within "
                      f"{self.INTERACTION_TIMEOUT}s — forcing transition anyway.")
        else:
            # Collect result/exception to avoid unhandled-exception warnings
            try:
                future.result()
            except Exception:
                pass

        # ── Transition back to State 1 ────────────────────────────────────────
        reason = "user lost" if user_lost else "conversation ended"
        print(f">>> [S3] Interaction finished ({reason}). Transition S3→S1")
        self.system_id    = 1
        self.mode         = "IDLE"
        self.avatar_state = "SLEEP"
        self.subtitle     = ""
        self.ad_url       = self.ad_selector.get_next_idle_ad()
        await self.broadcast_state()

    # ──────────────────────────────────────────────────────────────────────────
    #  Sync interaction runner (executed in thread pool)
    # ──────────────────────────────────────────────────────────────────────────
    def _run_interaction_sync(self, ad_url: str):
        """
        Wraps the blocking `start_interaction_loop`.

        - `is_active_callback` allows the interaction manager to check whether
          it should continue talking (returns False when abort is set OR
          system_id has already changed away from 3).
        - `state_callback` pushes in-progress avatar/subtitle updates to the
          frontend via the thread-safe sync_broadcast helper.
        """
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
#  SERVER LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("  ADORIX BACKEND — INITIALIZING")
    print("=" * 60 + "\n")

    # 1. Ad Selector
    rules_path = os.path.join(current_dir, "modules", "ad_engine", "rules.json")
    selector   = AdSelector(rules_path, ads_dir)
    manager.set_ad_selector(selector)

    # 2. State Machine (runs as a background asyncio task)
    asyncio.create_task(manager.run())

    # 3. Vision Thread (OpenCV — blocking, runs in a daemon thread)
    manager.vision_service = AdorixVision(
        broadcast_callback=manager.on_vision_update,
        selector=selector,
    )
    threading.Thread(target=manager.vision_service.start, daemon=True).start()

    # 4. Initial asset sync + periodic re-sync (every 10 min)
    from modules.storage import sync_ads
    threading.Thread(target=sync_ads, daemon=True).start()

    async def _periodic_sync():
        while True:
            await asyncio.sleep(600)
            await asyncio.to_thread(sync_ads)

    asyncio.create_task(_periodic_sync())

    yield

    # ── Cleanup on shutdown ──────────────────────────────────────────────────
    manager._stop_wake_word()
    print(">>> [System] Shutdown complete.")


# ═══════════════════════════════════════════════════════════════════════════════
#  FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════════
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


# ─── REST Endpoint ─────────────────────────────────────────────────────────────
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
    # Return all files in the ads directory that look like videos (.mp4, .webm, etc.)
    return [f for f in os.listdir(ads_dir) if f.lower().endswith(('.mp4', '.webm'))]


# ─── WebSocket Endpoint ────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    manager.clients.append(websocket)
    print(f">>> [WS] Client connected. Total: {len(manager.clients)}")

    try:
        # Immediately push current state so the frontend doesn't wait
        await websocket.send_text(json.dumps({
            "type":         "SYSTEM_UPDATE",
            "system_id":    manager.system_id,
            "mode":         manager.mode,
            "avatar_state": manager.avatar_state,
            "subtitle":     manager.subtitle,
            "ad_url":       manager.ad_url,
        }))

        # Receive loop — frontend sends control messages here
        while True:
            raw  = await websocket.receive_text()
            try:
                msg = json.loads(raw)
                msg_type = msg.get("type")

                if msg_type in ("AD_LOOP_TIMEOUT", "NEXT_AD", "AD_ENDED"):
                    # Frontend reports the ad finished
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