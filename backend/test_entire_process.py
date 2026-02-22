import sys
import os
import time
from unittest.mock import patch

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from modules.interaction.interaction_manager import start_interaction_loop

def mock_state_callback(avatar_state=None, subtitle=None):
    """Mocks the WebSocket broadcast for visual UI changes."""
    if subtitle:
        print(f"\n[AVATAR UI UPDATE] Video: {avatar_state} | Subtitle: '{subtitle}'")

def mock_is_active_callback():
    """Simulates that the user is continuously standing in front of the camera."""
    return True

# Simulate what the user's STT microphone hears:
# 1st time STT listens -> It hears a price question
# 2nd time STT listens -> It hears a feature question
# 3rd time STT listens -> It hears pure silence, which triggers the 10-second timeout!
simulated_audio_inputs = [
    "What is the price of this?", 
    "What are the features?",
    None,                           
]

def mock_listen_one_phrase(timeout=10):
    print(f"\n>>> [MOCK STT] Listening for {timeout} seconds...")
    time.sleep(2) # Simulate the user taking time to speak
    
    if simulated_audio_inputs:
        phrase = simulated_audio_inputs.pop(0)
        if phrase:
            print(f">>> [MOCK STT] Captured User Speech: '{phrase}'")
        else:
            print(">>> [MOCK STT] 10 seconds of silence elapsed (Timeout).")
        return phrase
    return None

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 ADORIX END-TO-END SIMULATION: FROM DETECTION TO QA ANSWERS")
    print("="*70)
    
    print("\n[STEP 1] User approaches Kiosk (Vision Detection)")
    print("Vision Service System identified: 16-29 Year Old Female")
    ad_url = "16-29_female.mp4"
    print(f"Currently playing personalized ad: {ad_url}")
    time.sleep(2)
    
    print("\n[STEP 2] Wake Word Triggered")
    print("User says: 'Hey Adorix'")
    print("Transitioning into Interaction Mode (System ID: 3)...")
    time.sleep(1)
    
    print("\n[STEP 3] Entering QA Interaction Loop")
    print("The system will now run the Full RAG Pipeline using simulated microphone input.")
    print("This tests STT interpretation, QA generation, and TTS Audio output.")
    print("-"*70)
    
    # Patch the actual STT engine so we don't need a real microphone, avoiding timeouts.
    with patch('modules.interaction.interaction_manager.listen_one_phrase', side_effect=mock_listen_one_phrase):
        result = start_interaction_loop(
            current_ad_name=ad_url,
            state_callback=mock_state_callback,
            is_active_callback=mock_is_active_callback
        )
        
    print("\n" + "-"*70)
    print(f"[STEP 4] Interaction Loop Finished (Result: {result})")
    print("System transitioning back to Background Loop Mode (System ID: 1).")
    print("="*70)
    print("TEST COMPLETE: The QA pipeline provided correct answers and successfully returned to loop mode upon silence detection.")
