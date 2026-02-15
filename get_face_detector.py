import urllib.request
import ssl
import os

# Disable SSL verification for this download
ssl_context = ssl._create_unverified_context()

url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/opencv_face_detector_uint8.pb"
filepath = "services/vision/models/opencv_face_detector_uint8.pb"

try:
    print(f"Downloading from {url}...")
    urllib.request.urlopen(url, context=ssl_context)
    print("✓ Downloaded successfully")
except Exception as e:
    print(f"Failed: {e}")
    print("Note: Face detection model could not be downloaded.")
    print("The age/gender detection models are available.")
