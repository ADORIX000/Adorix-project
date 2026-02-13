import speech_recognition as sr

recognizer = sr.Recognizer()

def listen_one_phrase(timeout=10):
    """
    Listens for a single phrase. 
    Returns the text if successful, or None if silence/error.
    timeout: How long to wait for the user to START speaking.
    """
    try:
        with sr.Microphone() as source:
            print(" Listening...")
            # Adjust for ambient noise (important for malls)
            recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # Listen (Wait 'timeout' seconds for speech to start)
            # phrase_time_limit=10 means stop listening if they talk for >10s
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            print(" Processing audio...")
            # Convert audio to text (Using Google Web Speech API - requires internet)
            # For offline, you would use Vosk here.
            text = recognizer.recognize_google(audio)
            print(f" USER: {text}")
            return text.lower()

    except sr.WaitTimeoutError:
        print("❌ No speech detected (Timeout)")
        return None
    except sr.UnknownValueError:
        print("❌ Could not understand audio")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# --- TEST CODE ---
if __name__ == "__main__":
    print("Say something in the next 5 seconds...")
    result = listen_one_phrase(10)
    if result:
        print("Success!")
    else:
        print("Failed or Silence.")