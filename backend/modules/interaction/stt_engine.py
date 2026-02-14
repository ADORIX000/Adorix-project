import speech_recognition as sr

def listen_one_phrase(timeout=5):
    """
    Listens to the microphone and returns the recognized text.
    Returns None if no speech is detected or if an error occurs.
    """
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    try:
        with mic as source:
            print(f">>> [STT] Listening (timeout={timeout}s)...")
            # Adjust for background noise for better accuracy
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Listen for a single phrase
            audio = recognizer.listen(source, timeout=timeout)
            
        print(">>> [STT] Processing speech...")
        # Use Google's free Web Speech API (requires internet)
        text = recognizer.recognize_google(audio)
        return text
        
    except sr.WaitTimeoutError:
        print(">>> [STT] Silence detected (Timeout)")
        return None
    except sr.UnknownValueError:
        print(">>> [STT] Could not understand audio")
        return None
    except Exception as e:
        print(f"!!! [STT] Error: {e}")
        return None

if __name__ == "__main__":
    # Test common usage
    print("Testing STT... please speak something.")
    result = listen_one_phrase()
    if result:
        print(f"STT Result: {result}")
    else:
        print("STT failed to capture speech.")