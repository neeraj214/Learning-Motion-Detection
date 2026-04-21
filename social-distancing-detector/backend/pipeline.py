import numpy as np
import time

from core.detector import Detector
from core.distancing import DistanceChecker, AlarmStateMachine, Annotator

class FramePipeline:
    def __init__(self):
        self.detector = Detector()
        self.checker = DistanceChecker()
        self.alarm = AlarmStateMachine()
        self.annotator = Annotator()
        self.frame_count: int = 0
        self.last_time = time.time()
        self.fps = 0.0

    def process(self, frame: np.ndarray) -> tuple[np.ndarray, dict]:
        self.frame_count += 1
        
        # Calculate FPS
        current_time = time.time()
        dt = current_time - self.last_time
        if dt > 0:
            current_fps = 1.0 / dt
            self.fps = self.fps * 0.9 + current_fps * 0.1
        self.last_time = current_time

        tracked = self.detector.process_frame_with_ids(frame)
        result = self.checker.check_frame(tracked)
        alarm_state = self.alarm.update(result["violation_count"])
        annotated = self.annotator.annotate(frame, result, alarm_state)
        
        stats = {
            "frame": self.frame_count,
            "fps": round(self.fps, 1),
            "active_ids": sorted([int(id) for id in tracked.keys()]) if tracked else [],
            "total_people": result["total_people"],
            "violation_count": result["violation_count"],
            "alarm_state": alarm_state["state"],
            "total_violations": alarm_state["total_violations"],
            "violation_pairs": [
                {"id_a": a, "id_b": b, "distance": round(d, 1)}
                for (a, b, d) in result["violations"]
            ],
        }
        
        return annotated, stats

pipeline = FramePipeline()
