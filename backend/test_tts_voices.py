import pyttsx3
import time

def test_voices():
    # Initialize the TTS engine
    engine = pyttsx3.init()
    
    # Get all available voices on the system
    voices = engine.getProperty('voices')
    
    print(f"Total voices found: {len(voices)}\n")
    print("="*50)
    
    # Iterate through all voices and print their properties
    for index, voice in enumerate(voices):
        print(f"Voice Index: {index}")
        print(f" - ID: {voice.id}")
        print(f" - Name: {voice.name}")
        
        # Select the current voice
        engine.setProperty('voice', voice.id)
        
        # Test the voice
        test_phrase = f"Hello. This is voice index {index}. My name is {voice.name}."
        print(f">>> Speaking: '{test_phrase}'\n")
        
        engine.say(test_phrase)
        engine.runAndWait()
        
        # Short pause between voices
        time.sleep(1)
        
    print("="*50)
    print("Test complete.")
    print("To use a specific voice, open 'modules/interaction/tts_engine.py' and change:")
    print("    engine.setProperty('voice', voices[INDEX].id)")

if __name__ == "__main__":
    test_voices()
