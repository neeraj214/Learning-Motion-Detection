import cv2
import numpy as np
import datetime
import requests
import threading
import time

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
CAMERA_INDEX       = 0          # 0 = default webcam
FRAME_WIDTH        = 640
FRAME_HEIGHT       = 480
GAUSSIAN_BLUR_SIZE = (21, 21)   # must be odd
MIN_CONTOUR_AREA   = 1500       # pixels²  – smaller blobs are ignored
LOG_FILE           = "motion_log.txt"
FLASK_STATUS_URL   = "http://127.0.0.1:5000/motion_status_update"  # internal endpoint
FLASK_NOTIFY_COOL  = 2.0        # seconds between Flask notifications


# ─────────────────────────────────────────────
# GLOBALS
# ─────────────────────────────────────────────
_last_notify_time = 0.0
_motion_state     = {"detected": False, "count": 0}


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def log_motion_event(event: str):
    """Append a timestamped motion event to the log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {event}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)
    print(entry, end="")


def notify_flask(motion_detected: bool, count: int):
    """
    Send motion status to the Flask backend (fire-and-forget in a thread).
    Throttled by FLASK_NOTIFY_COOL to avoid spamming.
    """
    global _last_notify_time
    now = time.time()
    if now - _last_notify_time < FLASK_NOTIFY_COOL:
        return
    _last_notify_time = now

    payload = {"motion_detected": motion_detected, "count": count}

    def _post():
        try:
            requests.post(FLASK_STATUS_URL, json=payload, timeout=0.5)
        except Exception:
            pass  # Flask may not be running – that's OK

    threading.Thread(target=_post, daemon=True).start()


def draw_overlay(frame: np.ndarray, boxes: list, fps: float):
    """Draw bounding boxes and HUD onto the frame."""
    for (x, y, w, h) in boxes:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    motion_text = f"Motion: {'YES' if boxes else 'NO'}"
    color       = (0, 0, 255) if boxes else (0, 255, 0)
    cv2.putText(frame, motion_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    cv2.putText(frame, f"Objects: {len(boxes)}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    """Main entry point for the Background Subtraction Motion Detection pipeline."""

    # ── PHASE 2: Camera Setup ──────────────────────────────────────────────
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera. Check CAMERA_INDEX.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    print(f"[INFO] Camera opened – resolution {FRAME_WIDTH}×{FRAME_HEIGHT}")

    # MOG2 background subtractor (Phase 3 workhorse)
    mog2 = cv2.createBackgroundSubtractorMOG2(
        history=500,
        varThreshold=40,
        detectShadows=False
    )
    morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    prev_motion   = False
    frame_count   = 0
    fps_timer     = time.time()
    fps           = 0.0

    log_motion_event("System started.")

    while True:
        # ── PHASE 2: Read Frame ────────────────────────────────────────────
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Frame read failed – retrying…")
            time.sleep(0.05)
            continue

        frame_count += 1

        # ── PHASE 3: Background Subtraction Logic ─────────────────────────
        # 1. Pre-process: grayscale + Gaussian blur reduces noise
        gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, GAUSSIAN_BLUR_SIZE, 0)

        # 2. Compute foreground mask via MOG2
        fg_mask = mog2.apply(blurred)

        # 3. Morphological cleanup: remove tiny blobs, fill holes
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN,  morph_kernel, iterations=1)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, morph_kernel, iterations=2)
        fg_mask = cv2.dilate(fg_mask, morph_kernel, iterations=2)

        # ── PHASE 4: Contour Detection & Bounding Boxes ───────────────────
        # 1. Find external contours on the cleaned mask
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 2. Filter by minimum area to suppress shadow/noise blobs
        boxes = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > MIN_CONTOUR_AREA:
                boxes.append(cv2.boundingRect(cnt))  # (x, y, w, h)

        # 3. Draw bounding rectangles + HUD
        if frame_count % 15 == 0:
            elapsed = time.time() - fps_timer
            fps     = 15 / elapsed if elapsed > 0 else 0.0
            fps_timer = time.time()

        draw_overlay(frame, boxes, fps)

        # ── PHASE 5: Logging & Communication ─────────────────────────────
        # 1. Log state transitions (start / stop of motion)
        motion_now = len(boxes) > 0
        if motion_now and not prev_motion:
            log_motion_event(f"MOTION STARTED – {len(boxes)} object(s) detected.")
        elif not motion_now and prev_motion:
            log_motion_event("MOTION STOPPED.")
        prev_motion = motion_now

        # 2. Notify Flask backend (throttled)
        notify_flask(motion_now, len(boxes))

        # ── Display ───────────────────────────────────────────────────────
        cv2.imshow("Background Subtraction – Motion Detection", frame)
        cv2.imshow("Foreground Mask", fg_mask)

        # Break on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            log_motion_event("System stopped by user.")
            break

    # ── Release Resources ─────────────────────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Resources released. Exiting.")


if __name__ == "__main__":
    main()
