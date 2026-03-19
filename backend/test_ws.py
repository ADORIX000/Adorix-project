import asyncio
import websockets
import sys

async def test_ws():
    try:
        async with websockets.connect("ws://localhost:8002/ws") as websocket:
            print("Connected to WebSocket successfully!")
            await websocket.send('{"type": "TEST"}')
            response = await websocket.recv()
            print("Received:", response)
    except Exception as e:
        print("WebSocket Error:", e)

if __name__ == "__main__":
    asyncio.run(test_ws())
