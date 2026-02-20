import os
import cv2
import time
import json
import numpy as np
from collections import Counter, deque

from .camera import Camera


class AgeGenderDetector:
    """
    Vision service:
    - tracks ALL faces with IDs
    - commits only after DWELL_SECONDS
    - exports committed people to: ADORIX_PROJECT/shared/current_users.json
    """

    def __init__(self):
        # detector.py is in backend/modules/vision/
        current_module_dir = os.path.dirname(os.path.abspath(__file__))
        # Project root is 4 levels up from this file
        self.PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

        self.MODEL_PATH = os.path.join(current_module_dir, "models") + os.sep
        self.SHARED_DIR = os.path.join(self.PROJECT_ROOT, "shared")
        self.SHARED_JSON = os.path.join(self.SHARED_DIR, "current_users.json")
        os.makedirs(self.SHARED_DIR, exist_ok=True)

        # Raspberry Pi performance knobs
        self.SKIP_FRAMES = 10
        self.DETECT_WIDTH = 320
        self.MAX_TRACKS = 4
        self.PER_TRACK_INFER_EVERY = 3
        self.EXPORT_EVERY_FRAMES = 20

        # Dwell gating
        self.DWELL_SECONDS = 3.0
        self.TRACK_TIMEOUT = 2.0
        self.MATCH_DISTANCE = 90

        # Smoothing
        self.SAMPLES_WINDOW = 20
        self.MIN_SAMPLES_FOR_STABLE = 8

        # UI (for debug window)
        self.DRAW_DEBUG_WINDOW = True
        self.LABEL_BG_COLOR = (180, 255, 180)  # soft green
        self.LABEL_TEXT_COLOR = (0, 0, 0)

        print("[INFO] Loading models...")
        self.face_net = cv2.dnn.readNet(
            self.MODEL_PATH + "opencv_face_detector_uint8.pb",
            self.MODEL_PATH + "opencv_face_detector.pbtxt"
        )
        self.age_net = cv2.dnn.readNet(
            self.MODEL_PATH + "age_net.caffemodel",
            self.MODEL_PATH + "age_deploy.prototxt"
        )
        self.gender_net = cv2.dnn.readNet(
            self.MODEL_PATH + "gender_net.caffemodel",
            self.MODEL_PATH + "gender_deploy.prototxt"
        )

        self.MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
        self.GENDER_LIST = ["Male", "Female"]
        self.AGE_MAP = {
            0: "Under 10", 1: "10-15", 2: "16-29", 3: "30-39",
            4: "40-49", 5: "50-59", 6: "60+", 7: "60+"
        }

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
    def _detect_faces_small(self, small_bgr, conf_threshold=0.7):
        h, w = small_bgr.shape[:2]
        blob = cv2.dnn.blobFromImage(
            small_bgr, 1.0, (300, 300), [104, 117, 123], swapRB=False, crop=False
        )
        self.face_net.setInput(blob)
        detections = self.face_net.forward()

        bboxes = []
        for i in range(detections.shape[2]):
            conf = float(detections[0, 0, i, 2])
            if conf >= conf_threshold:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                x1, y1, x2, y2 = box.astype("int")
                x1 = max(0, min(x1, w - 1))
                y1 = max(0, min(y1, h - 1))
                x2 = max(0, min(x2, w - 1))
                y2 = max(0, min(y2, h - 1))
                if x2 > x1 and y2 > y1:
                    bboxes.append((x1, y1, x2, y2))

        bboxes.sort(key=self._bbox_area, reverse=True)
        return bboxes

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
                    "age_idx_samples": deque(maxlen=self.SAMPLES_WINDOW),
                    "infer_counter": 0,
                    "stable": None
                }
                used.add(tid)
                results.append((tid, bbox))

        return results

    # ---------- inference ----------
    def _predict_age_gender(self, face_img_bgr):
        blob = cv2.dnn.blobFromImage(face_img_bgr, 1.0, (227, 227), self.MODEL_MEAN_VALUES, swapRB=False)

        self.gender_net.setInput(blob)
        gender_preds = self.gender_net.forward()
        gender = self.GENDER_LIST[int(gender_preds[0].argmax())]

        self.age_net.setInput(blob)
        age_preds = self.age_net.forward()
        age_idx = int(age_preds[0].argmax())

        return gender, age_idx

    @staticmethod
    def _smoothed_age_idx(age_idx_samples: deque):
        if not age_idx_samples:
            return None
        arr = np.array(list(age_idx_samples), dtype=np.int32)
        return int(np.median(arr))

    def _update_track_samples(self, tid, gender, age_idx):
        t = self.tracks[tid]
        t["gender_samples"].append(gender)
        t["age_idx_samples"].append(age_idx)

        if len(t["gender_samples"]) >= self.MIN_SAMPLES_FOR_STABLE and len(t["age_idx_samples"]) >= self.MIN_SAMPLES_FOR_STABLE:
            final_gender = Counter(t["gender_samples"]).most_common(1)[0][0]
            smooth_idx = self._smoothed_age_idx(t["age_idx_samples"])
            final_age = self.AGE_MAP.get(smooth_idx, "Unknown")
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

            if t["stable"]:
                g = t["stable"]["gender"]
                a = t["stable"]["age"]
            else:
                g = Counter(t["gender_samples"]).most_common(1)[0][0] if t["gender_samples"] else "..."
                s_idx = self._smoothed_age_idx(t["age_idx_samples"])
                a = self.AGE_MAP.get(s_idx, "...") if s_idx is not None else "..."

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
