import cv2
import threading
import time
import os
import numpy as np
from deepface import DeepFace

class AdorixVision:
    def __init__(self, broadcast_callback, selector):
        self.broadcast = broadcast_callback
        self.selector = selector
        self.is_analyzing = False
        self.last_result = None  # Store the latest successful detection for main.py to poll
        
        # Load the lightning-fast OpenCV Face Detector
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(current_dir, "modules", "vision", "models")
        
        print(f"[VISION] Loading OpenCV SSD Face Detector...")
        try:
            self.face_net = cv2.dnn.readNetFromTensorflow(
                os.path.join(model_dir, "opencv_face_detector_uint8.pb"),
                os.path.join(model_dir, "opencv_face_detector.pbtxt")
            )
            print("[VISION] Face Detector loaded successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to load Face Detector: {e}")
            self.face_net = None

    def detect_faces(self, frame):
        """Extracts bounding boxes using the fast SSD model."""
        if not self.face_net: return []
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123], False, False)
        self.face_net.setInput(blob)
        detections = self.face_net.forward()
        
        bboxes = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.6: 
                x1 = int(detections[0, 0, i, 3] * w)
                y1 = int(detections[0, 0, i, 4] * h)
                x2 = int(detections[0, 0, i, 5] * w)
                y2 = int(detections[0, 0, i, 6] * h)
                bboxes.append((x1, y1, x2, y2))
        return bboxes

    def map_deepface_data(self, age, gender):
        """Translates DeepFace output into Adorix keys."""
        female_terms = ["Woman", "female", "woman"]
        g_str = "female" if gender in female_terms else "male"
        
        if age < 20:   a_str = "under-20"
        elif age < 40: a_str = "20-40"
        elif age < 60: a_str = "40-60"
        else:          a_str = "above-60"
        
        return f"{a_str}_{g_str}"

    def analyze(self, frame):
        """Starts a background thread to process the face using DeepFace."""
        if self.is_analyzing: return
        
        bboxes = self.detect_faces(frame)
        if not bboxes: return

        self.is_analyzing = True
        threading.Thread(target=self._deepface_worker, args=(frame, bboxes[0]), daemon=True).start()

    def _deepface_worker(self, frame, bbox):
        """Background worker thread."""
        try:
            x1, y1, x2, y2 = bbox
            h, w = frame.shape[:2]
            # Crop with padding
            px1, py1 = max(0, x1-20), max(0, y1-20)
            px2, py2 = min(w, x2+20), min(h, y2+20)
            face_img = frame[py1:py2, px1:px2]
            
            if face_img.size > 0:
                results = DeepFace.analyze(face_img, actions=['age', 'gender'], enforce_detection=False, silent=True)
                res = results[0] if isinstance(results, list) else results
                mapped = self.map_deepface_data(res['age'], res['dominant_gender'])
                
                self.last_result = mapped
                print(f"[VISION-LIVE] DeepFace: {mapped} (Guessed: {res['age']} yrs, {res['dominant_gender']})")
        except Exception as e:
            pass
        finally:
            self.is_analyzing = False

    def get_latest_result(self):
        """Poll for the most recent detection result."""
        res = self.last_result
        self.last_result = None
        return res