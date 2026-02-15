import sys
import os

print("Python Executable:", sys.executable)
print("Python Version:", sys.version)
print("Current Path:", os.getcwd())
print("Sys Path:")
for p in sys.path:
    print(f"  {p}")

try:
    import cv2
    print("SUCCESS: cv2 imported from", cv2.__version__)
    print("cv2 file:", cv2.__file__)
except ImportError as e:
    print("FAILED: cv2 import failed with error:", e)

try:
    from modules.detection import AgeGenderDetector
    print("SUCCESS: modules.detection imported")
except ImportError as e:
    print("FAILED: modules.detection import failed with error:", e)
