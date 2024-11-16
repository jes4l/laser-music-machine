import cv2
import numpy as np
from scipy.spatial import distance
from scipy.optimize import linear_sum_assignment
import pygame

# Initialize the pygame mixer
pygame.mixer.init()

# Load sounds for each note
note_sounds = [
    pygame.mixer.Sound("A.MP3"),
    pygame.mixer.Sound("B.MP3"),
    pygame.mixer.Sound("C.MP3"),
    pygame.mixer.Sound("D.MP3"),
    pygame.mixer.Sound("E.MP3"),
    pygame.mixer.Sound("F.MP3"),
]

# Define the red color range for object detection in HSV
LOWER_RED = np.array([150, 100, 200])
UPPER_RED = np.array([170, 255, 255])


class ObjectTracker:
    def __init__(self, max_distance=30, max_objects=6):
        self.max_distance = max_distance
        self.max_objects = max_objects
        self.tracked_points = [None] * max_objects  # Fixed size list
        self.object_ids = list(range(1, max_objects + 1))  # IDs 1 to max_objects
        self.initial_positions = [None] * max_objects  # Reference initial positions
        self.initialized = False  # Flag to check if the initial positions are set
        self.played_flags = [False] * max_objects  # Flags to manage note playing

    def update(self, detected_points):
        # Sort detected points by their x-coordinate for left-to-right order
        detected_points.sort(key=lambda p: p[0])

        if not self.initialized and len(detected_points) >= self.max_objects:
            # Set the initial positions and tracked points when first detected
            self.tracked_points = detected_points[: self.max_objects]
            self.initial_positions = detected_points[: self.max_objects]
            self.initialized = True

        assigned = [False] * len(detected_points)
        updated_points = [None] * self.max_objects

        # Create a cost matrix for the Hungarian algorithm
        cost_matrix = np.full((self.max_objects, len(detected_points)), np.inf)

        for i in range(self.max_objects):
            tracked_point = self.tracked_points[i]
            if tracked_point is not None:
                for j, detected_point in enumerate(detected_points):
                    if not assigned[j]:
                        cost_matrix[i, j] = distance.euclidean(
                            tracked_point, detected_point
                        )

        # Replace inf values with a large number
        cost_matrix[cost_matrix == np.inf] = 1e6

        # Solve the assignment problem using the Hungarian algorithm
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        for i, j in zip(row_ind, col_ind):
            if cost_matrix[i, j] < self.max_distance:
                updated_points[i] = detected_points[j]
                assigned[j] = True

                # Reset the played flag if the object is detected again
                if not self.played_flags[i]:
                    note_sounds[i].play()  # Play the sound
                    self.played_flags[i] = True

        # Assign new detected points to empty slots in order
        for i in range(self.max_objects):
            if updated_points[i] is None:  # Empty slot
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

        # Ensure IDs do not change order
        for i in range(self.max_objects):
            if updated_points[i] is not None and self.tracked_points[i] is None:
                self.initial_positions[i] = updated_points[i]

        # Check for objects that have moved away and reset their played flags
        for i in range(self.max_objects):
            if updated_points[i] is None:
                self.played_flags[i] = False

        self.tracked_points = updated_points

        # Debug: Print current state
        print(f"Tracked Points: {self.tracked_points}")
        print(f"Object IDs: {self.object_ids}")

        return updated_points


# Instantiate object tracker
tracker = ObjectTracker(max_distance=30, max_objects=6)


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
    cv2.imshow("Red Object Detection", processed_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
