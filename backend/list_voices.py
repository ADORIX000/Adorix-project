import pyttsx3
import pythoncom

def list_voices():
    try:
        pythoncom.CoInitialize()
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print(f"--- Available Voices: {len(voices)} ---")
        for index, voice in enumerate(voices):
            print(f"Index {index}:")
            print(f" - ID: {voice.id}")
            print(f" - Name: {voice.name}")
            print(f" - Gender: {getattr(voice, 'gender', 'Unknown')}")
            print(f" - Languages: {voice.languages}")
            print("-" * 20)
    except Exception as e:
        print(f"Error listing voices: {e}")

if __name__ == "__main__":
    list_voices()
