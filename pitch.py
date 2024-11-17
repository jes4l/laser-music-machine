import cv2
import numpy as np
import mediapipe as mp

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2)
mp_drawing = mp.solutions.drawing_utils

# Initialize video capture from the camera
cap = cv2.VideoCapture(1)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Convert the frame to HSV color space
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define the HSV range for detecting green color
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])

    # Create a binary mask for green color
    mask = cv2.inRange(hsv_frame, lower_green, upper_green)

    # Find contours in the masked image
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Store the centers of the two largest green contours
    green_points = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if 100 < area < 2000:  # Adjust area range as needed
            # Get the center of the contour
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                green_points.append((cx, cy))

    # If we have two green points, draw a line between them
    if len(green_points) == 2:
        start_point = green_points[0]
        end_point = green_points[1]
        cv2.line(frame, start_point, end_point, (0, 255, 0), 2)

        # Calculate the length of the line for percentage calculation
        line_length = np.linalg.norm(np.array(start_point) - np.array(end_point))

    # Convert the frame to RGB for MediaPipe and process
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    # Draw hand landmarks and check position relative to the line
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            # Get the coordinates of the index finger tip (landmark 8)
            index_finger_tip = hand_landmarks.landmark[8]
            index_x = int(index_finger_tip.x * frame.shape[1])
            index_y = int(index_finger_tip.y * frame.shape[0])

            # Draw the hand landmarks
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Check the position of the index finger tip relative to the line
            if len(green_points) == 2:
                # Project the index finger tip point onto the line and calculate percentage
                vector_line = np.array(end_point) - np.array(start_point)
                vector_index = np.array([index_x, index_y]) - np.array(start_point)
                projection_length = np.dot(vector_index, vector_line) / np.linalg.norm(
                    vector_line
                )
                percentage = (projection_length / line_length) * 100

                # Clamp the percentage between 0 and 100
                percentage = max(0, min(100, percentage))
                cv2.putText(
                    frame,
                    f"{int(percentage)}%",
                    (index_x + 10, index_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 0, 0),
                    2,
                )

    # Display the frame
    cv2.imshow("Hand and Line Detection", frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release the video capture and close windows
cap.release()
cv2.destroyAllWindows()
