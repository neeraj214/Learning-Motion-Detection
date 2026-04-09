"""
stream.py – FastAPI-compatible MJPEG / WebSocket streaming layer
for the Social Distancing Detector.

Usage (standalone):
    python -m backend.stream          # serves on :8000

Depends on:
    pip install fastapi uvicorn opencv-python numpy
"""

import cv2
import numpy as np
import time
import asyncio
import threading
import logging
from typing import Generator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .core.detector import Detector
from .core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Social Distancing Detector – Stream API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# SHARED STATE
# ─────────────────────────────────────────────
_frame_lock   = threading.Lock()
_latest_frame: bytes | None = None

_state_lock = threading.Lock()
_detection_state = {
    "active_ids": [],
    "violation_pairs": [],
    "alarm_state": "safe",
    "fps": 0.0,
}

# ─────────────────────────────────────────────
# VIOLATION DETECTION HELPER
# ─────────────────────────────────────────────


# ─────────────────────────────────────────────
# CAMERA / PROCESSING THREAD
# ─────────────────────────────────────────────
def _camera_worker(camera_index: int = 0):
    """
    Background thread: reads frames from the camera, runs the full
    detection + tracking pipeline, annotates the frame with IDs and
    violation alerts, then stores the JPEG bytes for streaming.
    """
    global _latest_frame

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        logger.error("Cannot open camera %d.", camera_index)
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  settings.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_HEIGHT)
    logger.info("Camera %d opened (%dx%d).",
                camera_index, settings.FRAME_WIDTH, settings.FRAME_HEIGHT)

    detector    = Detector()
    frame_count = 0
    fps_timer   = time.time()
    fps         = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue

        frame_count += 1

        # ── Detect + Track + Annotate ─────────────────────────────────────
        # process_frame_full returns (annotated_frame, id_to_box, violations, alarm_state)
        annotated_frame, id_to_box, violations, alarm_state = detector.process_frame_full(frame, fps)

        # ── FPS computation ───────────────────────────────────────────────
        if frame_count % 30 == 0:
            elapsed   = time.time() - fps_timer
            fps       = 30 / elapsed if elapsed > 0 else 0.0
            fps_timer = time.time()

        # ── Publish ──────────────────────────────────────────────────────
        with _state_lock:
            _detection_state["active_ids"]       = list(id_to_box.keys())
            _detection_state["violation_pairs"]  = violations
            _detection_state["alarm_state"]      = alarm_state
            _detection_state["fps"]              = round(fps, 1)

        _, jpeg = cv2.imencode(".jpg", annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        with _frame_lock:
            _latest_frame = jpeg.tobytes()

    cap.release()
    logger.info("Camera thread exiting.")


def start_camera_worker(camera_index: int = 0):
    """Spawn the background camera processing thread."""
    t = threading.Thread(target=_camera_worker, args=(camera_index,), daemon=True)
    t.start()


# ─────────────────────────────────────────────
# MJPEG STREAM GENERATOR
# ─────────────────────────────────────────────
def _generate_mjpeg() -> Generator[bytes, None, None]:
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
        time.sleep(1 / 30)


# ─────────────────────────────────────────────
# FASTAPI ROUTES
# ─────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "Social Distancing Detector API is running."}


@app.get("/video_feed")
async def video_feed():
    """MJPEG stream for embedding in <img src='/video_feed'>."""
    return StreamingResponse(
        _generate_mjpeg(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/status")
async def status():
    """Return current detection state as JSON."""
    with _state_lock:
        snap = dict(_detection_state)
        snap["violation_pairs"] = [list(p) for p in snap["violation_pairs"]]
    return JSONResponse(content=snap)


# ─────────────────────────────────────────────
# STARTUP EVENT
# ─────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, start_camera_worker, 0)
    logger.info("Stream API started – camera worker launching.")


# ─────────────────────────────────────────────
# STANDALONE ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    start_camera_worker(camera_index=0)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
