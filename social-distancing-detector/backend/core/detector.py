import cv2
import numpy as np
from .config import settings

class Detector:
    def __init__(self):
        """Initialize OpenCV Background Subtractor MOG2 instance."""
        self.subtractor = cv2.createBackgroundSubtractorMOG2(
            history=settings.MOG2_HISTORY,
            varThreshold=settings.MOG2_VAR_THRESHOLD,
            detectShadows=settings.MOG2_DETECT_SHADOWS
        )
        self.kernel = np.ones(settings.MORPH_KERNEL_SIZE, np.uint8)

    def get_motion_mask(self, frame: np.ndarray) -> np.ndarray:
        """
        Convert frame to grayscale, apply MOG2, and clean up the mask with morphology.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fg_mask = self.subtractor.apply(gray)
        
        # Morphological opening (remove noise)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, self.kernel)
        # Morphological dilation (fill gaps)
        fg_mask = cv2.dilate(fg_mask, self.kernel, iterations=2)
        
        return fg_mask

    def get_bounding_boxes(self, mask: np.ndarray) -> list[tuple[int, int, int, int]]:
        """
        Find external contours and filter them by minimum area.
        Returns a list of (x, y, w, h) bounding boxes.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > settings.MIN_CONTOUR_AREA:
                boxes.append(cv2.boundingRect(cnt))
        return boxes

    def apply_nms(self, boxes: list[tuple]) -> list[tuple[int, int, int, int]]:
        """
        Apply Non-Maximum Suppression (OpenCV's NMSBoxes) logic.
        """
        if not boxes:
            return []
            
        # NMSBoxes expects list of boxes, list of confidences, and thresholds
        # Using a dummy confidence of 1.0
        confidences = [1.0] * len(boxes)
        # Use cv2.dnn.NMSBoxes (doesn't require a dnn model, just geometry)
        indices = cv2.dnn.NMSBoxes(boxes, confidences, score_threshold=0.0, nms_threshold=settings.NMS_IOU_THRESHOLD)
        
        filtered_boxes = []
        if len(indices) > 0:
            for i in indices.flatten():
                filtered_boxes.append(boxes[i])
        
        return filtered_boxes

    def process_frame(self, frame: np.ndarray) -> list[tuple[int, int, int, int]]:
        """
        The full detection pipeline: mask generation -> box extraction -> NMS.
        """
        mask = self.get_motion_mask(frame)
        raw_boxes = self.get_bounding_boxes(mask)
        final_boxes = self.apply_nms(raw_boxes)
        return final_boxes

if __name__ == "__main__":
    # Smoke test: reads 5 frames from VideoCapture(0) and prints detected boxes count.
    cap = cv2.VideoCapture(0)
    detector = Detector()
    print("[INFO] Starting smoke test for Detector...")
    for i in range(5):
        ret, frame = cap.read()
        if not ret:
            break
        boxes = detector.process_frame(frame)
        print(f"Frame {i+1}: Found {len(boxes)} boxes.")
    cap.release()
    cv2.destroyAllWindows()
