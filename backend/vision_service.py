import cv2
import threading
import time
import os
import numpy as np
from collections import Counter
from deepface import DeepFace # <-- The new AI engine
from modules.ad_engine.selector import AdSelector

class AdorixVision:
    def __init__(self, broadcast_callback, selector):
        self.broadcast = broadcast_callback
        self.selector = selector
        self.last_analysis = 0
        self.is_analyzing = False
        
        # --- BUFFER STATE VARIABLES ---
        self.detection_buffer = []      
        self.buffer_start_time = None   
        
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

        print("[VISION] Note: DeepFace models load automatically on first detection.")

    def detect_faces(self, frame):
        """Extracts bounding boxes using the fast SSD model."""
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123], False, False)
        self.face_net.setInput(blob)
        detections = self.face_net.forward()
        
        bboxes = []
        try:
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > 0.6: # High confidence only
                    raw_x1 = detections[0, 0, i, 3] * w
                    raw_y1 = detections[0, 0, i, 4] * h
                    raw_x2 = detections[0, 0, i, 5] * w
                    raw_y2 = detections[0, 0, i, 6] * h

                    if not all(np.isfinite([raw_x1, raw_y1, raw_x2, raw_y2])):
                        continue
                    
                    x1 = int(np.clip(raw_x1, 0, w - 1))
                    y1 = int(np.clip(raw_y1, 0, h - 1))
                    x2 = int(np.clip(raw_x2, 0, w - 1))
                    y2 = int(np.clip(raw_y2, 0, h - 1))
                    
                    if x2 > x1 and y2 > y1:
                        bboxes.append((x1, y1, x2, y2))
        except Exception as e:
            print(f"[ERROR] Logic error in detect_faces: {e}")
        return bboxes

    def map_deepface_data(self, raw_age, raw_gender):
        """Translates exact DeepFace output into Adorix buckets."""
        # DeepFace usually outputs 'Man' or 'Woman'. We standardize it to 'male' / 'female'.
        gender = "male" if "man" in raw_gender.lower() or "male" in raw_gender.lower() else "female"
        
        # Map exact integer age to your buckets
        if raw_age <= 15: age_group = "10-15"
        elif 16 <= raw_age <= 29: age_group = "16-29"
        elif 30 <= raw_age <= 39: age_group = "30-39"
        elif 40 <= raw_age <= 49: age_group = "40-49"
        elif 50 <= raw_age <= 59: age_group = "50-59"
        else: age_group = "above-60"
            
        return f"{age_group}_{gender}"

    def analyze(self, frame):
        """Background worker that processes the face using DeepFace."""
        try:
            self.is_analyzing = True
            bboxes = self.detect_faces(frame)
            
            if bboxes:
                for (x1, y1, x2, y2) in bboxes:
                    h, w = frame.shape[:2]
                    
                    # Add proportional padding so DeepFace sees the hair/chin
                    face_width = x2 - x1
                    face_height = y2 - y1
                    pad_w = int(face_width * 0.25)
                    pad_h = int(face_height * 0.25)
                    
                    py1 = max(0, y1 - pad_h)
                    py2 = min(h, y2 + pad_h)
                    px1 = max(0, x1 - pad_w)
                    px2 = min(w, x2 + pad_w)
                    
                    face_img = frame[py1:py2, px1:px2]
                    if face_img.size == 0: continue
                    
                    # ─── DEEPFACE MAGIC HAPPENS HERE ───
                    try:
                        # silent=True stops it from spamming the console
                        # enforce_detection=False because we already cropped the face
                        results = DeepFace.analyze(
                            img_path=face_img, 
                            actions=['age', 'gender'], 
                            enforce_detection=False,
                            silent=True 
                        )
                        
                        # DeepFace returns a list of dicts if multiple faces are found
                        res = results[0] if isinstance(results, list) else results
                        
                        raw_age = res['age']
                        raw_gender = res['dominant_gender']
                        
                        mapped = self.map_deepface_data(raw_age, raw_gender)
                        
                        self.detection_buffer.append(mapped)
                        print(f"[VISION-LIVE] DeepFace: {mapped} (Guessed: {raw_age} yrs, {raw_gender})")
                        
                    except Exception as df_err:
                        # DeepFace throws an error if the image is too blurry
                        pass 
                        
        except Exception as e:
            print(f"[ERROR] Analysis error: {e}")
        finally: 
            self.is_analyzing = False

    def start(self):
        """Main camera loop for continuous monitoring."""
        cap = None
        backends = [cv2.CAP_DSHOW, None]
        
        for index in [0, 1, 2]:
            for backend in backends:
                try:
                    cap = cv2.VideoCapture(index + backend) if backend else cv2.VideoCapture(index)
                    if cap.isOpened():
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        ret, test_frame = cap.read()
                        if ret: break
                        else: cap.release()
                except Exception: pass
            if cap and cap.isOpened(): break

        if not cap or not cap.isOpened():
            print("[ERROR] Could not open any webcam. Vision service will exit.")
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
                            self.detection_buffer = [] 
                            
                        # 2. COLLECT DATA (Fire thread continuously)
                        if not self.is_analyzing:
                            threading.Thread(target=self.analyze, args=(frame.copy(),), daemon=True).start()
                            
                        # 3. THE 2-SECOND EVALUATION
                        if time.time() - self.buffer_start_time >= 2.0:
                            if self.detection_buffer:
                                vote_counts = Counter(self.detection_buffer)
                                winning_demographic = vote_counts.most_common(1)[0][0]
                                
                                print(f"\n[ANALYSIS] 2-Sec Window Complete.")
                                print(f"[ANALYSIS] Votes: {dict(vote_counts)}")
                                print(f"[ANALYSIS] WINNER: {winning_demographic}")
                                
                                ad_name = self.selector.get_personalized_ad(winning_demographic)
                                
                                self.broadcast({
                                    "system_id": 2, 
                                    "ad_url": ad_name,
                                    "demographics": [winning_demographic], 
                                    "all_people": True 
                                })
                            
                            self.buffer_start_time = time.time()
                            self.detection_buffer = []
                    else:
                        self.buffer_start_time = None
                        self.detection_buffer = []
                        
                        if time.time() - self.last_analysis > 1.0:
                            self.broadcast({"system_id": 1})
                            self.last_analysis = time.time() 
                
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("[VISION] Stopping service...")
        except Exception as e:
            print(f"[ERROR] Vision loop error: {e}")
        finally:
            if cap: cap.release()
            cv2.destroyAllWindows()