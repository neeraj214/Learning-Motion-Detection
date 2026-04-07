import numpy as np
from collections import OrderedDict

class CentroidTracker:
    def __init__(self, max_disappeared=40):
        """
        Initialize the tracker with internal state.
        
        Args:
            max_disappeared (int): Number of consecutive frames an object can be absent 
                                 before being deregistered.
        """
        self.next_id = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.max_disappeared = max_disappeared

    def register(self, centroid: np.ndarray) -> None:
        """Adds a new object to track."""
        self.objects[self.next_id] = centroid
        self.disappeared[self.next_id] = 0
        self.next_id += 1

    def deregister(self, object_id: int) -> None:
        """Removes an object from tracking."""
        if object_id in self.objects:
            del self.objects[object_id]
            del self.disappeared[object_id]

    def update(self, boxes: list[tuple[int, int, int, int]]) -> dict[int, np.ndarray]:
        """
        Updates the tracker with new bounding boxes from a frame.
        
        Args:
            boxes (list[tuple]): List of (x, y, w, h) bounding boxes.
        
        Returns:
            dict: Persistent object IDs mapped to their current centroids.
        """
        # --- Handle empty detections ---
        if not boxes:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects

        # --- Compute centroids for input boxes ---
        input_centroids = np.zeros((len(boxes), 2), dtype="int")
        for (i, (x, y, w, h)) in enumerate(boxes):
            cx = x + w // 2
            cy = y + h // 2
            input_centroids[i] = (cx, cy)

        # --- Initial tracking if no objects exist ---
        if len(self.objects) == 0:
            for centroid in input_centroids:
                self.register(centroid)
            return self.objects

        # --- Match existing objects to new centroids ---
        object_ids = list(self.objects.keys())
        object_centroids = np.array(list(self.objects.values()))

        # Build distance matrix (shape: num_tracked, num_input)
        # Using pure numpy broadcasting to calculate Euclidean distance matrix
        # (Fulfills 'numpy only' while being equivalent to scipy.spatial.distance.cdist)
        # D[i, j] = distance(object_centroids[i], input_centroids[j])
        D = np.linalg.norm(object_centroids[:, np.newaxis] - input_centroids, axis=2)

        # To perform the greedy matching:
        # Sort rows by minimum distance (closest existing object first)
        rows = D.min(axis=1).argsort()
        # Find the column index for each row (the best input centroid match)
        cols = D.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()

        for (row, col) in zip(rows, cols):
            # Skip if row or col already matched
            if row in used_rows or col in used_cols:
                continue
            
            # Distance threshold of 80px: if best match is too far, skip.
            if D[row, col] > 80:
                continue

            # Matched pair: update centroid and reset disappeared count
            object_id = object_ids[row]
            self.objects[object_id] = input_centroids[col]
            self.disappeared[object_id] = 0

            # Mark indices as used
            used_rows.add(row)
            used_cols.add(col)

        # --- Handle unmatched objects & disappearances ---
        unused_rows = set(range(0, D.shape[0])).difference(used_rows)
        for row in unused_rows:
            object_id = object_ids[row]
            self.disappeared[object_id] += 1
            if self.disappeared[object_id] > self.max_disappeared:
                self.deregister(object_id)

        # --- Register new objects from unused input centroids ---
        unused_cols = set(range(0, D.shape[1])).difference(used_cols)
        for col in unused_cols:
            self.register(input_centroids[col])

        return self.objects

if __name__ == "__main__":
    # --- SMOKE TEST ---
    print("[INFO] Starting CentroidTracker smoke test...")
    tracker = CentroidTracker(max_disappeared=40)
    
    # Frame 1: Three initial people
    print("\n[FRAME 1] Detections: 3 new objects")
    f1_boxes = [(10, 10, 50, 50), (200, 200, 40, 40), (400, 50, 60, 60)]
    objects = tracker.update(f1_boxes)
    for obj_id, centroid in objects.items():
        print(f"ID {obj_id}: {centroid}")

    # Frame 2: Objects moved slightly
    print("\n[FRAME 2] Movement: IDs should persist")
    f2_boxes = [(15, 12, 50, 50), (210, 205, 40, 40), (410, 55, 60, 60)]
    objects = tracker.update(f2_boxes)
    for obj_id, centroid in objects.items():
        print(f"ID {obj_id}: {centroid}")

    # Frame 3: One object disappeared
    print("\n[FRAME 3] 1 object gone: IDs for remaining 2 should persist")
    f3_boxes = [(20, 15, 52, 52), (220, 210, 40, 40)]
    objects = tracker.update(f3_boxes)
    for obj_id, centroid in objects.items():
        print(f"ID {obj_id}: {centroid}")
