from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio

app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "Backend is running"}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    print("WebSocket client connected")

    actions = [
        {"action": "wake"},
        {"action": "talk"},
        {"action": "play_sport_ad"},
        {"action": "play_fashion_ad"},
        {"action": "idle"}
    ]

    index = 0

    while True:
        await ws.send_text(json.dumps(actions[index]))
        index = (index + 1) % len(actions)
        await asyncio.sleep(4)