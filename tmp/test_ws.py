import asyncio
import websockets
import json

async def test_transition():
    uri = "ws://localhost:8002/ws"
    async with websockets.connect(uri) as websocket:
        print("Connected to Adorix Backend")
        
        # 1. Send first AD_ENDED
        print("Sending 1st AD_ENDED...")
        await websocket.send(json.dumps({"type": "AD_ENDED"}))
        await asyncio.sleep(1)
        
        # 2. Send second AD_ENDED
        print("Sending 2nd AD_ENDED...")
        await websocket.send(json.dumps({"type": "AD_ENDED"}))
        await asyncio.sleep(1)
        
        print("Done.")

if __name__ == "__main__":
    asyncio.run(test_transition())
