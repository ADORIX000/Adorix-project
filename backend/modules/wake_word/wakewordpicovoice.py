import os
import time
import threading
import pvporcupine
from pvrecorder import PvRecorder
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

class WakeWordService:
    def __init__(self, callback_function=None):
        self.callback = callback_function
        self.access_key = os.environ.get("PICOVOICE_ACCESS_KEY")
        self.keyword_path = os.path.join(os.path.dirname(__file__), "models", "hey_adorix.ppn")
        self.porcupine = None
        self.recorder = None
        self.stop_requested = False

        if not self.access_key:
            print("[PICOWAKE] Error: PICOVOICE_ACCESS_KEY not found in .env")
            return

        try:
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keyword_paths=[self.keyword_path]
            )
            print(f"[PICOWAKE] Porcupine initialized with custom keyword: {os.path.basename(self.keyword_path)}")
        except Exception as e:
            print(f"[PICOWAKE] Error initializing Porcupine: {e}")

    def start(self):
        if not self.porcupine:
            print("[PICOWAKE] Cannot start: Porcupine not initialized.")
            return

        self.recorder = PvRecorder(
            frame_length=self.porcupine.frame_length,
            device_index=-1  # Use default device
        )
        self.recorder.start()

        print("[PICOWAKE] Listening for 'Hey Adorix'...")

        try:
            while not self.stop_requested:
                pcm = self.recorder.read()
                result = self.porcupine.process(pcm)

                if result >= 0:
                    print("\n[PICOWAKE] >>> WAKE WORD DETECTED! <<<")
                    if self.callback:
                        self.callback()
        except Exception as e:
            print(f"[PICOWAKE] Error in main loop: {e}")
        finally:
            self.stop()

    def stop(self):
        self.stop_requested = True
        if self.recorder:
            self.recorder.stop()
            self.recorder.delete()
            self.recorder = None
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None
        print("[PICOWAKE] Service stopped.")

if __name__ == "__main__":
    def on_wake():
        print("Heard you!")
    
    ww = WakeWordService(on_wake)
    try:
        ww.start()
    except KeyboardInterrupt:
        ww.stop()
