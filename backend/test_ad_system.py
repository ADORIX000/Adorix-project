import os
import sys
import json

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Import Ad Selector
from modules.ad_engine.selector import AdSelector
from modules.interaction.brain_engine import adorix_brain

def test_ad_selector_and_context():
    print("\n--- Testing Ad Selector & Knowledge Loading (Real Data) ---")
    rules_path = os.path.join(backend_dir, "modules", "ad_engine", "rules.json")
    
    # Point to the actual ads mapping
    # Note: The backend expects ads in backend/ads if it's the static server, 
    # but the selector uses the path provided to it.
    ads_dir = os.path.join(os.path.dirname(backend_dir), "frontend", "public", "ads")
    
    print(f"Rules Path: {rules_path}")
    print(f"Ads Dir: {ads_dir}")

    if not os.path.exists(ads_dir):
        print(f"ERROR: Ads directory not found at {ads_dir}")
        return

    selector = AdSelector(rules_path, ads_dir)
    
    test_cases = [
        {"name": "IDLE State", "payload": {"status": "IDLE"}, "expected": "ANY_MP4"},
        {"name": "Male 16-29", "payload": {"status": "ACTIVE", "primary": {"gender": "Male", "age": "16-29"}}, "expected": "16-29_male.mp4"},
        {"name": "Female 16-29", "payload": {"status": "ACTIVE", "primary": {"gender": "Female", "age": "16-29"}}, "expected": "16-29_female.mp4"},
        {"name": "Female 30-39", "payload": {"status": "ACTIVE", "primary": {"gender": "Female", "age": "30-39"}}, "expected": "30-39_female.mp4"},
        {"name": "Default (Male 40+)", "payload": {"status": "ACTIVE", "primary": {"gender": "Male", "age": "40+"}}, "expected": "16-29_male.mp4"},
        {"name": "Female 10-15", "payload": {"status": "ACTIVE", "primary": {"gender": "Female", "age": "10-15"}}, "expected": "10-15_female.mp4"},
        {"name": "Male 10-15", "payload": {"status": "ACTIVE", "primary": {"gender": "Male", "age": "10-15"}}, "expected": "10-15_male.mp4"},
    ]
    
    passed = 0
    for tc in test_cases:
        result = selector.choose_ad_filename(tc["payload"])
        
        is_match = (result == tc["expected"]) or (tc["expected"] == "ANY_MP4" and result.endswith(".mp4"))
        status = "[PASS]" if is_match else "[FAIL]"
        print(f"{status} {tc['name']}: {result} (Expected: {tc['expected']})")

        # Verification: Check if brain_engine can load knowledge using this result (stripping .mp4)
        print(f"   -> Loading knowledge for: {result}...")
        context = adorix_brain.load_context_from_json(result)
        if context:
            print(f"      ✅ Knowledge context loaded.")
        else:
            print(f"      ❌ Knowledge context MISSING.")

        if is_match and context:
            passed += 1
    
    print(f"\nFinal Results: {passed}/{len(test_cases)} cases fully successful.")


if __name__ == "__main__":
    print("🚀 Adorix System Test Suite")
    test_ad_selector_and_context()
    
    print("\n💡 Tip: This test verifies that demographics map to the correct ads")
    print("   and that each ad has a corresponding knowledge JSON file.")
