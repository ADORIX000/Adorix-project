import cv2
import mediapipe as mp
import threading
import time
from deepface import DeepFace

class AdorixVision:
    def __init__(self, broadcast_callback):
        self.face_detector = mp.solutions.face_detection.FaceDetection(min_detection_confidence=0.5)
        self.broadcast = broadcast_callback
        self.last_analysis = 0
        self.is_analyzing = False

    def map_to_group(self, age, raw_gender):
        """
        Translates raw AI data into Adorix predefined format.
        Example: (24, "Woman") -> "16-29_female"
        """
        # 1. Normalize Gender
        gender = str(raw_gender).lower()
        if "man" in gender or "male" in gender:
            mapped_gender = "male"
        else:
            mapped_gender = "female"
            
        # 2. Bucket Age
        # Note: We catch anyone under 16 into the "10-15" bucket to prevent errors 
        # if a 9-year-old looks at the kiosk.
        if age < 16:
            age_group = "10-15"
        elif 16 <= age <= 29:
            age_group = "16-29"
        elif 30 <= age <= 39:
            age_group = "30-39"
        elif 40 <= age <= 49:
            age_group = "40-49"
        elif 50 <= age <= 59:
            age_group = "50-59"
        else:
            age_group = "above-60"
            
        # 3. Combine them into your exact required string
        return f"{age_group}_{mapped_gender}"

    def analyze(self, frame):
        try:
            self.is_analyzing = True
            
            # DeepFace analyzes the whole frame for multiple people
            results = DeepFace.analyze(
                img_path=frame, 
                actions=['age', 'gender'], 
                enforce_detection=False, 
                detector_backend='opencv'
            )
            
            if results:
                # Create a clean list to hold all detected formats
                demographics_list = []
                
                # Loop through every person found and map them
                for face in results:
                    mapped_string = self.map_to_group(
                        age=face.get('age'),
                        raw_gender=face.get('dominant_gender')
                    )
                    demographics_list.append(mapped_string)
                
                # Remove duplicates in case it detects two "16-29_male" users
                # This makes your ad selection logic much cleaner!
                unique_demographics = list(set(demographics_list))
                
                # Broadcast the JSON array to React
                # Output looks exactly like: ["16-29_male", "30-39_female"]
                data = {
                    "system_id": 2, 
                    "demographics": unique_demographics
                }
                self.broadcast(data)
                
        except Exception as e:
            print(f"Analysis error: {e}")
        finally: 
            self.is_analyzing = False

    def start(self):
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            # Fast trigger: Is anyone there?
            results = self.face_detector.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            if results.detections:
                # If people are detected, analyze them every 2 seconds
                if time.time() - self.last_analysis > 2.0 and not self.is_analyzing:
                    self.last_analysis = time.time()
                    threading.Thread(target=self.analyze, args=(frame,), daemon=True).start()
            else:
                # No one is in the frame -> Revert to generic Loop Mode
                self.broadcast({"system_id": 1})