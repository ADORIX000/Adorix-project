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

# Add the backend and modules directories to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
modules_dir = os.path.join(current_dir, 'modules')
if modules_dir not in sys.path:
    sys.path.append(modules_dir)

ads_dir = os.path.join(current_dir, "ads")

# Local modules
from wake_word import WakeWordService
from interaction.interaction_manager import start_interaction_loop
from vision_service import AdorixVision
from modules.ad_engine.selector import AdSelector

# --- Async State Manager ---
class AdorixStateManager:
    def __init__(self):
        self.system_id = 1             # 1: Loop, 2: Personalized, 3: Interaction
        self.mode = "IDLE"             # IDLE, INTERACTION
        self.avatar_state = "HIDDEN"
        self.subtitle = ""
        self.ad_url = ""               # Current ad URL
        
        self.play_count = 0            # Tracking loops in State 2
        self.last_timeout_time = 0     # Cooldown for re-triggering State 2
        
        # Async synchronization
        self.command_queue = asyncio.Queue()
        self.wake_word_event = asyncio.Event()
        self.clients: List[WebSocket] = []
        self.main_loop = None
        
        self.ad_selector = None
        self.wake_word_service = None
        self.vision_service = None

    def set_ad_selector(self, selector):
        self.ad_selector = selector
        self.ad_url = selector.get_next_idle_ad()

    async def broadcast_state(self):
        payload = {
            "type": "SYSTEM_UPDATE",
            "system_id": self.system_id,
            "mode": self.mode,
            "avatar_state": self.avatar_state,
            "subtitle": self.subtitle,
            "ad_url": self.ad_url
        }
        state_payload = json.dumps(payload)
        if not self.clients: return
        
        tasks = [client.send_text(state_payload) for client in self.clients]
        await asyncio.gather(*tasks, return_exceptions=True)

    def sync_broadcast(self):
        """Safe call from threads."""
        if self.main_loop:
            asyncio.run_coroutine_threadsafe(self.broadcast_state(), self.main_loop)

    # --- External Event Handlers (Called from threads) ---
    def on_vision_update(self, data):
        """Vision thread pushes updates here."""
        asyncio.run_coroutine_threadsafe(
            self.command_queue.put({"type": "VISION", "data": data}), 
            self.main_loop
        )

    def on_wake_word(self):
        """Wake word thread signals here."""
        print("\n!!! [Async Manager] Wake Word Detected Signal !!!")
        self.main_loop.call_soon_threadsafe(self.wake_word_event.set)

    def on_ad_end(self):
        """Frontend signals ad finished."""
        asyncio.run_coroutine_threadsafe(
            self.command_queue.put({"type": "AD_ENDED"}), 
            self.main_loop
        )

    # --- State Machine Core ---
    async def run(self):
        self.main_loop = asyncio.get_running_loop()
        print(">>> [Async Manager] Orchestration Loop Started.")
        
        while True:
            # --- STATE 1: LOOP MODE ---
            if self.system_id == 1:
                await self.run_state_loop()
            
            # --- STATE 2: PERSONALIZED MODE ---
            elif self.system_id == 2:
                await self.run_state_personalized()
            
            # --- STATE 3: INTERACTION MODE ---
            elif self.system_id == 3:
                await self.run_state_interaction()
            
            await asyncio.sleep(0.1)

    async def run_state_loop(self):
        """Continuously loop through generic ads."""
        print(">>> [State Machine] Entering STATE 1: LOOP MODE")
        self.system_id = 1
        self.mode = "IDLE"
        self.avatar_state = "HIDDEN"
        if not self.ad_url:
            self.ad_url = self.ad_selector.get_next_idle_ad()
        await self.broadcast_state()

        while self.system_id == 1:
            try:
                # Wait for Vision activity or next ad request
                msg = await asyncio.wait_for(self.command_queue.get(), timeout=1.0)
                
                if msg["type"] == "VISION":
                    new_id = msg["data"].get("system_id")
                    ad_url = msg["data"].get("ad_url", "")
                    
                    if new_id == 2:
                        # Cooldown check
                        if time.time() - self.last_timeout_time < 10:
                            continue
                            
                        print(f">>> [State Machine] Transition 1 -> 2 (Target: {ad_url})")
                        self.system_id = 2
                        self.ad_url = ad_url
                        self.play_count = 0
                        return # Exit to main loop to switch state

                elif msg["type"] == "AD_ENDED":
                    self.ad_url = self.ad_selector.get_next_idle_ad()
                    print(f">>> [State Machine] Advancing Loop Ad: {self.ad_url}")
                    await self.broadcast_state()

            except asyncio.TimeoutError:
                continue

    async def run_state_personalized(self):
        """Play targeted ad up to 3 times, listen for wake word."""
        print(f">>> [State Machine] Entering STATE 2: PERSONALIZED MODE (Ad: {self.ad_url})")
        self.system_id = 2
        self.play_count = 0
        self.wake_word_event.clear()
        await self.broadcast_state()

        # Ensure wake word service is running
        self.restart_wake_word_service()

        while self.system_id == 2:
            # Two things can happen:
            # 1. Wake word detected (HIGH PRIORITY)
            # 2. Ad ends (Increment count, check limit)
            # 3. Vision lost user (Revert to 1)
            
            wake_task = asyncio.create_task(self.wake_word_event.wait())
            msg_task = asyncio.create_task(self.command_queue.get())
            
            done, pending = await asyncio.wait(
                [wake_task, msg_task], 
                return_when=asyncio.FIRST_COMPLETED,
                timeout=0.5
            )

            for task in pending:
                task.cancel()

            # Path A: Wake Word
            if wake_task in done:
                print(">>> [State Machine] Path A: Wake Word! Transition 2 -> 3")
                self.system_id = 3
                return

            # Other events
            if msg_task in done:
                msg = msg_task.result()
                if msg["type"] == "AD_ENDED":
                    self.play_count += 1
                    print(f">>> [State Machine] Ad Playback Count: {self.play_count}/3")
                    
                    if self.play_count >= 3:
                        print(">>> [State Machine] Path B: Max Plays Reached. Transition 2 -> 1")
                        self.system_id = 1
                        self.last_timeout_time = time.time()
                        return
                    else:
                        # Still playing the same personalized ad
                        await self.broadcast_state()

                elif msg["type"] == "VISION":
                    new_id = msg["data"].get("system_id")
                    if new_id == 1:
                        print(">>> [State Machine] User Lost. Transition 2 -> 1")
                        self.system_id = 1
                        return

            await asyncio.sleep(0.01)

    async def run_state_interaction(self):
        """Full Interaction Loop."""
        print(">>> [State Machine] Entering STATE 3: INTERACTION MODE")
        self.system_id = 3
        self.mode = "INTERACTION"
        self.avatar_state = "wakeup.webm"
        self.subtitle = "Yes? I'm listening..."
        await self.broadcast_state()

        # Stop wake word listener to free the MIC
        self.stop_wake_word_service()

        # Run interaction in a thread (since it's blocking/uses sync libs)
        current_ad = self.ad_url
        
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(None, self.handle_interaction_sync, current_ad)
        
        # While waiting for interaction to finish, still watch for VISION lost user
        while not future.done():
            try:
                msg = await asyncio.wait_for(self.command_queue.get(), timeout=0.5)
                if msg["type"] == "VISION":
                    if msg["data"].get("system_id") == 1:
                        print(">>> [State Machine] User Lost during interaction! Aborting.")
                        self.system_id = 1
                        # Note: The interaction thread has its own internal check (is_active_callback)
                        break
            except asyncio.TimeoutError:
                continue

        await future # Ensure thread finishes
        
        print(">>> [State Machine] Interaction Finished. Transition -> 1")
        self.system_id = 1
        self.mode = "IDLE"
        self.avatar_state = "SLEEP"
        self.subtitle = ""
        self.ad_url = self.ad_selector.get_next_idle_ad()
        await self.broadcast_state()
        
        # Restart wake word for next person
        self.restart_wake_word_service()

    def handle_interaction_sync(self, ad_url):
        """Sync wrapper for the interaction manager."""
        try:
            is_active = lambda: self.system_id == 3
            def interaction_cb(avatar_state=None, subtitle=None):
                if avatar_state: self.avatar_state = avatar_state
                if subtitle is not None: self.subtitle = subtitle
                self.sync_broadcast()

            start_interaction_loop(
                current_ad_name=ad_url,
                state_callback=interaction_cb,
                is_active_callback=is_active
            )
        except Exception as e:
            print(f"!!! [Interaction] Error: {e}")

    # --- Hardware Management ---
    def restart_wake_word_service(self):
        if self.wake_word_service:
            self.stop_wake_word_service()
        
        print(">>> [System] Starting Wake Word Service...")
        self.wake_word_service = WakeWordService(callback_function=self.on_wake_word)
        threading.Thread(target=self.wake_word_service.start, daemon=True).start()

    def stop_wake_word_service(self):
        if self.wake_word_service:
            print(">>> [System] Stopping Wake Word Service...")
            try: self.wake_word_service.stop()
            except: pass
            self.wake_word_service = None

