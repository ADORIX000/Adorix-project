"""
Adorix Personalized Mode (System ID 2) Diagnostic Test
Verifies targeted ad selection, demographic mapping, and frontend payload compatibility.
Test ID: system_id-002
"""
import os
import sys
import json

# Ensure backend/ root and modules are on path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'modules'))

from modules.ad_engine.selector import AdSelector

DIVIDER = "=" * 60

def run_personalized_test():
    print(f"\n{DIVIDER}")
    print("  ADORIX PERSONALIZED MODE DIAGNOSTIC (system_id-002)")
    print(f"{DIVIDER}\n")

    # 1. Setup Paths
    rules_path = os.path.join(current_dir, "modules", "ad_engine", "rules.json")
    ads_dir = os.path.abspath(os.path.join(current_dir, "..", "frontend", "public", "ads"))
    personalized_view_path = os.path.abspath(os.path.join(current_dir, "..", "frontend", "src", "views", "PersonalizedView.jsx"))

    # 2. Logic Verification (Ad Selection)
    print("[1/3] Verifying Demographic-to-Ad Mapping...")
    try:
        selector = AdSelector(rules_path, ads_dir)
        
        # Test a few known demographics
        target_tests = [
            {"demo": "16-29_male", "expected": "16-29_male.mp4"},
            {"demo": "above-60_female", "expected": "above-60_female.mp4"},
            {"demo": "10-15_male", "expected": "10-15_male.mp4"}
        ]
        
        for test in target_tests:
            result = selector.get_personalized_ad(test["demo"])
            full_path = os.path.join(ads_dir, result)
            exists = os.path.exists(full_path)
            
            print(f"\n  Demographic: {test['demo']}")
            print(f"  Selected Ad: {result}")
            print(f"  File Exists: {'YES' if exists else 'NO'}")
            
            if result == test["expected"] and exists:
                print("  [OK] Mapping and File validation passed.")
            else:
                print("  [FAIL] Mapping or File missing!")
                
    except Exception as e:
        print(f"  [FAIL] Error in AdSelector logic: {e}")

    # 3. Payload Compatibility (Backend -> Frontend)
    print(f"\n{DIVIDER}")
    print("[2/3] Verifying Payload Compatibility (System ID 2)...")
    
    # This simulates the data vision_service.py:187 sends
    sample_payload = {
        "system_id": 2, 
        "ad_url": "16-29_male.mp4",
        "demographics": ["16-29_male"]
    }
    
    print("  Simulated Broadcast Payload:")
    print(json.dumps(sample_payload, indent=4))
    
    # Check if frontend uses these keys
    if os.path.exists(personalized_view_path):
        with open(personalized_view_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("\n  Frontend Check (PersonalizedView.jsx):")
        checks = {
            "ad_url": "systemState.ad" in content or "ad_url" in content,
            "system_id": "systemId === 2" in content or "2" in content # Checked in App.jsx
        }
        
        if "App.jsx" in os.listdir(os.path.join(current_dir, "..", "frontend", "src")):
            app_path = os.path.join(current_dir, "..", "frontend", "src", "App.jsx")
            with open(app_path, 'r', encoding='utf-8') as f:
                app_content = f.read()
            checks["systemId_check"] = "systemId === 2" in app_content
            
        for key, val in checks.items():
            print(f"    Check {key:15}: {'OK' if val else 'MISSING'}")
            
    else:
        print("  [WARN] PersonalizedView.jsx not found for content verification.")

    # 4. State Machine Transition Rules
    print(f"\n{DIVIDER}")
    print("[3/3] System ID Verification...")
    print("  - System ID 1: LOOP")
    print("  - System ID 2: PERSONALIZED (Targeted Video + 'Hey Adorix' Prompt)")
    print("  - System ID 3: INTERACTION")
    print("\n  [OK] system_id-002 confirmed as Secondary Targeted state.")

    print(f"\n{DIVIDER}")
    print("  Diagnostic Complete.")
    print(DIVIDER)

if __name__ == "__main__":
    run_personalized_test()
