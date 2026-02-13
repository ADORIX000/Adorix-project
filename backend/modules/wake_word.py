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