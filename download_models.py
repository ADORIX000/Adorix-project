import urllib.request
import os

models_dir = "services/vision/models"
os.makedirs(models_dir, exist_ok=True)

# Model URLs from reliable sources
models = {
    # Face Detection (OpenCV SSD) - TensorFlow model
    "opencv_face_detector_uint8.pb": "https://raw.githubusercontent.com/spmallick/caffemodel-zoo/master/opencv_face_detector_uint8.pb",
    "opencv_face_detector.pbtxt": "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/opencv_face_detector.pbtxt",
    
    # Age Detection (Caffe)
    "age_net.caffemodel": "https://www.dropbox.com/s/1u3o3EGmSyQjqeFc/age_net.caffemodel?dl=1",
    "age_deploy.prototxt": "https://raw.githubusercontent.com/spmallick/caffemodel-zoo/master/age_deploy.prototxt",
    
    # Gender Detection (Caffe)
    "gender_net.caffemodel": "https://www.dropbox.com/s/cjuffo7kv4yrfrn/gender_net.caffemodel?dl=1",
    "gender_deploy.prototxt": "https://raw.githubusercontent.com/spmallick/caffemodel-zoo/master/gender_deploy.prototxt",
}

print("Downloading model files...")
for filename, url in models.items():
    filepath = os.path.join(models_dir, filename)
    
    if os.path.exists(filepath):
        print(f"✓ {filename} already exists")
        continue
    
    try:
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, filepath)
        file_size = os.path.getsize(filepath)
        print(f"✓ {filename} ({file_size:,} bytes)")
    except Exception as e:
        print(f"✗ Failed to download {filename}: {e}")

print("\nModel files ready!")

