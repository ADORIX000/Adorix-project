import cv2
import threading
import time
import os
import numpy as np
from collections import Counter # <-- NEW: For calculating the majority vote

class AdorixVision:
    def __init__(self, broadcast_callback):
        self.broadcast = broadcast_callback
        self.last_analysis = 0
        self.is_analyzing = False
        
        # --- NEW: BUFFER STATE VARIABLES ---
        self.detection_buffer = []      # Holds all predictions made in the 2-second window
        self.buffer_start_time = None   # Tracks when the timer started
        
        # Load Models
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
        self.AGE_LIST = ['(10-15)', '(16-29)', '(30-39)', '(40-49)', '(50-59)', '(60-100)']
        self.GENDER_LIST = ['Male', 'Female']

    def map_to_group(self, age_idx, gender_pred):
        """Translates raw AI data into Adorix predefined format."""
        gender = self.GENDER_LIST[gender_pred[0].argmax()].lower()
        
        if age_idx <= 2: age_group = "10-15"
        elif age_idx == 3: age_group = "16-29"
        elif age_idx == 4: age_group = "16-29"
        elif age_idx == 5: age_group = "30-39"
        elif age_idx == 6: age_group = "50-59"
        else: age_group = "above-60"
            
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
        """Background worker: Now it only adds to the buffer, it doesn't broadcast."""
        try:
            self.is_analyzing = True
            bboxes = self.detect_faces(frame)
            demographics_list = []
            
            if bboxes:
                for (x1, y1, x2, y2) in bboxes:
                    h, w = frame.shape[:2]
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
                    # Strip duplicates from THIS specific frame and add to the global list
                    unique_in_frame = list(set(demographics_list))
                    self.detection_buffer.extend(unique_in_frame)
                    
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
                if not ret: break
                
                if self.face_net:
                    bboxes = self.detect_faces(frame)
                    
                    if bboxes:
                        # 1. START THE CLOCK
                        if self.buffer_start_time is None:
                            self.buffer_start_time = time.time()
                            self.detection_buffer = [] # Start fresh
                            
                        # 2. COLLECT DATA (Fire thread continuously without blocking)
                        if not self.is_analyzing:
                            threading.Thread(target=self.analyze, args=(frame.copy(),), daemon=True).start()
                            
                        # 3. THE 2-SECOND EVALUATION
                        if time.time() - self.buffer_start_time >= 2.0:
                            if self.detection_buffer:
                                # Count the list and get the #1 most frequent value
                                most_common_tuple = Counter(self.detection_buffer).most_common(1)
                                winning_demographic = most_common_tuple[0][0]
                                
                                print(f"\n[WINNER] 2-Sec Analysis complete: {winning_demographic}")
                                
                                # Broadcast the winner to React
                                self.broadcast({
                                    "system_id": 2, 
                                    "demographics": [winning_demographic]
                                })
                            
                            # Reset the clock so it continues to evaluate every 2 seconds
                            # while they stand in front of the kiosk.
                            self.buffer_start_time = time.time()
                            self.detection_buffer = []
                    else:
                        # No one is in the frame -> Wipe the buffer
                        self.buffer_start_time = None
                        self.detection_buffer = []
                        
                        # Revert to generic Loop Mode (Rate limited)
                        if time.time() - self.last_analysis > 1.0:
                            self.broadcast({"system_id": 1})
                            self.last_analysis = time.time() 
                
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("[VISION] Stopping service...")
        except Exception as e:
            print(f"[ERROR] Vision loop error: {e}")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("[VISION] Camera released.")