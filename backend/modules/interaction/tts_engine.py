import pyttsx3
import threading

def _speak_thread(text):
    """
    Initializes pyttsx3 localized to this specific thread.
    This prevents Windows COM objects from getting locked out across
    various backend threads, which causes silent failures on the 2nd run.
    """
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[1].id)
        engine.setProperty('rate', 160)
        engine.setProperty('volume', 1.0)
        engine.say(text)
        engine.runAndWait()
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
