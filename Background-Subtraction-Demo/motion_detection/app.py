import cv2
import numpy as np
import threading
import time
import logging
from flask import Flask, jsonify, Response, request
from flask_cors import CORS

# ── Import the cv2 processing loop (runs in a background thread)
# We use a lazy import so app.py can be run standalone too.

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow React frontend on any port

# ─────────────────────────────────────────────
# SHARED STATE  (written by motion thread, read by Flask)
# ─────────────────────────────────────────────
_state_lock = threading.Lock()
_motion_state = {
    "motion_detected": False,
    "object_count": 0,
    "status": "Idle",
}

# Frame buffer for MJPEG streaming
_frame_lock   = threading.Lock()
_latest_frame = None   # raw JPEG bytes


# ─────────────────────────────────────────────
# INTERNAL: background thread sets the state
# ─────────────────────────────────────────────
def _update_state(motion: bool, count: int):
    """Thread-safe state update (called from within app or motion thread)."""
    with _state_lock:
        _motion_state["motion_detected"] = motion
        _motion_state["object_count"]    = count
        _motion_state["status"]          = "Motion detected" if motion else "Monitoring"


def _push_frame(jpeg_bytes: bytes):
    """Store the latest encoded frame for streaming."""
    global _latest_frame
    with _frame_lock:
        _latest_frame = jpeg_bytes


# ─────────────────────────────────────────────
# MOTION PROCESSING THREAD
# ─────────────────────────────────────────────
MIN_CONTOUR_AREA = 1500
GAUSSIAN_BLUR    = (21, 21)

def _generate_frames(camera_index: int = 0):
    """
    Background thread: opens the webcam, runs MOG2 subtraction,
    publishes frames via _push_frame() and updates _motion_state.
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        logger.error("Cannot open camera %d. Video feed unavailable.", camera_index)
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    logger.info("Camera %d opened for MJPEG streaming.", camera_index)

    mog2 = cv2.createBackgroundSubtractorMOG2(
        history=500, varThreshold=40, detectShadows=False
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue

        # --- Background subtraction ---
        gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, GAUSSIAN_BLUR, 0)
        fg_mask = mog2.apply(blurred)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN,  kernel, iterations=1)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)

        # --- Contour detection ---
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) > MIN_CONTOUR_AREA]

        # --- Annotate frame ---
        for (x, y, w, h) in boxes:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        motion = len(boxes) > 0
        color  = (0, 0, 255) if motion else (0, 200, 0)
        cv2.putText(frame, f"Motion: {'YES' if motion else 'NO'}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        cv2.putText(frame, f"Objects: {len(boxes)}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # --- Publish ---
        _update_state(motion, len(boxes))
        _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        _push_frame(jpeg.tobytes())

    cap.release()


def start_camera_thread(camera_index: int = 0):
    """Launch the background camera/processing thread."""
    t = threading.Thread(target=_generate_frames, args=(camera_index,), daemon=True)
    t.start()
    logger.info("Camera processing thread started.")


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────
@app.route("/")
def index():
    """Health-check endpoint."""
    return jsonify({"message": "Motion Detection Backend is running.", "status": "ok"})


def _mjpeg_stream():
    """Generator: yields MJPEG multipart frames."""
    while True:
        with _frame_lock:
            frame = _latest_frame

        if frame is None:
            time.sleep(0.05)
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        )
        time.sleep(1 / 30)  # ~30 fps cap


@app.route("/video_feed")
def video_feed():
    """MJPEG stream endpoint for the React frontend."""
    return Response(
        _mjpeg_stream(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/motion_status")
def motion_status():
    """Return the current motion detection status as JSON."""
    with _state_lock:
        snapshot = dict(_motion_state)
    return jsonify(snapshot)


@app.route("/motion_status_update", methods=["POST"])
def motion_status_update():
    """
    Internal endpoint: main.py (standalone script) can POST state updates here.
    Body: { "motion_detected": bool, "count": int }
    """
    data = request.get_json(force=True, silent=True) or {}
    _update_state(
        bool(data.get("motion_detected", False)),
        int(data.get("count", 0))
    )
    return jsonify({"status": "ok"})


@app.route("/set_threshold", methods=["POST"])
def set_threshold():
    """
    Update the minimum contour area threshold at runtime.
    Body: { "threshold": int }
    """
    global MIN_CONTOUR_AREA
    data = request.get_json(force=True, silent=True) or {}
    new_val = data.get("threshold")
    if new_val is not None and isinstance(new_val, (int, float)) and new_val > 0:
        MIN_CONTOUR_AREA = int(new_val)
        logger.info("Threshold updated to %d px²", MIN_CONTOUR_AREA)
        return jsonify({"status": "success", "threshold": MIN_CONTOUR_AREA})
    return jsonify({"status": "error", "message": "Invalid threshold value."}), 400


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Start processing thread then serve
    start_camera_thread(camera_index=0)
    logger.info("Flask server starting on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
