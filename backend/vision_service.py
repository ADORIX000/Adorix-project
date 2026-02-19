import cv2
import threading
import time
import os
import numpy as np

class AdorixVision:
    def __init__(self, broadcast_callback):
        self.broadcast = broadcast_callback
        self.last_analysis = 0
        self.is_analyzing = False
        
        # Load Models (No TensorFlow or MediaPipe needed!)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(current_dir, "modules", "vision", "models")
        
        print(f"[VISION] Loading models from {model_dir}...")
        
        try:
            # Face Detection Model
            self.face_net = cv2.dnn.readNetFromTensorflow(
                os.path.join(model_dir, "opencv_face_detector_uint8.pb"),
                os.path.join(model_dir, "opencv_face_detector.pbtxt")
            )
            
            # Age/Gender Models
            self.age_net = cv2.dnn.readNet(
                os.path.join(model_dir, "age_net.caffemodel"),
                os.path.join(model_dir, "age_deploy.prototxt")
            )
            self.gender_net = cv2.dnn.readNet(
                os.path.join(model_dir, "gender_net.caffemodel"),
                os.path.join(model_dir, "gender_deploy.prototxt")
            )
            print("[VISION] Models loaded successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to load models: {e}")
            self.face_net = None
            self.age_net = None
            self.gender_net = None

        self.MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
        self.AGE_LIST = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
        self.GENDER_LIST = ['Male', 'Female']

    def map_to_group(self, age_idx, gender_pred):
        """
        Translates raw AI data into Adorix predefined format.
        """
        # 1. Gender
        gender = self.GENDER_LIST[gender_pred[0].argmax()].lower()
        
        # 2. Age Mapping
        # AGE_LIST = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
        # Index:       0        1        2         3          4          5          6          7
        
        # Simplified mapping logic for Adorix standard groups
        if age_idx <= 2: # 0-12
            age_group = "10-15"
        elif age_idx == 3: # 15-20
            age_group = "16-29"
        elif age_idx == 4: # 25-32
            age_group = "16-29"
        elif age_idx == 5: # 38-43
            age_group = "30-39"
        elif age_idx == 6: # 48-53
            age_group = "50-59"
        else: # 60+
            age_group = "above-60"
            
        return f"{age_group}_{gender}"

    def predict_age_gender(self, face_img):
        blob = cv2.dnn.blobFromImage(face_img, 1.0, (227, 227), self.MODEL_MEAN_VALUES, swapRB=False)
        
        self.gender_net.setInput(blob)
        gender_preds = self.gender_net.forward()
        
        self.age_net.setInput(blob)
        age_preds = self.age_net.forward()
        age_idx = age_preds[0].argmax()
        
        return age_idx, gender_preds

    def detect_faces(self, frame):
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123], False, False)
        self.face_net.setInput(blob)
        detections = self.face_net.forward()
        
        bboxes = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:
                x1 = int(detections[0, 0, i, 3] * w)
                y1 = int(detections[0, 0, i, 4] * h)
                x2 = int(detections[0, 0, i, 5] * w)
                y2 = int(detections[0, 0, i, 6] * h)
                bboxes.append((max(0, x1), max(0, y1), min(w, x2), min(h, y2)))
        return bboxes

    def analyze(self, frame):
        try:
            self.is_analyzing = True
            
            # Since we pass in a fresh frame copy, we re-detect faces here
            # Or pass the bbox. Let's re-detect for clean thread logic.
            bboxes = self.detect_faces(frame)
            
            demographics_list = []
            
            if bboxes:
                for (x1, y1, x2, y2) in bboxes:
                    h, w = frame.shape[:2]
                    
                    # Padding
                    padding = 20
                    py1 = max(0, y1 - padding)
                    py2 = min(h, y2 + padding)
                    px1 = max(0, x1 - padding)
                    px2 = min(w, x2 + padding)
                    
                    face_img = frame[py1:py2, px1:px2]
                    if face_img.size == 0: continue
                    
                    if self.age_net and self.gender_net:
                        age_idx, gender_preds = self.predict_age_gender(face_img)
                        mapped = self.map_to_group(age_idx, gender_preds)
                        demographics_list.append(mapped)
                
                if demographics_list:
                    unique = list(set(demographics_list))
                    data = {
                        "system_id": 2, 
                        "demographics": unique
                    }
                    self.broadcast(data)
                
        except Exception as e:
            print(f"[ERROR] Analysis error: {e}")
        finally: 
            self.is_analyzing = False

    def start(self):
        print("[VISION] Starting camera capture...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("[ERROR] Could not open webcam.")
            return

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print("[WARNING] Frame read failed. Exiting...")
                    break
                
                # Fast trigger: Is anyone there?
                if self.face_net:
                    bboxes = self.detect_faces(frame)
                    
                    if bboxes:
                        # If people are detected, analyze them every 2 seconds
                        if time.time() - self.last_analysis > 2.0 and not self.is_analyzing:
                            self.last_analysis = time.time()
                            # Use a copy of the frame for thread safety
                            threading.Thread(target=self.analyze, args=(frame.copy(),), daemon=True).start()
                    else:
                        # No one is in the frame -> Revert to generic Loop Mode
                        # Rate limit this to avoid spamming the socket every 30ms
                        if time.time() - self.last_analysis > 1.0:
                            self.broadcast({"system_id": 1})
                            self.last_analysis = time.time() # Reset timer to avoid spam
                
                # Optional: Sleep slightly to reduce CPU usage if needed
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("[VISION] Stopping service...")
        except Exception as e:
            print(f"[ERROR] Vision loop error: {e}")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("[VISION] Camera released.")