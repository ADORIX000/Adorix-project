import os
import sys

# Add backend and modules to path
project_root = r"c:\Users\deegh\OneDrive\Desktop\DEE\GitHUB\Adorix-project"
backend_dir = os.path.join(project_root, "backend")
modules_dir = os.path.join(backend_dir, "modules")
sys.path.insert(0, backend_dir)
sys.path.insert(0, modules_dir)

from modules.interaction.tts_engine import speak

def test_tts():
    print("=== Adorix TTS Verification ===")
    text = "Hello! I'm Adorix. I'm testing the voice system right now. Can you hear me?"
    print(f"Speaking: '{text}'")
    speak(text)
    print("TTS test completed.")
    print("================================")

if __name__ == "__main__":
    test_tts()
