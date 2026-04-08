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
        Full pipeline: detect boxes -> update tracker -> match IDs back to boxes.
        Returns { id: (x, y, w, h) }.
        """
        # 1. Get detected boxes
        boxes = self.process_frame(frame)
        
        # 2. Update tracker to get { id: centroid }
        id_to_centroid = self.tracker.update(boxes)

        # 3. Match each tracked ID back to its box by centroid distance
        id_to_box: dict[int, tuple[int, int, int, int]] = {}
        
        if not boxes or not id_to_centroid:
            return id_to_box

        # Pre-compute centroids for detection boxes
        detection_centroids = np.array(
            [(x + w // 2, y + h // 2) for (x, y, w, h) in boxes], dtype="float"
        )

        for obj_id, centroid in id_to_centroid.items():
            # Calculate distances between this tracked centroid and all current detections
            dists = np.linalg.norm(detection_centroids - centroid.astype("float"), axis=1)
            best_idx = int(np.argmin(dists))
            
            # 4. Filter by distance: if the closest box is too far (> 100px), 
            # consider the object "currently not matched to a box" (e.g., disappeared)
            if dists[best_idx] < 100:
                id_to_box[obj_id] = boxes[best_idx]

        return id_to_box

    def find_violations(self, id_to_box: dict) -> list[tuple[int, int]]:
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
        self,
        frame: np.ndarray,
        id_to_box: dict,
        violations: list,
        fps: float = 0.0
    ) -> np.ndarray:
        """Draw bounding boxes, IDs, violation lines, and HUD onto the frame."""
        violation_ids = {uid for pair in violations for uid in pair}

        for obj_id, (x, y, w, h) in id_to_box.items():
            color = (0, 0, 255) if obj_id in violation_ids else (0, 255, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(
                frame, f"ID {obj_id}", (x, max(y - 8, 12)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2
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
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        cv2.putText(
            frame, f"FPS: {fps:.1f}  People: {len(id_to_box)}", (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2
        )
        return frame

    def process_frame_full(self, frame: np.ndarray, fps: float = 0.0) -> tuple[np.ndarray, dict, list]:
        """
        Convenience method: runs detection + tracking + violation check + annotation.
        Returns (annotated_frame, id_to_box, violations).
        """
        id_to_box  = self.process_frame_with_ids(frame)
        violations = self.find_violations(id_to_box)
        annotated  = self.annotate_frame(frame.copy(), id_to_box, violations, fps)
        return annotated, id_to_box, violations


# ─────────────────────────────────────────────
# REFINED SMOKE TEST – live webcam test loop
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

    print("[INFO] Starting smoke test (max 200 frames) – press 'q' to quit.")

    while frame_count < 200:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # 1. Process frame to get tracked objects
        id_to_box = detector.process_frame_with_ids(frame)

        # 2. Draw each bounding box and person ID
        for obj_id, (x, y, w, h) in id_to_box.items():
            # Green box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # Person ID text above box
            cv2.putText(frame, f"Person {obj_id}", (x, max(y - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # 3. FPS Calculation every 30 frames
        if frame_count % 30 == 0:
            elapsed   = time.time() - fps_timer
            fps       = 30 / elapsed if elapsed > 0 else 0.0
            fps_timer = time.time()
            print(f"[STATUS] Frame: {frame_count}/200 | FPS: {fps:.1f} | Tracking: {len(id_to_box)}")

        # 4. Display result
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Detector Test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("[INFO] Quit signal received.")
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print(f"[INFO] Smoke test complete. Processed {frame_count} frames.")
