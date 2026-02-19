import mediapipe as mp
import os

path = os.path.dirname(mp.__file__)
print(f"Searching in: {path}")

for root, dirs, files in os.walk(path):
    for file in files:
        if "face_detection" in file or "solutions" in file:
            print(os.path.join(root, file))

print("Search complete.")
