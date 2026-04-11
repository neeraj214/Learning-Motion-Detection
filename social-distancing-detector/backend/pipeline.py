import numpy as np

from .core.detector import Detector
from .core.distancing import DistanceChecker, AlarmStateMachine, Annotator

class FramePipeline:
    def __init__(self):
        self.detector = Detector()
        self.checker = DistanceChecker()
        self.alarm = AlarmStateMachine()
        self.annotator = Annotator()
        self.frame_count: int = 0

    def process(self, frame: np.ndarray) -> tuple[np.ndarray, dict]:
        self.frame_count += 1
        tracked = self.detector.process_frame_with_ids(frame)
        result = self.checker.check_frame(tracked)
        alarm_state = self.alarm.update(result["violation_count"])
        annotated = self.annotator.annotate(frame, result, alarm_state)
        
        stats = {
            "frame": self.frame_count,
            "total_people": result["total_people"],
            "violation_count": result["violation_count"],
            "alarm_state": alarm_state["state"],
            "total_violations": alarm_state["total_violations"],
            "violations": [
                {"id_a": a, "id_b": b, "distance": round(d, 1)}
                for (a, b, d) in result["violations"]
            ],
        }
        
        return annotated, stats

pipeline = FramePipeline()
