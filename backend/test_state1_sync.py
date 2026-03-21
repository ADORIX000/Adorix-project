import os
import sys
import asyncio
import time

# Add the backend directory to the path so modules can be found
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Mock some dependencies if needed, but here we can just import the class
from main import AdorixStateManager

async def verify_state1_sync():
    print(">>> [Verification] Testing State 1 Synchronization Logic...")
    
    # 1. Initialize State Manager
    # Note: AdorixStateManager starts its own vision and wake word threads.
    mgr = AdorixStateManager()
    
    # Give it a moment to boot
    time.sleep(1)
    
    # Verify initial boot state
    print(f"Initial State: ID={mgr.system_id}, last_timeout_time={mgr.last_timeout_time}")
    assert mgr.system_id == 1
    assert mgr.last_timeout_time == 0.0 or mgr.last_timeout_time == 87.0 # 87.0 is from Selector init? No, let's see.
    # Actually in __init__ it's 0.0
    
    # 2. Simulate moving to State 2 and then State 3
    mgr.system_id = 3
    mgr.mode = "INTERACTIVE"
    mgr.detection_buffer = ["20-40_male", "20-40_male"] # Fake some stale data
    mgr.buffer_start_time = time.time() - 5
    
    print(f"Simulated State 3: ID={mgr.system_id}, Buffer Size={len(mgr.detection_buffer)}")
    
    # 3. Trigger transition to State 1
    print(">>> [Action] Triggering transition_to_loop()...")
    await mgr.transition_to_loop()
    
    # 4. Verify post-transition state
    print(f"Final State: ID={mgr.system_id}, last_timeout_time={mgr.last_timeout_time}")
    print(f"Final Buffer Size: {len(mgr.detection_buffer)}")
    
    # SUCCESS CRITERIA:
    # - system_id should be 1
    # - detection_buffer should be empty
    # - last_timeout_time should be 0.0
    
    assert mgr.system_id == 1, "Failed: system_id should be 1"
    assert len(mgr.detection_buffer) == 0, "Failed: detection_buffer should be empty"
    assert mgr.last_timeout_time == 0.0, "Failed: last_timeout_time should be 0.0"
    
    print("\n[OK] Verification Passed! State 1 is perfectly synchronized with boot behavior.")

if __name__ == "__main__":
    asyncio.run(verify_state1_sync())
