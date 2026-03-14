"""
Adorix Ad Selector Diagnostic Test
Tests the AdSelector logic: demographic mapping, fallback, and idle rotation.
Run from the backend/ directory:
    python test_ad_engine.py
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

def print_header(title):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)

def run_test():
    print_header("ADORIX AD SELECTOR DIAGNOSTIC")
    
    # 1. Paths Setup
    rules_path = os.path.join(current_dir, "modules", "ad_engine", "rules.json")
    ads_dir = os.path.abspath(os.path.join(current_dir, "..", "frontend", "public", "ads"))
    
    print(f"[INFO] Rules Path: {rules_path}")
    print(f"[INFO] Ads Directory: {ads_dir}")
    
    if not os.path.exists(rules_path):
        print(f"[FAIL] Rules file missing at {rules_path}")
        return
    if not os.path.exists(ads_dir):
        print(f"[FAIL] Ads directory missing at {ads_dir}")
        return

    # 2. Initialization
    print("\n[1/4] Initializing AdSelector...")
    try:
        selector = AdSelector(rules_path, ads_dir)
        print(f"[OK] AdSelector initialized with {len(selector.idle_ads)} available idle ads.")
    except Exception as e:
        print(f"[FAIL] Initialization error: {e}")
        return

    # 3. Test Demographic Mapping (get_personalized_ad)
    print("\n[2/4] Testing Demographic Mapping (get_personalized_ad)...")
    
    # Load all keys from rules.json to test everything
    with open(rules_path, "r", encoding="utf-8") as f:
        rules_data = json.load(f)
    
    # Filter for actual demographic mappings (Value should be a string, usually .mp4)
    demographic_keys = [
        k for k, v in rules_data.items() 
        if isinstance(v, str) and v.endswith(".mp4") and k not in ["IDLE", "DEFAULT"]
    ]
    
    test_cases = demographic_keys + ["invalid_key", None]
    
    for key in test_cases:
        ad = selector.get_personalized_ad(key)
        # Handle cases where get_personalized_ad returns a non-string (shouldn't happen with valid rules)
        if not isinstance(ad, str):
            print(f"  Input: {str(key):15} -> [ERROR] Result is {type(ad).__name__}: {ad}")
            continue
            
        exists = os.path.exists(os.path.join(ads_dir, ad))
        status = "[OK]" if exists else "[WARN - File Missing]"
        print(f"  Input: {str(key):15} -> Result: {ad:20} {status}")

    # 4. Test Idle Rotation (choose_ad_filename)
    print("\n[3/4] Testing Idle Rotation (choose_ad_filename)...")
    print("  Rotating through 5 cycles of IDLE...")
    
    # Simulate IDLE payload
    idle_payload = {"status": "IDLE"}
    
    history = []
    for i in range(5):
        # We pass advance_idle=True to force a new ad in the rotation
        ad = selector.choose_ad_filename(idle_payload, advance_idle=True)
        history.append(ad)
        print(f"  Cycle {i+1}: {ad}")
    
    if len(set(history)) > 1:
        print("  [OK] Idle rotation is working (different ads selected).")
    else:
        print("  [INFO] Idle rotation returned same ad (maybe only 1 file exists or shuffle is off).")

    # 5. Test Active Payload Mapping
    print("\n[4/4] Testing Active Payload Mapping...")
    active_payload = {
        "status": "ACTIVE",
        "primary": {
            "gender": "female",
            "age": "16-29"
        }
    }
    
    ad = selector.choose_ad_filename(active_payload)
    print(f"  Payload: Female, 16-29 -> Result: {ad}")
    if ad == "16-29_female.mp4":
        print("  [OK] Active payload mapping successful.")
    else:
        print("  [FAIL] Active payload mapping failed.")

    print(f"\n{DIVIDER}")
    print("  Diagnostic complete.")
    print(DIVIDER)

if __name__ == "__main__":
    run_test()
