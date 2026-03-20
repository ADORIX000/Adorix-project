import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://127.0.0.1:8001/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            # Wait for initial update
            msg = await websocket.recv()
            print(f"Received: {msg}")
            data = json.loads(msg)
            if data.get("type") == "SYSTEM_UPDATE":
                print("SUCCESS: Received SYSTEM_UPDATE")
            else:
                print(f"FAILED: Unexpected message type {data.get('type')}")
    except Exception as e:
        print(f"FAILED: Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
