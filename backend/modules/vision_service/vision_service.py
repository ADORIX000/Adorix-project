import cv2
import time
import json
import threading

# 1. SETUP OPENCV FACE DETECTION (Replacement for deprecated MediaPipe Legacy)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# 2. GLOBAL STATE
current_demographics = {"age": None, "gender": None}
last_analysis_time = 0
ANALYSIS_INTERVAL = 2.0 # Only check age every 2 seconds to save CPU

def analyze_face_worker(face_img):
    """Runs in background to guess Age/Gender without freezing video"""
    global current_demographics
    try:
        from deepface import DeepFace
        # DeepFace is accurate but slow (0.2s - 0.5s)
        # We use 'ssd' or 'opencv' backend for speed
        analysis = DeepFace.analyze(face_img, actions=['age', 'gender'], enforce_detection=False, detector_backend='opencv')
        current_demographics = {
            "age": analysis[0]['age'],
            "gender": analysis[0]['dominant_gender']
        }
        print(f"Update: {current_demographics}")
    except Exception as e:
        print(f"Analysis failed: {e}")

def start_vision_loop(websocket_manager):
    global last_analysis_time
    print("Starting vision loop...")
    
    # Try Camera index 0 first, then 1
    for index in [0, 1]:
        print(f"Attempting to open camera {index}...")
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            print(f"Camera {index} opened successfully.")
            break
        print(f"Failed to open camera {index}.")
    else:
        print("Error: Could not open any camera.")
        return
    
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        # 3. FAST DETECTION
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) > 0:
            # Face Found! 
            # Logic: If we haven't analyzed in 2 seconds, do it now.
            if time.time() - last_analysis_time > ANALYSIS_INTERVAL:
                # 1. Get bounding box coordinates
                # faces is a list of (x, y, w, h)
                (x, y, w_box, h_box) = faces[0]
                
                # 2. Crop the face
                face_crop = image[y:y+h_box, x:x+w_box]
                
                # 3. Start analysis in a thread (NON-BLOCKING)
                if face_crop.size > 0:
                    threading.Thread(target=analyze_face_worker, args=(face_crop,)).start()
                    last_analysis_time = time.time()

            # 4. SEND SIGNAL TO FRONTEND
            # Logic: Decide which ad ID to play based on current_demographics
            # (You will add your rules.json logic here)
            if current_demographics["gender"]:
                 # Example: Send "System ID 2" (Personalized)
                 websocket_manager.broadcast_sync({
                     "system_id": 2, 
                     "demographics": current_demographics
                 })
        else:
            # No Face = System ID 1 (Loop Mode)
            # Only send this if we were previously in mode 2 to avoid spamming
            websocket_manager.broadcast_sync({"system_id": 1})

        # Optional: Show preview window for debugging
        # cv2.imshow('Adorix Vision', image)
        # if cv2.waitKey(5) & 0xFF == 27:
        #     break

    cap.release()