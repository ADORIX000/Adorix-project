import pvporcupine
from pvrecorder import PvRecorder
import sys
import os

# Allow importing from the 'core' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.config import PICOVOICE_KEY, WAKE_WORD_PATH, AUDIO_DEVICE_INDEX

class WakeWordService:
    def __init__(self, callback_function):
        self.callback = callback_function
        self.is_listening = False

        # Security Check
        if not os.path.exists(WAKE_WORD_PATH):
            print(f"CRITICAL ERROR: Wake word file not found at: {WAKE_WORD_PATH}")
            print("Did you make sure the filename in config.py matches the file in backend/core/?")
            return

        try:
            self.porcupine = pvporcupine.create(
                access_key=PICOVOICE_KEY,
                keyword_paths=[WAKE_WORD_PATH]
            )
            self.recorder = PvRecorder(
                device_index=AUDIO_DEVICE_INDEX,
                frame_length=self.porcupine.frame_length
            )
            print(f">>> [WakeWord] Engine Initialized for Raspberry Pi")
        except Exception as e:
            print(f"Error initializing Wake Word: {e}")

    def start(self):
        if not hasattr(self, 'recorder'): return
        
        self.is_listening = True
        self.recorder.start()
        print(">>> [Backend] Listening for 'Hey Adorix'...")

        try:
            while self.is_listening:
                pcm = self.recorder.read()
                result = self.porcupine.process(pcm)

                if result >= 0:
                    print(">>> [Backend] WAKE WORD DETECTED!")
                    self.callback()
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            print(f"Error in listener: {e}")
        finally:
            self.stop()

    def stop(self):
        self.is_listening = False
        if hasattr(self, 'recorder'): self.recorder.stop()
        if hasattr(self, 'porcupine'): self.porcupine.delete()
        if hasattr(self, 'recorder'): self.recorder.delete()