"""
Adorix Transition Diagnostic Test (Personalized -> Interaction)
Tests the wake-word triggered state change from System ID 2 to System ID 3.
Test ID: system_id-002-to-003
"""
import os
import sys
import time
import threading

# Ensure backend/ root and modules are on path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'modules'))

from modules.wake_word.wakeword import WakeWordService

DIVIDER = "=" * 60

# 1. Mock System State
class MockState:
    def __init__(self):
        self.system_id = 2  # Start in Personalized Mode
        self.ad_url = "16-29_male.mp4"
        self.mode = "PERSONALIZED"
        self.avatar_state = "idle.webm"
        self.subtitle = ""
        self.lock = threading.Lock()

state = MockState()

def mock_sync_broadcast():
    print(f"\n[BROADCAST] System State Updated: ID={state.system_id}, Mode={state.mode}")

def mock_on_wake_word():
    """
    Simulates the actual logic from main.py:on_wake_word()
    """
    print("\n>>> [Callback] Wake Word detected by engine!")
    
    with state.lock:
        if state.system_id != 2:
            print(f">>> [Blocked] Transition denied. Current ID is {state.system_id}, not 2.")
            return
            
        print(">>> [State Machine] Transitioning: 2 (Personalized) -> 3 (Interaction)")
        state.system_id = 3
        state.mode = "INTERACTION"
        state.avatar_state = "wakeup.webm"
        state.subtitle = "Yes? I'm listening..."
        
    mock_sync_broadcast()
    print("\n[OK] Transition Test Passed! You are now in Interaction Mode.")
    print("[INFO] Press Ctrl+C to exit.")

def run_transition_test():
    print(f"\n{DIVIDER}")
    print("  ADORIX TRANSITION TEST (Personalized -> Interaction)")
    print("  Test ID: system_id-002-to-003")
    print(f"{DIVIDER}\n")

    print(f"Initial State: ID={state.system_id} (Personalized Mode)")
    print("Goal: Say 'Hey Adorix' to trigger transition to ID=3.")
    print("-" * 60)

    # Initialize Service
    try:
        service = WakeWordService(callback_function=mock_on_wake_word)
        if not service.spotter:
            print("[FAIL] Wake word engine (Sherpa-ONNX) failed to initialize.")
            return
            
        print("\n[LIVE] Wake Word Service is starting...")
        service.start()
        
    except KeyboardInterrupt:
        print("\n[INFO] Test stopped by user.")
    except Exception as e:
        print(f"\n[ERROR] Test execution failed: {e}")

if __name__ == "__main__":
    run_transition_test()
