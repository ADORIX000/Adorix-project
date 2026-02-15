# core_controller/main.py
import os
import time
import json
import cv2
import numpy as np
from collections import Counter

from services.vision.detector import AgeGenderDetector
from services.ad_engine.selector import AdSelector
from .state_manager import StateManager


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED_JSON = os.path.join(PROJECT_ROOT, "shared", "current_users.json")

RULES_PATH = os.path.join(PROJECT_ROOT, "services", "ad_engine", "rules.json")
ADS_DIR = os.path.join(PROJECT_ROOT, "services", "ad_engine", "ads")


def load_payload():
    try:
        with open(SHARED_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"status": "IDLE", "primary": None, "people": []}


def reset_shared_json():
    os.makedirs(os.path.dirname(SHARED_JSON), exist_ok=True)
    payload = {"status": "IDLE", "primary": None, "people": []}
    tmp = SHARED_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    os.replace(tmp, SHARED_JSON)


def draw_tracks_on_frame(detector: AgeGenderDetector, frame):
    """
    Draw bounding boxes + labels (ID, gender, age range) on the camera preview.
    Uses detector.tracks which are updated by detector.update().
    """
    if frame is None:
        return frame

    LABEL_BG_COLOR = (180, 255, 180)  # soft green (BGR)
    LABEL_TEXT_COLOR = (0, 0, 0)

    def smoothed_age_idx(samples):
        if not samples:
            return None
        arr = np.array(list(samples), dtype=np.int32)
        return int(np.median(arr))

    now_ts = time.time()

    # draw biggest faces first (nice UX)
    items = sorted(detector.tracks.items(),
                   key=lambda kv: detector._bbox_area(kv[1]["bbox"]),
                   reverse=True)

    for tid, t in items:
        x1, y1, x2, y2 = t["bbox"]

        # bbox rectangle
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)

        # dwell timer
        dwell = now_ts - t["first_seen"]
        remaining = max(0.0, detector.DWELL_SECONDS - dwell)

        # gender/age (stable if available)
        if t.get("stable") is not None:
            g = t["stable"]["gender"]
            a = t["stable"]["age"]
        else:
            g = Counter(t["gender_samples"]).most_common(1)[0][0] if t["gender_samples"] else "..."
            s_idx = smoothed_age_idx(t["age_idx_samples"])
            a = detector.AGE_MAP.get(s_idx, "...") if s_idx is not None else "..."

        committed = (dwell >= detector.DWELL_SECONDS and t.get("stable") is not None)
        label = f"ID:{tid}  {g}  {a}" if committed else f"ID:{tid}  {g}  {a}  (wait {remaining:.1f}s)"

        # label bg + text (solid bg for speed)
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.55
        thickness = 2
        (tw, th), baseline = cv2.getTextSize(label, font, scale, thickness)

        rect_top = y1 - th - baseline - 12
        text_y = y1 - 8
        if rect_top < 0:
            rect_top = y1 + 4
            text_y = y1 + th + 4

        rect_left = x1
        rect_right = x1 + tw + 10
        rect_bottom = rect_top + th + baseline + 8

        cv2.rectangle(frame, (rect_left, rect_top), (rect_right, rect_bottom), LABEL_BG_COLOR, -1)
        cv2.putText(frame, label, (x1 + 5, text_y), font, scale, LABEL_TEXT_COLOR, thickness, cv2.LINE_AA)

    return frame


def play_step(cap, window_name):
    """
    Reads one frame from cap and shows it. 
    Returns False if video ends, so the main loop can pick the next ad.
    """
    ret, frame = cap.read()
    if not (ret and frame is not None):
        return False
        
    cv2.imshow(window_name, frame)
    return True


def main():
    # Always start IDLE
    reset_shared_json()

    # Start vision detector
    detector = AgeGenderDetector().start(index=0, width=640, height=480)

    # Ad selector
    selector = AdSelector(RULES_PATH, ADS_DIR)
    sm = StateManager()

    WIN_TITLE = "ADORIX AD PLAYER"
    cv2.namedWindow(WIN_TITLE, cv2.WINDOW_NORMAL)

    current_ad = None
    cap = None
    advance_rotation = False

    print("[INFO] Kiosk running 3-state mode with SEQUENTIAL PLAYLIST.")
    print("[INFO] - All ads in the folder will cycle during IDLE state.")
    print("[INFO] Press 'q' to quit.")

    try:
        while True:
            # 1. Update vision
            frame = detector.update()
            payload = load_payload()
            sm.update(payload)

            status = payload.get("status")       # ACTIVE (5s+) or IDLE
            presence = payload.get("presence", False)  # Someone in frame

            # 2. State Logic
            show_camera = False
            chosen = None

            if status == "ACTIVE":
                chosen = selector.choose_ad_filename(payload)
            elif presence:
                show_camera = True
            else:
                chosen = selector.choose_ad_filename(payload, advance_idle=advance_rotation)
                advance_rotation = False

            # 3. Handle Playback
            if show_camera:
                if cap:
                    cap.release()
                    cap = None
                    current_ad = None
                
                if frame is not None:
                    frame = draw_tracks_on_frame(detector, frame)
                    msg = "IDENTIFYING... PLEASE WAIT 3 SECONDS"
                    cv2.putText(frame, msg, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.imshow(WIN_TITLE, frame)
            else:
                if chosen != current_ad or cap is None:
                    if cap:
                        cap.release()
                    current_ad = chosen
                    path = selector.ad_path(current_ad)
                    cap = cv2.VideoCapture(path)
                    if not cap.isOpened():
                        print(f"❌ Error opening {path}")
                        time.sleep(1)
                        continue
                    print(f"[STATE={sm.state}] ▶ Playing: {current_ad}")

                success = play_step(cap, WIN_TITLE)
                if not success:
                    advance_rotation = True
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            time.sleep(0.01)

    finally:
        if cap:
            cap.release()
        detector.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
