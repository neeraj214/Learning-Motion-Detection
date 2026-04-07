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
def find_violations(id_to_box: dict) -> list[tuple[int, int]]:
    """Return pairs of object IDs that are too close together."""
    items = list(id_to_box.items())
    violations = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            id_a, (xa, ya, wa, ha) = items[i]
            id_b, (xb, yb, wb, hb) = items[j]
            cx_a, cy_a = xa + wa // 2, ya + ha // 2
            cx_b, cy_b = xb + wb // 2, yb + hb // 2
            dist = np.sqrt((cx_a - cx_b) ** 2 + (cy_a - cy_b) ** 2)
            if dist < settings.DISTANCE_THRESHOLD_PX:
                violations.append((id_a, id_b))
    return violations


def annotate_frame(
    frame: np.ndarray,
    id_to_box: dict,
    violations: list,
    fps: float,
) -> np.ndarray:
    """Draw bounding boxes, IDs, violation lines, and HUD onto the frame."""
    violation_ids = {uid for pair in violations for uid in pair}

    for obj_id, (x, y, w, h) in id_to_box.items():
        color = (0, 0, 255) if obj_id in violation_ids else (0, 255, 0)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(
            frame, f"ID {obj_id}", (x, max(y - 8, 12)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2,
        )

    for (id_a, id_b) in violations:
        (xa, ya, wa, ha) = id_to_box[id_a]
        (xb, yb, wb, hb) = id_to_box[id_b]
        pt_a = (xa + wa // 2, ya + ha // 2)
        pt_b = (xb + wb // 2, yb + hb // 2)
        cv2.line(frame, pt_a, pt_b, (0, 0, 255), 2)

    # HUD
    status_text  = f"VIOLATIONS: {len(violations)}" if violations else "SAFE"
    status_color = (0, 0, 255) if violations else (0, 200, 0)
    cv2.putText(frame, status_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, status_color, 2)
    cv2.putText(
        frame,
        f"FPS: {fps:.1f}   People tracked: {len(id_to_box)}",
        (10, 62),
        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 200), 2,
    )
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, ts, (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    return frame


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
        id_to_box  = detector.process_frame_with_ids(frame)
        violations = find_violations(id_to_box)

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
        if violations and alarm_cooldown <= 0:
            logger.warning(
                "⚠ SOCIAL DISTANCING VIOLATION – IDs too close: %s",
                violations,
            )
            alarm_cooldown = settings.ALARM_COOLDOWN_FRAMES
        if alarm_cooldown > 0:
            alarm_cooldown -= 1

        # ── Visual output (skip in headless mode) ─────────────────────────
        if not headless:
            annotate_frame(frame, id_to_box, violations, fps)
            cv2.imshow("Social Distancing Detector", frame)
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
