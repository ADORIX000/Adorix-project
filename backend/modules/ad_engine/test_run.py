import os
import json
import sys

# Add the parent directory to sys.path to allow importing selector
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from selector import AdSelector

def run_test():
    print("🚀 Starting Ad Engine Test Run...")
    
    # Paths
    rules_path = os.path.join(current_dir, "rules.json")
    ads_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "ads") # backend/ads
    
    if not os.path.exists(ads_dir):
        print(f"⚠️ Warning: Ads directory not found at {ads_dir}. Creating it for testing.")
        os.makedirs(ads_dir, exist_ok=True)
        # Create some dummy ad files
        for ad in ["puppy_ad.mp4", "furniture_ad.mp4", "makeup_ad.mp4", "gaming_ad.mp4", "phone_ad.mp4"]:
            with open(os.path.join(ads_dir, ad), "w") as f:
                f.write("dummy")

    # Initialize Selector
    selector = AdSelector(rules_path, ads_dir)
    
    # Test Cases
    test_cases = [
        {"name": "IDLE State", "payload": {"status": "IDLE"}, "expected": "puppy_ad.mp4"},
        {"name": "Male 16-29", "payload": {"status": "ACTIVE", "primary": {"gender": "Male", "age": "16-29"}}, "expected": "gaming_ad.mp4"},
        {"name": "Female 16-29", "payload": {"status": "ACTIVE", "primary": {"gender": "Female", "age": "16-29"}}, "expected": "makeup_ad.mp4"},
        {"name": "Female 30-39", "payload": {"status": "ACTIVE", "primary": {"gender": "Female", "age": "30-39"}}, "expected": "phone_ad.mp4"},
        {"name": "Unknown Person (Default)", "payload": {"status": "ACTIVE", "primary": {"gender": "Unknown", "age": "Unknown"}}, "expected": "furniture_ad.mp4"},
    ]
    
    passed = 0
    for tc in test_cases:
        result = selector.choose_ad_filename(tc["payload"])
        if result == tc["expected"]:
            print(f"✅ {tc['name']}: Matched {result}")
            passed += 1
        else:
            print(f"❌ {tc['name']}: Expected {tc['expected']}, got {result}")
            
    print(f"\n📊 Test Summary: {passed}/{len(test_cases)} cases passed.")

if __name__ == "__main__":
    run_test()
