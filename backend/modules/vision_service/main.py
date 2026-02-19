from fastapi import FastAPI, WebSocket
from vision_service import start_vision_loop
import threading
import asyncio
import uvicorn

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.loop = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.loop = asyncio.get_event_loop()
        print(f"New connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Connection closed. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Broadcast error: {e}")

    def broadcast_sync(self, message: dict):
        """Thread-safe synchronous broadcast wrapper"""
        if self.loop and self.active_connections:
            asyncio.run_coroutine_threadsafe(self.broadcast(message), self.loop)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    # Start the Vision Loop in a separate thread so FastAPI stays responsive
    print("Starting vision loop thread...")
    vision_thread = threading.Thread(target=start_vision_loop, args=(manager,))
    vision_thread.daemon = True # Kills thread when server stops
    vision_thread.start()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep connection alive
    except:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)