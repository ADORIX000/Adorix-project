import os
import sys
import time

# Add backend and modules to path
project_root = os.path.dirname(os.path.abspath(__file__))
backend_dir = project_root
modules_dir = os.path.join(backend_dir, "modules")
sys.path.insert(0, backend_dir)
sys.path.insert(0, modules_dir)

from modules.interaction.interaction_manager import start_interaction_loop

def mock_state_callback(**kwargs):
    """Prints state updates that would normally go to the frontend."""
    print(f"\n[FRONTEND UI UPDATE] {kwargs}")

def mock_is_active():
    """Simulates the system being active."""
    return True

def run_debug_state3():
    print("==================================================")
    print(" DEBUG TOOL: INTERACTION MODE (STATE 3)")
    print("==================================================")
    print("This script simulates the full State 3 flow.")
    print("1. Animation (wakeup.webm)")
    print("2. Greeting (TTS)")
    print("3. Product Listing Display")
    print("4. Conversational Q&A (STT -> Brain -> TTS)")
    print("--------------------------------------------------\n")

    # Simulate a specific ad context (e.g., 30-39_male)
    test_ad_name = "30-39_male.mp4"
    
    print(f">>> Simulating transition for ad: {test_ad_name}")
    print(">>> (Wait 2.5s for wakeup animation...)\n")

    try:
        # Start the interaction loop in isolation
        result = start_interaction_loop(
            current_ad_name=test_ad_name,
            state_callback=mock_state_callback,
            is_active_callback=mock_is_active
        )
        
        print(f"\n>>> Interaction Finished. Result: {result}")
        
    except KeyboardInterrupt:
        print("\n>>> Debug session interrupted by user.")
    except Exception as e:
        print(f"\n!!! CRITICAL DEBUG ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_debug_state3()
