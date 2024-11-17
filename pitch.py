import cv2
import numpy as np
import mediapipe as mp
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2)
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(1)

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])

    mask = cv2.inRange(hsv_frame, lower_green, upper_green)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    green_points = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if 100 < area < 2000:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                green_points.append((cx, cy))

    if len(green_points) == 2:
        start_point = green_points[0]
        end_point = green_points[1]
        cv2.line(frame, start_point, end_point, (0, 255, 0), 2)
        line_length = np.linalg.norm(np.array(start_point) - np.array(end_point))

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            index_finger_tip = hand_landmarks.landmark[8]
            index_x = int(index_finger_tip.x * frame.shape[1])
            index_y = int(index_finger_tip.y * frame.shape[0])

            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            if len(green_points) == 2:
                vector_line = np.array(end_point) - np.array(start_point)
                vector_index = np.array([index_x, index_y]) - np.array(start_point)
                projection_length = np.dot(vector_index, vector_line) / np.linalg.norm(
                    vector_line
                )
                percentage = (projection_length / line_length) * 100
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
                volume.SetMasterVolumeLevelScalar(percentage / 100, None)

    cv2.imshow("Hand and Line Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
