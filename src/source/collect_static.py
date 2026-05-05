import cv2
import mediapipe as mp
import csv
import os

LABEL = input("Enter static gesture label: ")
DATA_DIR = "../../data/static_data"
os.makedirs(DATA_DIR, exist_ok=True)

file_path = os.path.join(DATA_DIR, "static_data.csv")

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils   # for drawing points
hands = mp_hands.Hands(
    max_num_hands=2,   #allow two hands
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)

count = 0   # serial number

with open(file_path, "a", newline="") as f:
    writer = csv.writer(f)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]

            # Draw 21 landmarks
            mp_draw.draw_landmarks(
                frame,
                hand,
                mp_hands.HAND_CONNECTIONS
            )

            # Save landmark data
            row = []
            for lm in hand.landmark:
                row.extend([lm.x, lm.y, lm.z])
            row.append(LABEL)
            writer.writerow(row)

            count += 1
            print(f"Saved {count} → {LABEL}")

            # Show count on screen
            cv2.putText(
                frame,
                f"Samples: {count}",
                (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

        cv2.imshow("Static Gesture Capture", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
