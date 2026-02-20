import json
import asyncio
import websockets
import sys

# Configuration
WS_URL = "ws://localhost:8001/ws"

class AdorixTestClient:
    def __init__(self):
        self.current_system_id = None
        self.current_mode = None
        self.current_ad = None

    async def monitor(self):
        print("====================================================")
        print("      Adorix Integration & Sync Test Tool")
        print("====================================================")
        
        try:
            async with websockets.connect(WS_URL) as websocket:
                print("### WebSocket Connected to Adorix Server ###")
                print("\nWaiting for state updates... Perform actions in front of camera now.")
                print("1. Stand in front of camera -> Should trigger STAGE: PERSONALIZED DELIVERY")
                print("2. Say 'Hey Adorix' -> Should trigger STAGE: INTERACTION MODE")
                print("3. Walk away -> Should trigger STAGE: LOOP MODE")
                print("\n(Press Ctrl+C to stop this test)")

                async for message in websocket:
                    data = json.loads(message)
                    
                    system_id = data.get("system_id")
                    mode = data.get("mode")
                    ad_url = data.get("ad_url")
                    
                    changed = False
                    if system_id != self.current_system_id:
                        print(f"\n[SYSTEM_ID] {self.current_system_id} -> {system_id}")
                        self.current_system_id = system_id
                        changed = True
                        
                    if mode != self.current_mode:
                        print(f"[MODE] {self.current_mode} -> {mode}")
                        self.current_mode = mode
                        changed = True

                    if ad_url != self.current_ad:
                        print(f"[AD] {self.current_ad} -> {ad_url}")
                        self.current_ad = ad_url
                        changed = True

                    if changed:
                        if system_id == 1:
                            print(">>> STAGE: 🔄 LOOP MODE (Searching for users...)")
                        elif system_id == 2:
                            print(f">>>> STAGE: ✨ PERSONALIZED DELIVERY (Ad: {ad_url})")
                        
                        if mode == "INTERACTION":
                            print(">>> STAGE: 🎙️ INTERACTION MODE (Wake Word Detected!)")

        except Exception as e:
            print(f"\n[ERROR] Could not connect: {e}")
            print("Please make sure 'python main.py' is running.")

if __name__ == "__main__":
    client = AdorixTestClient()
    try:
        asyncio.run(client.monitor())
    except KeyboardInterrupt:
        print("\nTest stopped by user.")
