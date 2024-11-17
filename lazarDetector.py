import cv2
import numpy as np
from scipy.spatial import distance
from scipy.optimize import linear_sum_assignment
import pygame
import time
import csv
import subprocess

pygame.mixer.init()

note_sounds = [
    pygame.mixer.Sound("A.MP3"),
    pygame.mixer.Sound("B.MP3"),
    pygame.mixer.Sound("C.MP3"),
    pygame.mixer.Sound("D.MP3"),
    pygame.mixer.Sound("E.MP3"),
    pygame.mixer.Sound("F.MP3"),
]

recording_data = []


def dynamic_red_range(frame):
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hue_channel = hsv_frame[:, :, 0]
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    hue_channel = clahe.apply(hue_channel)

    hist = cv2.calcHist([hue_channel], [0], None, [180], [0, 180])
    hist = cv2.normalize(hist, hist).flatten()

    lower_peak = np.argmax(hist[:20])  # Hue 0-20 (lower red)
    upper_peak = np.argmax(hist[150:]) + 150  # Hue 150-180 (upper red)

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
        self.debounce_time = debounce_time

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
                        recording_data.append((time.time(), chr(65 + i)))
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


tracker = ObjectTracker(max_distance=30, max_objects=6)


def detect_red_objects(frame):
    stripe_top, stripe_bottom, stripe_left, stripe_right = 250, 340, 5, 630
    stripe_width = stripe_right - stripe_left
    segment_width = stripe_width // 6

    stripe_roi = frame[stripe_top:stripe_bottom, stripe_left:stripe_right]
    LOWER_RED, UPPER_RED = dynamic_red_range(stripe_roi)

    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    red_mask = cv2.inRange(hsv_frame, LOWER_RED, UPPER_RED)

    red_mask = cv2.GaussianBlur(red_mask, (5, 5), 0)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    red_mask = cv2.dilate(red_mask, np.ones((3, 3), np.uint8), iterations=1)

    detected_points = []

    for i in range(6):
        segment_left = stripe_left + i * segment_width
        segment_right = segment_left + segment_width

        segment_mask = np.zeros_like(red_mask)
        segment_mask[stripe_top:stripe_bottom, segment_left:segment_right] = red_mask[
            stripe_top:stripe_bottom, segment_left:segment_right
        ]

        contours, _ = cv2.findContours(
            segment_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        largest_contour = None
        max_area = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 10000:
                if area > max_area:
                    max_area = area
                    largest_contour = contour

        if largest_contour is not None:
            M = cv2.moments(largest_contour)
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

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):  # Trigger exit when 'q' is pressed
        # Save recording data to CSV
        with open("recording.csv", "w", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(["Time", "Note"])
            csvwriter.writerows(recording_data)
        # Run end.py
        subprocess.run(["python", "end.py"])
        break

    if cv2.getWindowProperty("Red Object Detection", cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()