# --- Global Manager ---
manager = AdorixStateManager()

# --- Server Lifecycle Integration ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*50)
    print("ADORIX ASYNC STATE MACHINE INITIALIZING")
    print("="*50)
    
    # 1. Initialize Ad Selector
    rules_path = os.path.join(current_dir, "modules", "ad_engine", "rules.json")
    selector = AdSelector(rules_path, ads_dir)
    manager.set_ad_selector(selector)
    
    # 2. Start Manager Core
    asyncio.create_task(manager.run())

    # 3. Start Vision Thread
    manager.vision_service = AdorixVision(broadcast_callback=manager.on_vision_update, selector=selector)
    threading.Thread(target=manager.vision_service.start, daemon=True).start()
    
    # 4. Initial Sync & Fallbacks
    from modules.storage import sync_ads
    threading.Thread(target=sync_ads, daemon=True).start()
    
    async def periodic_sync():
        while True:
            await asyncio.to_thread(sync_ads)
            await asyncio.sleep(600)
    asyncio.create_task(periodic_sync())

    yield
    
    # Cleanup
    manager.stop_wake_word_service()

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

@app.get("/api/status")
async def get_status():
    return {
        "system_id": manager.system_id,
        "mode": manager.mode,
        "ad_url": manager.ad_url
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    manager.clients.append(websocket)
    try:
        # Initial push
        await websocket.send_text(json.dumps({
            "type": "SYSTEM_UPDATE",
            "system_id": manager.system_id,
            "mode": manager.mode,
            "avatar_state": manager.avatar_state,
            "subtitle": manager.subtitle,
            "ad_url": manager.ad_url
        }))
        
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                # AD_LOOP_TIMEOUT from frontend
                if msg.get("type") == "AD_LOOP_TIMEOUT" or msg.get("type") == "NEXT_AD":
                    manager.on_ad_end()
            except Exception as e:
                print(f"!!! [WS] Error: {e}")
    except WebSocketDisconnect:
        manager.clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
    