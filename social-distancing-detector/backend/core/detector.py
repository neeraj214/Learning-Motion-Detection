import cv2
import numpy as np
import time
from .config import settings
from .tracker import CentroidTracker


class Detector:
    def __init__(self):
        """Initialize MOG2 subtractor and CentroidTracker."""
        self.subtractor = cv2.createBackgroundSubtractorMOG2(
            history=settings.MOG2_HISTORY,
            varThreshold=settings.MOG2_VAR_THRESHOLD,
            detectShadows=settings.MOG2_DETECT_SHADOWS
        )
        self.kernel  = np.ones(settings.MORPH_KERNEL_SIZE, np.uint8)
        self.tracker = CentroidTracker(max_disappeared=40)

    # ─────────────────────────────────────────────
    # LOW-LEVEL PIPELINE STEPS
    # ─────────────────────────────────────────────
    def get_motion_mask(self, frame: np.ndarray) -> np.ndarray:
        """
        Convert frame to grayscale, apply MOG2, and clean up the mask with morphology.
        """
        gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fg_mask = self.subtractor.apply(gray)

        # Morphological opening (remove noise)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, self.kernel)
        # Morphological dilation (fill gaps)
        fg_mask = cv2.dilate(fg_mask, self.kernel, iterations=2)

        return fg_mask

    def get_bounding_boxes(self, mask: np.ndarray) -> list[tuple[int, int, int, int]]:
        """
        Find external contours and filter by minimum area.
        Returns a list of (x, y, w, h) bounding boxes.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for cnt in contours:
            if cv2.contourArea(cnt) > settings.MIN_CONTOUR_AREA:
                boxes.append(cv2.boundingRect(cnt))
        return boxes

    def apply_nms(self, boxes: list[tuple]) -> list[tuple[int, int, int, int]]:
        """
        Apply Non-Maximum Suppression via cv2.dnn.NMSBoxes.
        """
        if not boxes:
            return []
        confidences = [1.0] * len(boxes)
        indices = cv2.dnn.NMSBoxes(
            boxes, confidences,
            score_threshold=0.0,
            nms_threshold=settings.NMS_IOU_THRESHOLD
        )
        if len(indices) > 0:
            return [boxes[i] for i in indices.flatten()]
        return []

    def process_frame(self, frame: np.ndarray) -> list[tuple[int, int, int, int]]:
        """
        Full detection pipeline: mask → boxes → NMS.
        Returns list of (x, y, w, h) tuples.
        """
        mask      = self.get_motion_mask(frame)
        raw_boxes = self.get_bounding_boxes(mask)
        return self.apply_nms(raw_boxes)

    # ─────────────────────────────────────────────
    # TRACKER-INTEGRATED METHOD
    # ─────────────────────────────────────────────
    def process_frame_with_ids(self, frame: np.ndarray) -> dict[int, tuple[int, int, int, int]]:
        """
        Full pipeline chained with CentroidTracker.

        Returns
        -------
        dict[int, tuple[int,int,int,int]]
            Mapping of persistent object ID → (x, y, w, h) bounding box.
            IDs survive across frames as long as the object remains visible.
        """
        boxes       = self.process_frame(frame)
        id_centroid = self.tracker.update(boxes)  # dict[int, np.ndarray(cx,cy)]

        # Map each tracked centroid back to the closest detected bounding box.
        # Strategy: for each ID, find the box whose own centroid is nearest.
        id_to_box: dict[int, tuple[int, int, int, int]] = {}

        if not boxes:
            return id_to_box

        # Pre-compute box centroids
        box_centroids = np.array(
            [(x + w // 2, y + h // 2) for (x, y, w, h) in boxes], dtype="float"
        )

        for obj_id, centroid in id_centroid.items():
            dists = np.linalg.norm(box_centroids - centroid.astype("float"), axis=1)
            best  = int(np.argmin(dists))
            id_to_box[obj_id] = boxes[best]

        return id_to_box


# ─────────────────────────────────────────────
# ENHANCED SMOKE TEST – live webcam with IDs
# ─────────────────────────────────────────────
if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera.")
        raise SystemExit(1)

    detector    = Detector()
    frame_count = 0
    fps_timer   = time.time()
    fps         = 0.0

    print("[INFO] Starting enhanced smoke test – press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Get tracked IDs → boxes
        id_to_box = detector.process_frame_with_ids(frame)

        # Draw bounding boxes and persistent IDs
        for obj_id, (x, y, w, h) in id_to_box.items():
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"ID {obj_id}", (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            # Mark centroid
            cx, cy = x + w // 2, y + h // 2
            cv2.circle(frame, (cx, cy), 4, (255, 0, 0), -1)

        # FPS display every 30 frames
        if frame_count % 30 == 0:
            elapsed   = time.time() - fps_timer
            fps       = 30 / elapsed if elapsed > 0 else 0.0
            fps_timer = time.time()
            print(f"[FPS] {fps:.1f}  |  Active IDs: {list(id_to_box.keys())}")

        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        cv2.putText(frame, f"IDs: {list(id_to_box.keys())}", (10, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        cv2.imshow("Social Distancing – Tracker Smoke Test", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Smoke test complete.")
