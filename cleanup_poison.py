import shutil
import os
import sys

# Offending paths
paths_to_clean = [
    r"C:\Users\deegh\AppData\Roaming\Python\Python310\site-packages\google\protobuf",
    r"C:\Users\deegh\AppData\Roaming\Python\Python310\site-packages\google", # Clean the whole namespace just in case
    r"C:\Users\deegh\AppData\Roaming\Python\Python310\site-packages\tensorflow",
    r"C:\Users\deegh\AppData\Roaming\Python\Python310\site-packages\deepface"
]

for path in paths_to_clean:
    if os.path.exists(path):
        print(f"Removing {path}...")
        try:
            shutil.rmtree(path)
            print("Successfully removed.")
        except Exception as e:
            print(f"Failed to remove {path}: {e}")
    else:
        print(f"Path {path} does not exist.")
