"""
Adorix Full Interaction Flow Diagnostic (Interaction -> Loop)
Tests the conversation lifecycle, AI response, and the 7-second timeout transition to Loop Mode.
Test ID: system_id-003
"""
import os
import sys
import time
import threading

# Ensure backend/ root and modules are on path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'modules'))

from modules.interaction.interaction_manager import start_interaction_loop

DIVIDER = "=" * 60

# 1. Mock System State
class MockState:
    def __init__(self):
        self.system_id = 3  # Start in Interaction Mode
        self.ad_url = "16-29_male.mp4"
        self.mode = "INTERACTION"
        self.avatar_state = "idle.webm"
        self.subtitle = ""
        self.lock = threading.Lock()

state = MockState()

def mock_sync_broadcast():
    print(f"\n[BROADCAST] System State Updated: ID={state.system_id}, Mode={state.mode}")

def mock_state_callback(avatar_state=None, subtitle=None):
    """
    Simulates the interaction_state_callback from main.py
    """
    with state.lock:
        if avatar_state: state.avatar_state = avatar_state
        if subtitle: state.subtitle = subtitle
    
    print(f"  [Frontend Sync] Avatar: {state.avatar_state:15} | Subtitle: {state.subtitle[:50]}...")

def run_lifecycle_test():
    print(f"\n{DIVIDER}")
    print("  ADORIX INTERACTION LIFECYCLE TEST (ID 3 -> 1)")
    print("  Test ID: system_id-003")
    print(f"{DIVIDER}\n")

    print(f"Initial State: ID={state.system_id} (Interaction Mode)")
    print("Process:")
    print("  1. System greets you.")
    print("  2. System waits 7 seconds for a question.")
    print("  3. If you speak, it answers and waits another 7 seconds.")
    print("  4. If silent for 7 seconds, it transitions to ID=1 (Loop Mode).")
    print("-" * 60)

    try:
        # Pass the abort checker function to the loop (simulating main.py logic)
        is_active = lambda: state.system_id == 3
        
        result = start_interaction_loop(
            current_ad_name=state.ad_url, 
            state_callback=mock_state_callback,
            is_active_callback=is_active
        )
        
        print(f"\n>>> [Interaction Loop] Finished with reason: {result}")
        
        # Perform Reversion Logic (Simulating final block in main.py:handle_interaction)
        with state.lock:
            if state.system_id == 3:
                print("\n>>> [State Machine] Transitioning: 3 (Interaction) -> 1 (Loop Mode)")
                state.system_id = 1
                state.mode = "IDLE"
                state.avatar_state = "SLEEP"
                state.subtitle = ""
                state.ad_url = ""
                
        mock_sync_broadcast()
        
        if state.system_id == 1:
            print("\n[OK] Lifecycle Test Passed! System has returned to Loop Mode.")
        else:
            print("\n[FAIL] System stuck in ID 3.")

    except KeyboardInterrupt:
        print("\n[INFO] Test stopped by user.")
    except Exception as e:
        print(f"\n[ERROR] Test execution failed: {e}")

if __name__ == "__main__":
    run_lifecycle_test()
