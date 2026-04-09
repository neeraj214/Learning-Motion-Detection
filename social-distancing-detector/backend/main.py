"""
main.py – CLI entry point for the Social Distancing Detector backend.

Runs a headless (or windowed) detection loop and prints real-time alerts
to stdout. Intended for development / testing without the FastAPI layer.

Usage:
    python -m backend.main
    python -m backend.main --camera 1 --headless
"""

import argparse
import cv2
import numpy as np
import time
import datetime
import logging

from backend.core.detector import Detector
from backend.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────


# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────
def run(camera_index: int = 0, headless: bool = False):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        logger.error("Cannot open camera %d.", camera_index)
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  settings.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_HEIGHT)
    logger.info(
        "Camera %d opened @ %dx%d. Press 'q' to quit.",
        camera_index, settings.FRAME_WIDTH, settings.FRAME_HEIGHT
    )

    detector    = Detector()
    frame_count = 0
    fps_timer   = time.time()
    fps         = 0.0
    alarm_cooldown = 0  # frames remaining on alarm cooldown

    while True:
        ret, frame = cap.read()
        if not ret:
            logger.warning("Frame read failed – retrying…")
            time.sleep(0.05)
            continue

        frame_count += 1

        # ── Detect + Track ────────────────────────────────────────────────
        # process_frame_full returns (annotated_frame, id_to_box, violations, alarm_state)
        # We pass the latest calculated FPS for the HUD.
        annotated_frame, id_to_box, violations, alarm_state = detector.process_frame_full(frame, fps)

        # ── FPS computation ───────────────────────────────────────────────
        if frame_count % 30 == 0:
            elapsed   = time.time() - fps_timer
            fps       = 30 / elapsed if elapsed > 0 else 0.0
            fps_timer = time.time()
            logger.info(
                "FPS: %.1f | People: %d | Violations: %d",
                fps, len(id_to_box), len(violations),
            )

        # ── Alarm: print & cooldown ───────────────────────────────────────
        if alarm_state == "alarm" and alarm_cooldown <= 0:
            logger.warning(
                "⚠ SOCIAL DISTANCING VIOLATION – State: %s | Violations: %d",
                alarm_state.upper(), len(violations)
            )
            alarm_cooldown = settings.ALARM_COOLDOWN_FRAMES
        if alarm_cooldown > 0:
            alarm_cooldown -= 1

        # ── Visual output (skip in headless mode) ─────────────────────────
        if not headless:
            # We must draw the current timestamp as it is not in the core Detector annotation
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(annotated_frame, ts, (10, annotated_frame.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

            cv2.imshow("Social Distancing Detector", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                logger.info("Quit signal received.")
                break
        else:
            # In headless mode, break via KeyboardInterrupt
            pass

    cap.release()
    if not headless:
        cv2.destroyAllWindows()
    logger.info("Detector stopped.")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def _parse_args():
    parser = argparse.ArgumentParser(description="Social Distancing Detector – CLI")
    parser.add_argument("--camera",   type=int,  default=0, help="Camera index (default: 0)")
    parser.add_argument("--headless", action="store_true",  help="Run without GUI window")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    try:
        run(camera_index=args.camera, headless=args.headless)
    except KeyboardInterrupt:
        logger.info("Interrupted. Exiting.")
