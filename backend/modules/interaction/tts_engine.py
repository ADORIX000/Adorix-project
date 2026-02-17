import pyttsx3
import threading

class TTSEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TTSEngine, cls).__new__(cls)
                cls._instance._init_engine()
            return cls._instance

    def _init_engine(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 160)
            self.engine.setProperty('volume', 1.0)
            # Optional: Select a specific voice if available
            # voices = self.engine.getProperty('voices')
            # self.engine.setProperty('voice', voices[1].id) 
        except Exception as e:
            print(f"!!! [TTS] Error initializing engine: {e}")
            self.engine = None

    def speak(self, text):
        if not text:
            return
        print(f">>> [TTS] Speaking: {text}")
        if self.engine:
            try:
                # pyttsx3's runAndWait can be tricky if called from different threads
                # but usually works fine if initialized in the same thread or with locks
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"!!! [TTS] Error during speech: {e}")
                # Re-initialize on failure
                self._init_engine()
        else:
            print("!!! [TTS] Engine not available.")

# Global instance for easy access
tts_engine = TTSEngine()

def speak(text):
    tts_engine.speak(text)

if __name__ == "__main__":
    speak("Hello, this is a test of the Adorix text to speech engine.")
