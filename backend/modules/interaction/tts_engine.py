import pyttsx3
import threading

_engine_initialized = False

def _speak_thread(text):
    """
    Initializes pyttsx3 localized to this specific thread.
    This prevents Windows COM objects from getting locked out across
    various backend threads, which causes silent failures on the 2nd run.
    """
    global _engine_initialized
    try:
        # Explicitly import win32 components to ensure they are in memory
        import pythoncom
        import pywintypes
        pythoncom.CoInitialize() # Initialize COM for this thread
        
        engine = pyttsx3.init()
        # Set to a female voice if possible
        voices = engine.getProperty('voices')
        for v in voices:
            if "female" in v.name.lower() or "zira" in v.name.lower() or "hazel" in v.name.lower():
                engine.setProperty('voice', v.id)
                break
        else:
            # Fallback to Index 1 if search fails (usually female on Windows)
            if len(voices) > 1:
                engine.setProperty('voice', voices[1].id)
                
        engine.setProperty('rate', 160)
        engine.setProperty('volume', 1.0)
        engine.say(text)
        engine.runAndWait()
        _engine_initialized = True
    except ImportError as e:
        if "pywintypes" in str(e):
            print(f"!!! [TTS] Critical error: 'pywintypes' missing. Please ensure pypiwin32 is installed and post-install script run.")
        else:
            print(f"!!! [TTS] Import error during speech: {e}")
    except Exception as e:
        print(f"!!! [TTS] Error during speech: {e}")

def speak(text):
    if not text:
        return
    print(f">>> [TTS] Speaking: {text}")
    
    # Run the engine in its own isolated thread to prevent SAPI5 thread-lock
    t = threading.Thread(target=_speak_thread, args=(text,))
    t.start()
    # We must wait for the thread to finish speaking before returning,
    # otherwise the STT scanner will turn on and hear the computer's own voice!
    t.join()

if __name__ == "__main__":
    speak("Hello, this is a test of the Adorix text to speech engine.")
    speak("This is the second phrase, proving the thread-lock is fixed.")
