import cv2
import numpy as np
import itertools
from backend.core.config import settings

class DistanceChecker:
    def __init__(self):
        self.threshold: int = settings.DISTANCE_THRESHOLD_PX

    def get_centroids(self, tracked: dict[int, tuple]) -> dict[int, np.ndarray]:
        """
        Input: { id: (x, y, w, h) }
        Output: { id: np.array([cx, cy]) }
        """
        centroids = {}
        for obj_id, (x, y, w, h) in tracked.items():
            cx = x + w // 2
            cy = y + h // 2
            centroids[obj_id] = np.array([cx, cy])
        return centroids

    def compute_distances(self, centroids: dict[int, np.ndarray]) -> list[tuple]:
        """
        Takes the output of get_centroids.
        Returns a list of tuples: [(id_a, id_b, dist), ...]
        """
        if len(centroids) < 2:
            return []

        ids = list(centroids.keys())
        distances = []
        for id_a, id_b in itertools.combinations(ids, 2):
            dist = float(np.linalg.norm(centroids[id_a] - centroids[id_b]))
            distances.append((id_a, id_b, dist))
        return distances

    def get_violations(self, distances: list[tuple]) -> list[tuple]:
        """
        Filter the list from compute_distances.
        Keep only tuples where dist < self.threshold.
        """
        return [d for d in distances if d[2] < self.threshold]

    def check_frame(self, tracked: dict[int, tuple]) -> dict:
        """
        Chains get_centroids → compute_distances → get_violations.
        Returns a result dict summaring findings.
        """
        centroids = self.get_centroids(tracked)
        all_distances = self.compute_distances(centroids)
        violations = self.get_violations(all_distances)
        
        violating_ids = set()
        for id_a, id_b, _ in violations:
            violating_ids.add(id_a)
            violating_ids.add(id_b)

        # Convert centroids to list for JSON serialization if needed
        centroids_serializable = {k: v.tolist() for k, v in centroids.items()}

        return {
            "total_people": len(tracked),
            "centroids": centroids_serializable,
            "all_distances": all_distances,
            "violations": violations,
            "violation_count": len(violations),
            "violating_ids": violating_ids,
        }

class AlarmStateMachine:
    def __init__(self):
        self.state: str = "safe"          # "safe" | "warning" | "alarm"
        self.violation_frames: int = 0    # consecutive frames with violations
        self.clear_frames: int = 0        # consecutive frames without violations
        self.total_violations: int = 0    # cumulative violation events (never resets)
        self.cooldown: int = settings.ALARM_COOLDOWN_FRAMES

        # Thresholds (hardcoded, not in config)
        self.WARN_THRESHOLD = 3     # frames with violations before entering "warning"
        self.ALARM_THRESHOLD = 8    # frames with violations before entering "alarm"
        self.CLEAR_THRESHOLD = 15   # consecutive clear frames before downgrading state

    def update(self, violation_count: int) -> dict:
        """
        Logic to smooth out noisy violation signals into a stable state.
        """
        if violation_count > 0:
            self.violation_frames += 1
            self.clear_frames = 0
            
            if self.violation_frames >= self.ALARM_THRESHOLD:
                self.state = "alarm"
                self.total_violations += violation_count
            elif self.violation_frames >= self.WARN_THRESHOLD:
                self.state = "warning"
        else:
            self.clear_frames += 1
            self.violation_frames = 0
            
            if self.clear_frames >= self.CLEAR_THRESHOLD:
                self.state = "safe"

        return {
            "state": self.state,
            "violation_frames": self.violation_frames,
            "clear_frames": self.clear_frames,
            "total_violations": self.total_violations,
        }

    def reset(self) -> None:
        """Resets all state back to initial values except total_violations."""
        self.state = "safe"
        self.violation_frames = 0
        self.clear_frames = 0

class Annotator:
    COLOR_SAFE     = (0, 200, 0)
    COLOR_WARN     = (0, 165, 255)
    COLOR_ALARM    = (0, 0, 220)
    COLOR_LINE     = (0, 0, 220)
    COLOR_TEXT_BG  = (20, 20, 20)

    def _get_state_color(self, state: str) -> tuple:
        if state == "safe":
            return self.COLOR_SAFE
        elif state == "warning":
            return self.COLOR_WARN
        elif state == "alarm":
            return self.COLOR_ALARM
        return self.COLOR_SAFE

    def draw_boxes(self, frame, tracked: dict[int, tuple], violating_ids: set, state: str) -> None:
        for person_id, (x, y, w, h) in tracked.items():
            color = self.COLOR_ALARM if person_id in violating_ids else self.COLOR_SAFE
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            label = f"P{person_id}"
            (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            text_y = y - 10
            
            # small filled rectangle behind the text
            cv2.rectangle(frame, (x, text_y - text_h - 5), (x + text_w, text_y + 5), self.COLOR_TEXT_BG, -1)
            cv2.putText(frame, label, (x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    def draw_violation_lines(self, frame, centroids: dict, violations: list) -> None:
        for id_a, id_b, dist in violations:
            pt1 = (int(centroids[id_a][0]), int(centroids[id_a][1]))
            pt2 = (int(centroids[id_b][0]), int(centroids[id_b][1]))
            cv2.line(frame, pt1, pt2, self.COLOR_LINE, 2)
            
            midpoint = ((pt1[0] + pt2[0]) // 2, (pt1[1] + pt2[1]) // 2)
            cv2.putText(frame, f"{int(dist)}px", midpoint, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def draw_hud(self, frame, result: dict, alarm: dict) -> None:
        x, y, w, h = 10, 10, 220, 80
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), self.COLOR_TEXT_BG, -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        cv2.putText(frame, f"People: {result['total_people']}", (x + 10, y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        cv2.putText(frame, f"Violations: {result['violation_count']}", (x + 10, y + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        
        state_color = self._get_state_color(alarm['state'])
        cv2.putText(frame, f"Status: {alarm['state'].upper()}", (x + 10, y + 75), cv2.FONT_HERSHEY_SIMPLEX, 0.55, state_color, 1)

    def annotate(self, frame, result: dict, alarm: dict, tracked: dict = None) -> np.ndarray:
        if tracked is None:
            tracked = result.get('tracked', {})
            
        annotated_frame = frame.copy()
        self.draw_boxes(annotated_frame, tracked, result['violating_ids'], alarm['state'])
        self.draw_violation_lines(annotated_frame, result['centroids'], result['violations'])
        self.draw_hud(annotated_frame, result, alarm)
        
        return annotated_frame

if __name__ == "__main__":

    asm = AlarmStateMachine()
    
    print("--- Simulating Violations (10 frames) ---")
    for i in range(1, 11):
        res = asm.update(violation_count=2)
        print(f"Frame {i:02d}: {res['state']} (v_frames={res['violation_frames']}, total_v={res['total_violations']})")
        
        # Confirm transitions
        if i == asm.WARN_THRESHOLD:
            assert res["state"] == "warning"
        if i == asm.ALARM_THRESHOLD:
            assert res["state"] == "alarm"

    print("\n--- Simulating Clear Frames (20 frames) ---")
    for i in range(1, 21):
        res = asm.update(violation_count=0)
        print(f"Frame {i:02d}: {res['state']} (c_frames={res['clear_frames']})")
        
        # Confirm recovery
        if i == asm.CLEAR_THRESHOLD:
            assert res["state"] == "safe"

    print("\nAlarmStateMachine Smoke test passed!")
