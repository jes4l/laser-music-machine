import cv2
import numpy as np
from scipy.spatial import distance

# Define the red color range for object detection in HSV
LOWER_RED = np.array([150, 100, 200])
UPPER_RED = np.array([170, 255, 255])


class ObjectTracker:
    def __init__(self, max_distance=30, max_objects=8):
        self.max_distance = max_distance
        self.max_objects = max_objects
        self.tracked_points = [None] * max_objects  # Fixed size list
        self.object_ids = list(range(1, max_objects + 1))  # IDs 1 to max_objects
        self.initial_positions = [None] * max_objects  # Reference initial positions

    def update(self, detected_points):
        # Map each detected point to a position in the tracked points list
        assigned = [False] * len(detected_points)
        updated_points = [None] * self.max_objects

        # Match detected points to existing tracked points
        for i, tracked_point in enumerate(self.tracked_points):
            if tracked_point is not None:
                distances = [
                    (
                        distance.euclidean(tracked_point, dp)
                        if not assigned[j]
                        else float("inf")
                    )
                    for j, dp in enumerate(detected_points)
                ]
                if distances and min(distances) < self.max_distance:
                    idx = distances.index(min(distances))
                    updated_points[i] = detected_points[idx]
                    assigned[idx] = True

        # Assign new detected points to empty slots
        for i, tracked_point in enumerate(updated_points):
            if tracked_point is None:  # Empty slot
                for j, detected_point in enumerate(detected_points):
                    if not assigned[j]:
                        initial_distance = (
                            distance.euclidean(
                                self.initial_positions[i], detected_point
                            )
                            if self.initial_positions[i] is not None
                            else float("inf")
                        )
                        if (
                            initial_distance < self.max_distance
                            or self.tracked_points[i] is None
                        ):
                            updated_points[i] = detected_point
                            assigned[j] = True
                            break

        # Update initial positions if the slot was newly filled
        for i in range(self.max_objects):
            if updated_points[i] is not None and self.tracked_points[i] is None:
                self.initial_positions[i] = updated_points[i]

        self.tracked_points = updated_points

        # Debug: Print current state
        print(f"Tracked Points: {self.tracked_points}")
        print(f"Object IDs: {self.object_ids}")

        return updated_points


# Instantiate object tracker
tracker = ObjectTracker(max_distance=30, max_objects=8)


def detect_red_objects(frame):
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    red_mask = cv2.inRange(hsv_frame, LOWER_RED, UPPER_RED)
    red_mask = cv2.GaussianBlur(red_mask, (5, 5), 0)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    contours, _ = cv2.findContours(red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    detected_points = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 100:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                detected_points.append((cX, cY))

    tracked_points = tracker.update(detected_points)

    for i, point in enumerate(tracked_points):
        if point is not None:
            x, y = point
            cv2.circle(frame, (int(x), int(y)), 10, (0, 255, 0), -1)
            cv2.putText(
                frame,
                f"{tracker.object_ids[i]}",
                (int(x) + 10, int(y) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
            )

    return frame


cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    processed_frame = detect_red_objects(frame)
    cv2.imshow("red Object Detection", processed_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
