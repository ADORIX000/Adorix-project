import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8003/ws"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            # Wait for 3 messages
            for _ in range(3):
                message = await websocket.recv()
                print(f"Received: {message}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
