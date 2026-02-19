import mediapipe as mp
import sys

print(f"Python version: {sys.version}")
print(f"Mediapipe version: {mp.__version__}")

try:
    print("Attempting to import mediapipe.solutions...")
    import mediapipe.solutions as solutions
    print("Successfully imported mediapipe.solutions")
    print(f"Solutions: {dir(solutions)}")
except Exception as e:
    print(f"Failed to import mediapipe.solutions: {e}")

try:
    print("Attempting to import mediapipe.solutions.face_detection...")
    from mediapipe.solutions import face_detection
    print("Successfully imported face_detection")
except Exception as e:
    print(f"Failed to import face_detection: {e}")
