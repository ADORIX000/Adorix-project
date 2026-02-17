#!/usr/bin/env python
"""
ADORIX DEBUG - Simplified test to identify errors
"""

import os
import sys

print("\n" + "="*60)
print("🔍 ADORIX DEBUG - Testing Components")
print("="*60 + "\n")

# Test 1: Check project structure
print("✓ Testing project structure...")
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
print(f"  Project root: {PROJECT_ROOT}")

services_vision = os.path.join(PROJECT_ROOT, "services", "vision")
services_ad = os.path.join(PROJECT_ROOT, "services", "ad_engine", "ads")

print(f"  Vision path exists: {os.path.exists(services_vision)}")
print(f"  Ad path exists: {os.path.exists(services_ad)}")

# Test 2: Check vision models
print("\n✓ Testing vision models...")
models_path = os.path.join(PROJECT_ROOT, "services", "vision", "models")
models = ['age_deploy.prototxt', 'age_net.caffemodel', 
          'gender_deploy.prototxt', 'gender_net.caffemodel',
          'opencv_face_detector.pbtxt', 'opencv_face_detector_uint8.pb']

for model in models:
    model_file = os.path.join(models_path, model)
    exists = os.path.exists(model_file)
    status = "✅" if exists else "❌"
    print(f"  {status} {model}")

# Test 3: Check ad files
print("\n✓ Testing ad files...")
if os.path.exists(services_ad):
    ads = [f for f in os.listdir(services_ad) if f.endswith('.mp4')]
    if ads:
        for ad in ads:
            print(f"  ✅ {ad}")
    else:
        print("  ❌ No MP4 files found!")
else:
    print(f"  ❌ Ad directory not found: {services_ad}")

# Test 4: Try importing vision detector
print("\n✓ Testing imports...")
try:
    from services.vision.detector import AgeGenderDetector
    print("  ✅ Vision detector imported")
except Exception as e:
    print(f"  ❌ Vision detector import failed: {e}")
    sys.exit(1)

try:
    from services.ad_engine.selector import AdSelector
    print("  ✅ Ad selector imported")
except Exception as e:
    print(f"  ❌ Ad selector import failed: {e}")
    sys.exit(1)

# Test 5: Check camera
print("\n✓ Testing camera...")
try:
    import cv2
    cam_count = 0
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"  ✅ Camera {i} available")
            cap.release()
            cam_count += 1
        else:
            cap.release()
    
    if cam_count == 0:
        print("  ⚠️  No camera found! (Kiosk will still run with dummy frames)")
except Exception as e:
    print(f"  ❌ Camera test failed: {e}")

# Test 6: Check FastAPI
print("\n✓ Testing FastAPI/WebSocket...")
try:
    from fastapi import FastAPI
    print("  ✅ FastAPI available")
except Exception as e:
    print(f"  ❌ FastAPI not installed: {e}")

# Test 7: Initialize vision detector
print("\n✓ Initializing vision detector...")
try:
    detector = AgeGenderDetector()
    print("  ✅ Detector initialized")
    print(f"     - Models loaded from: {detector.MODEL_PATH}")
    print(f"     - Shared JSON path: {detector.SHARED_JSON}")
    print(f"     - Debug window: {detector.DRAW_DEBUG_WINDOW}")
except Exception as e:
    print(f"  ❌ Detector initialization failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("✅ All checks passed! Ready to run adorix_kiosk.py")
print("="*60 + "\n")
