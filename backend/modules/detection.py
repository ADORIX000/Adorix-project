import os
import cv2
import time
import json
import numpy as np
from collections import Counter, deque
from deepface import DeepFace

from .camera import Camera


class AgeGenderDetector:
    """
    Vision service using DeepFace:
    - tracks ALL faces with IDs
    - commits only after DWELL_SECONDS
    - exports committed people to: ADORIX_PROJECT/shared/current_users.json
    """

    def __init__(self):
        # Project root = two levels up from services/vision/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.PROJECT_ROOT = base_dir

        self.SHARED_DIR = os.path.join(self.PROJECT_ROOT, "shared")
        self.SHARED_JSON = os.path.join(self.SHARED_DIR, "current_users.json")
        os.makedirs(self.SHARED_DIR, exist_ok=True)

        # Raspberry Pi performance knobs (Adjusted for DeepFace)
        self.SKIP_FRAMES = 15  # DeepFace is heavier, skip more frames
        self.DETECT_WIDTH = 320
        self.MAX_TRACKS = 2    # Reduce max tracks for performance
        self.PER_TRACK_INFER_EVERY = 2
        self.EXPORT_EVERY_FRAMES = 20

        # Dwell gating
        self.DWELL_SECONDS = 3.0 # Feel more responsive
        self.TRACK_TIMEOUT = 2.0
        self.MATCH_DISTANCE = 90

        # Smoothing
        self.SAMPLES_WINDOW = 15
        self.MIN_SAMPLES_FOR_STABLE = 5

        # UI (for debug window)
        self.DRAW_DEBUG_WINDOW = False
        self.LABEL_BG_COLOR = (180, 255, 180)  # soft green
        self.LABEL_TEXT_COLOR = (0, 0, 0)

        print("[INFO] Initializing DeepFace models...")
        # We don't pre-load explicitly here, DeepFace will handle it on first run
        
        self.frame_count = 0
        self.next_track_id = 1
        self.tracks = {}

        self._fps_t = time.time()
        self._fps_count = 0
        self._fps = 0

        self.cam = None

    # ---------- utils ----------
    @staticmethod
    def _bbox_area(b):
        x1, y1, x2, y2 = b
        return max(0, x2 - x1) * max(0, y2 - y1)

    @staticmethod
    def _bbox_center(b):
        x1, y1, x2, y2 = b
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    def _update_fps(self):
        self._fps_count += 1
        if time.time() - self._fps_t >= 1.0:
            self._fps = self._fps_count
            self._fps_count = 0
            self._fps_t = time.time()

    # ---------- camera lifecycle ----------
    def start(self, index=0, width=640, height=480):
        self.cam = Camera(index, width=width, height=height).start()
        return self

    def stop(self):
        if self.cam:
            self.cam.stop()

    # ---------- face detection ----------
    def _detect_faces_small(self, small_bgr):
        """
        Uses DeepFace (with opencv backend) for detection.
        Returns a list of (x1, y1, x2, y2)
        """
        try:
            # detector_backend can be 'opencv', 'retinaface', 'mtcnn', 'yolov8', etc.
            # 'opencv' is fastest for RPi contexts.
            faces = DeepFace.extract_faces(
                img_path=small_bgr, 
                detector_backend='opencv', 
                enforce_detection=False,
                align=False
            )
            
            bboxes = []
            for face in faces:
                # face['confidence'] check
                if face['confidence'] > 0.7:
                    r = face['facial_area']
                    # r is {x, y, w, h}
                    bboxes.append((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h']))
            
            bboxes.sort(key=self._bbox_area, reverse=True)
            return bboxes
        except Exception as e:
            print(f"[ERROR] Face extraction failed: {e}")
            return []

    # ---------- tracking ----------
    def _cleanup_tracks(self, now_ts):
        dead = [tid for tid, t in self.tracks.items() if (now_ts - t["last_seen"]) > self.TRACK_TIMEOUT]
        for tid in dead:
            del self.tracks[tid]

    def _match_or_create_tracks(self, detected_bboxes, now_ts):
        self._cleanup_tracks(now_ts)
        detected_bboxes = detected_bboxes[: self.MAX_TRACKS]

        results = []
        used = set()

        for bbox in detected_bboxes:
            cx, cy = self._bbox_center(bbox)

            best_id = None
            best_dist = float("inf")

            for tid, t in self.tracks.items():
                if tid in used:
                    continue
                tx, ty = t["center"]
                dist = ((cx - tx) ** 2 + (cy - ty) ** 2) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best_id = tid

            if best_id is not None and best_dist <= self.MATCH_DISTANCE:
                tr = self.tracks[best_id]
                tr["bbox"] = bbox
                tr["center"] = (cx, cy)
                tr["last_seen"] = now_ts
                used.add(best_id)
                results.append((best_id, bbox))
            else:
                tid = self.next_track_id
                self.next_track_id += 1
                self.tracks[tid] = {
                    "bbox": bbox,
                    "center": (cx, cy),
                    "first_seen": now_ts,
                    "last_seen": now_ts,
                    "gender_samples": deque(maxlen=self.SAMPLES_WINDOW),
                    "age_samples": deque(maxlen=self.SAMPLES_WINDOW),
                    "infer_counter": 0,
                    "stable": None
                }
                used.add(tid)
                results.append((tid, bbox))

        return results

    # ---------- inference ----------
    def _predict_age_gender(self, face_img_bgr):
        """
        DeepFace analysis for age and gender.
        """
        try:
            results = DeepFace.analyze(
                img_path=face_img_bgr, 
                actions=['age', 'gender'],
                enforce_detection=False,
                silent=True
            )
            if results:
                res = results[0]
                gender = res['dominant_gender']
                age = int(res['age'])
                return gender, age
        except Exception as e:
            pass # Analysis might fail on poor crops
        
        return None, None

    def _update_track_samples(self, tid, gender, age):
        if gender is None or age is None:
            return
            
        t = self.tracks[tid]
        t["gender_samples"].append(gender)
        t["age_samples"].append(age)

        if len(t["gender_samples"]) >= self.MIN_SAMPLES_FOR_STABLE:
            final_gender = Counter(t["gender_samples"]).most_common(1)[0][0]
            final_age = int(np.median(list(t["age_samples"])))
            
            # Group age into readable ranges for the dashboard if needed
            # Or just keep it as a number
            t["stable"] = {"id": tid, "gender": final_gender, "age": final_age}

    # ---------- public output ----------
    def get_committed_people(self, now_ts):
        committed = []
        sorted_tracks = sorted(self.tracks.items(), key=lambda kv: self._bbox_area(kv[1]["bbox"]), reverse=True)
        for tid, t in sorted_tracks:
            dwell = now_ts - t["first_seen"]
            if dwell >= self.DWELL_SECONDS and t["stable"] is not None:
                committed.append(t["stable"])
        return committed

    def export_for_logic_engine(self, now_ts):
        people = self.get_committed_people(now_ts)
        payload = {
            "status": "ACTIVE" if people else "IDLE",
            "presence": len(self.tracks) > 0,
            "primary": people[0] if people else None,
            "people": people
        }

        tmp = self.SHARED_JSON + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        os.replace(tmp, self.SHARED_JSON)

    # ---------- update (one step) ----------
    def update(self):
        frame = self.cam.read() if self.cam else None
        if frame is None:
            return None

        self.frame_count += 1
        self._update_fps()
        now_ts = time.time()

        run_ai = (self.frame_count % self.SKIP_FRAMES == 0)

        if run_ai:
            h, w = frame.shape[:2]
            scale = self.DETECT_WIDTH / float(w)
            small = cv2.resize(frame, (self.DETECT_WIDTH, int(h * scale)))

            detected_small = self._detect_faces_small(small)
            inv = 1.0 / scale
            detected = [(int(x1 * inv), int(y1 * inv), int(x2 * inv), int(y2 * inv)) for (x1, y1, x2, y2) in detected_small]

            matched = self._match_or_create_tracks(detected, now_ts)

            padding = 14
            for tid, bbox in matched:
                t = self.tracks.get(tid)
                if not t:
                    continue

                t["infer_counter"] += 1
                if (t["infer_counter"] % self.PER_TRACK_INFER_EVERY) != 0:
                    continue

                x1, y1, x2, y2 = bbox
                face_img = frame[
                    max(0, y1 - padding):min(y2 + padding, frame.shape[0] - 1),
                    max(0, x1 - padding):min(x2 + padding, frame.shape[1] - 1),
                ]
                if face_img.size == 0:
                    continue

                gender, age_idx = self._predict_age_gender(face_img)
                self._update_track_samples(tid, gender, age_idx)
        else:
            self._cleanup_tracks(now_ts)

        if self.frame_count % self.EXPORT_EVERY_FRAMES == 0:
            self.export_for_logic_engine(now_ts)

        # optional debug window
        if self.DRAW_DEBUG_WINDOW:
            self._draw_debug(frame, now_ts)

        return frame

    def _draw_debug(self, frame, now_ts):
        # draw tracks
        for tid, t in self.tracks.items():
            x1, y1, x2, y2 = t["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)

            dwell = now_ts - t["first_seen"]
            remaining = max(0.0, self.DWELL_SECONDS - dwell)

    def _draw_debug(self, frame, now_ts):
        # draw tracks
        for tid, t in self.tracks.items():
            x1, y1, x2, y2 = t["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)

            dwell = now_ts - t["first_seen"]
            remaining = max(0.0, self.DWELL_SECONDS - dwell)

            if t["stable"]:
                g = t["stable"]["gender"]
                a = t["stable"]["age"]
            else:
                g = Counter(t["gender_samples"]).most_common(1)[0][0] if t["gender_samples"] else "..."
                a = int(np.median(list(t["age_samples"]))) if t["age_samples"] else "..."

            committed = (dwell >= self.DWELL_SECONDS and t["stable"] is not None)
            label = f"ID:{tid} {g} {a}" if committed else f"ID:{tid} {g} {a} (wait {remaining:.1f}s)"

            self._draw_label(frame, x1, y1, label)

        committed_people = self.get_committed_people(now_ts)
        cv2.putText(frame, f"Tracked: {len(self.tracks)}  Committed: {len(committed_people)}  FPS:{self._fps}",
                    (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

        cv2.imshow("VISION DEBUG", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            raise SystemExit

    def _draw_label(self, frame, x1, y1, text):
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.55
        thickness = 2
        (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)

        rect_top = y1 - th - baseline - 12
        text_y = y1 - 8
        if rect_top < 0:
            rect_top = y1 + 4
            text_y = y1 + th + 4

        rect_left = x1
        rect_right = x1 + tw + 10
        rect_bottom = rect_top + th + baseline + 8

        cv2.rectangle(frame, (rect_left, rect_top), (rect_right, rect_bottom), self.LABEL_BG_COLOR, -1)
        cv2.putText(frame, text, (x1 + 5, text_y), font, scale, self.LABEL_TEXT_COLOR, thickness, cv2.LINE_AA)
