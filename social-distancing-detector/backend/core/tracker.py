import numpy as np
from collections import OrderedDict

class CentroidTracker:
    def __init__(self, max_disappeared=40):
        """Initialize tracker with object IDs and centroids."""
        self.next_id = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.max_disappeared = max_disappeared

    def register(self, centroid: np.ndarray):
        """Register a new object."""
        self.objects[self.next_id] = centroid
        self.disappeared[self.next_id] = 0
        self.next_id += 1

    def deregister(self, object_id: int):
        """Deregister an existing object."""
        if object_id in self.objects:
            del self.objects[object_id]
            del self.disappeared[object_id]

    def update(self, boxes: list[tuple[int, int, int, int]]) -> dict[int, np.ndarray]:
        """
        Match detected bounding boxes to existing tracked objects.
        """
        # 1. If no boxes detected, increment disappeared counter for all
        if not boxes:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects

        # 2. Compute centroids for input boxes
        input_centroids = np.zeros((len(boxes), 2), dtype="int")
        for (i, (x, y, w, h)) in enumerate(boxes):
            input_centroids[i] = (x + w // 2, y + h // 2)

        # 3. If no objects tracked, register every input centroid
        if len(self.objects) == 0:
            for centroid in input_centroids:
                self.register(centroid)
            return self.objects

        # 4. Otherwise, calculate distances between objects and input centroids
        object_ids = list(self.objects.keys())
        object_centroids = list(self.objects.values())

        # Isolate scipy dependency (import inside method as requested)
        from scipy.spatial import distance as dist
        D = dist.cdist(np.array(object_centroids), input_centroids)

        # 5. Greedy matching logic
        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()

        for (row, col) in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue
            
            # Check if distance is too far (e.g., > 80px as requested)
            if D[row, col] > 80:
                continue

            # Update tracked object's centroid and reset disappeared count
            object_id = object_ids[row]
            self.objects[object_id] = input_centroids[col]
            self.disappeared[object_id] = 0

            used_rows.add(row)
            used_cols.add(col)

        # 6. For unused rows/objects, increment disappeared count
        unused_rows = set(range(0, D.shape[0])).difference(used_rows)
        for row in unused_rows:
            object_id = object_ids[row]
            self.disappeared[object_id] += 1
            if self.disappeared[object_id] > self.max_disappeared:
                self.deregister(object_id)

        # 7. For unused columns/centroids, register as new
        unused_cols = set(range(0, D.shape[1])).difference(used_cols)
        for col in unused_cols:
            self.register(input_centroids[col])

        return self.objects

if __name__ == "__main__":
    # Smoke test: simulates 3 "frames" of movement
    tracker = CentroidTracker()
    
    # Mock Frame 1: Two people detecteds
    print("[FRAME 1] Detected two items...")
    f1_boxes = [(10, 10, 50, 50), (200, 200, 40, 40)]
    objects = tracker.update(f1_boxes)
    print(f"Tracking: {objects}")

    # Mock Frame 2: Objects moved slightly
    print("[FRAME 2] Items moved...")
    f2_boxes = [(15, 12, 50, 50), (210, 205, 40, 40)]
    objects = tracker.update(f2_boxes)
    print(f"Tracking: {objects}")

    # Mock Frame 3: One object disappeared
    print("[FRAME 3] One item remains...")
    f3_boxes = [(20, 15, 52, 52)]
    objects = tracker.update(f3_boxes)
    print(f"Tracking: {objects}")
