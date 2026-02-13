from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import threading
import time
import sys
import os

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












# Import the service
from modules.wake_word import WakeWordService

def on_wake_word_detected():
    """
    This function triggers when the Pi hears the wake word.
    """
    print("\n------------------------------------------------")
    print(">>> TRIGGER: 'Hey Adorix' Detected on Raspberry Pi!")
    print(">>> Action: Waking up Avatar...")
    print("------------------------------------------------\n")
    # TODO: Add logic here to turn on the screen or start recording

    def start_backend():
    print(">>> [System] Starting Adorix Backend on Raspberry Pi...")

    # Initialize Service
    service = WakeWordService(callback_function=on_wake_word_detected)

    # Run in background thread
    t = threading.Thread(target=service.start)
    t.daemon = True
    t.start()

    # Keep Main Program Alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        service.stop()

if __name__ == "__main__":
    start_backend()