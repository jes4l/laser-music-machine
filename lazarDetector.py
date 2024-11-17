import cv2
import numpy as np
from scipy.spatial import distance
from scipy.optimize import linear_sum_assignment
import pygame
import time

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


# Define a function to dynamically calculate the red color range in HSV
def dynamic_red_range(frame):
    """
    Dynamically calculates the red color range in HSV.
    Enhances the detection by equalizing and analyzing the hue channel.
    """
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Apply CLAHE to the Hue channel to improve contrast
    hue_channel = hsv_frame[:, :, 0]
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    hue_channel = clahe.apply(hue_channel)

    # Compute the histogram of the Hue channel
    hist = cv2.calcHist([hue_channel], [0], None, [180], [0, 180])
    hist = cv2.normalize(hist, hist).flatten()

    # Identify peaks in the histogram corresponding to red hues
    lower_peak = np.argmax(hist[:20])  # Hue 0-20 (lower red)
    upper_peak = np.argmax(hist[150:]) + 150  # Hue 150-180 (upper red)

    # Dynamically set lower and upper bounds
    lower_red = max(0, lower_peak - 10)
    upper_red = min(179, upper_peak + 10)

    return np.array([lower_red, 100, 100]), np.array([upper_red, 255, 255])


class ObjectTracker:
    def __init__(self, max_distance=30, max_objects=6, debounce_time=0.3):
        self.max_distance = max_distance
        self.max_objects = max_objects
        self.tracked_points = [None] * max_objects
        self.object_ids = list(range(1, max_objects + 1))
        self.initial_positions = [None] * max_objects
        self.initialized = False
        self.played_flags = [False] * max_objects
        self.last_played_time = [0] * max_objects
        self.debounce_time = debounce_time  # Reduced debounce time

    def update(self, detected_points):
        if not detected_points:
            self.played_flags = [False] * self.max_objects
            return self.tracked_points

        detected_points.sort(key=lambda p: p[0])

        if not self.initialized and len(detected_points) >= self.max_objects:
            self.tracked_points = detected_points[: self.max_objects]
            self.initial_positions = detected_points[: self.max_objects]
            self.initialized = True

        assigned = [False] * len(detected_points)
        updated_points = [None] * self.max_objects
        cost_matrix = np.full((self.max_objects, len(detected_points)), np.inf)

        for i, tracked_point in enumerate(self.tracked_points):
            if tracked_point is not None:
                for j, detected_point in enumerate(detected_points):
                    if not assigned[j]:
                        cost_matrix[i, j] = distance.euclidean(
                            tracked_point, detected_point
                        )

        cost_matrix[cost_matrix == np.inf] = 1e6
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        for i, j in zip(row_ind, col_ind):
            if cost_matrix[i, j] < self.max_distance:
                updated_points[i] = detected_points[j]
                assigned[j] = True
                current_time = time.time()
                if not self.played_flags[i] and (
                    current_time - self.last_played_time[i] > self.debounce_time
                ):
                    try:
                        note_sounds[i].play()
                        print(
                            f"Playing sound for object ID {self.object_ids[i]}: Note {chr(65 + i)}"
                        )
                    except Exception as e:
                        print(
                            f"Error playing sound for object ID {self.object_ids[i]}: {e}"
                        )
                    self.played_flags[i] = True
                    self.last_played_time[i] = current_time

        for i in range(self.max_objects):
            if updated_points[i] is None:
                updated_points[i] = self.tracked_points[i]
                self.played_flags[i] = False

        return updated_points


# Instantiate object tracker
tracker = ObjectTracker(max_distance=30, max_objects=6)


def detect_red_objects(frame):
    """
    Detects a single red object in each of 6 vertical segments of a defined ROI.
    Improves accuracy using advanced preprocessing and validation.
    """
    # Define the region of interest (ROI)
    stripe_top, stripe_bottom, stripe_left, stripe_right = 250, 340, 5, 630
    stripe_width = stripe_right - stripe_left
    segment_width = stripe_width // 6  # Width of each vertical segment

    # Get the dynamic red range for the stripe region
    stripe_roi = frame[stripe_top:stripe_bottom, stripe_left:stripe_right]
    LOWER_RED, UPPER_RED = dynamic_red_range(stripe_roi)

    # Convert the full frame to HSV and apply the mask to the ROI
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    red_mask = cv2.inRange(hsv_frame, LOWER_RED, UPPER_RED)

    # Preprocessing for better detection
    red_mask = cv2.GaussianBlur(red_mask, (5, 5), 0)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    red_mask = cv2.dilate(red_mask, np.ones((3, 3), np.uint8), iterations=1)

    detected_points = []

    # Process each vertical segment separately
    for i in range(6):  # Loop over 6 segments
        segment_left = stripe_left + i * segment_width
        segment_right = segment_left + segment_width

        # Mask out everything outside the current segment
        segment_mask = np.zeros_like(red_mask)
        segment_mask[stripe_top:stripe_bottom, segment_left:segment_right] = red_mask[
            stripe_top:stripe_bottom, segment_left:segment_right
        ]

        # Detect contours in the current segment
        contours, _ = cv2.findContours(
            segment_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        # Select a single red source per segment
        largest_contour = None
        max_area = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 10000:  # Minimum and maximum area thresholds
                if area > max_area:
                    max_area = area
                    largest_contour = contour

        # If a valid contour is found, calculate its center
        if largest_contour is not None:
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                detected_points.append((cX, cY))

    # Update the tracker with detected points
    tracked_points = tracker.update(detected_points)

    # Visualize the region of interest (draw border)
    cv2.rectangle(
        frame,
        (stripe_left, stripe_top),  # Top-left corner of the stripe
        (stripe_right, stripe_bottom),  # Bottom-right corner of the stripe
        (255, 0, 0),  # Blue color for the border
        2,  # Thickness of the border
    )

    # Draw segment borders
    for i in range(1, 6):  # Draw lines between the 6 vertical segments
        segment_line_x = stripe_left + i * segment_width
        cv2.line(
            frame,
            (segment_line_x, stripe_top),
            (segment_line_x, stripe_bottom),
            (0, 255, 0),  # Green line
            1,
        )

    # Visualize tracked points
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

    # Dynamically detect and track red objects only in the stripe
    processed_frame = detect_red_objects(frame)

    # Show the results
    cv2.imshow("Red Object Detection", processed_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
