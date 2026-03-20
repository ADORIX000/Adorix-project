import os
import sys
import speech_recognition as sr

# Add backend and modules to path
project_root = r"c:\Users\deegh\OneDrive\Desktop\DEE\GitHUB\Adorix-project"
backend_dir = os.path.join(project_root, "backend")
modules_dir = os.path.join(backend_dir, "modules")
sys.path.insert(0, backend_dir)
sys.path.insert(0, modules_dir)

def test_stt_init():
    print("=== Adorix STT Initialization Verification ===")
    try:
        recognizer = sr.Recognizer()
        print("Recognizer initialized.")
        
        # List all microphones to see if any are available
        mics = sr.Microphone.list_microphone_names()
        if not mics:
            print("ERROR: No microphones found on this system.")
            return False
        
        print(f"Found {len(mics)} microphones: {mics[:3]}...")
        
        # Try to open the default microphone
        with sr.Microphone() as source:
            print("Successfully opened the default microphone.")
            print("STT initialization successful.")
            return True
            
    except Exception as e:
        print(f"!!! [STT] Initialization Error: {e}")
        return False

if __name__ == "__main__":
    test_stt_init()
