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

if __name__ == "__main__":
    checker = DistanceChecker()
    
    # Mock tracked dict with 3 people:
    # IDs 0 and 1 are close; ID 2 is far away
    mock_tracked = {
        0: (50, 50, 40, 80), 
        1: (80, 60, 40, 80), 
        2: (400, 400, 40, 80)
    }
    
    result = checker.check_frame(mock_tracked)
    
    print("Result:", result)
    
    # Assertions
    assert result["violation_count"] == 1
    assert result["violating_ids"] == {0, 1}
    print("Smoke test passed!")
