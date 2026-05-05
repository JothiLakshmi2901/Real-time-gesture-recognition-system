import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import pickle
import time
import pyperclip

# ===== LOAD MODEL =====
model = tf.keras.models.load_model("../../models/static_model.h5")
labels = pickle.load(open("../../models/static_labels.pkl", "rb"))

# ===== MEDIAPIPE =====
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

cap = cv2.VideoCapture(0)

# ===== CONFIG =====
THRESHOLD = 0.85
HOLD_TIME = 1.0
LOCK_TIME = 1.0
BACKSPACE_HOLD_TIME = 1.0

last_label = None
gesture_start_time = None
lock_until = 0

backspace_start_time = None
backspace_triggered = False

sentence = ""

print("🎥 Gesture prediction started")
print("Press 'q' to quit | 'c' to copy sentence")

# ===== MULTILINE TEXT FUNCTION =====
def draw_multiline_text(img, text, x, y, max_width, line_height):
    words = text.split(" ")
    line = ""
    y_offset = 0

    for word in words:
        test_line = line + word + " "
        (w, _), _ = cv2.getTextSize(
            test_line,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            2
        )

        if w > max_width:
            cv2.putText(
                img,
                line,
                (x, y + y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )
            line = word + " "
            y_offset += line_height
        else:
            line = test_line

    # last line
    cv2.putText(
        img,
        line,
        (x, y + y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

# ===== MAIN LOOP =====
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    current_time = time.time()
    display_label = "No Hand"

    if result.multi_hand_landmarks and current_time > lock_until:
        hand = result.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

        data = []
        for lm in hand.landmark:
            data.extend([lm.x, lm.y, lm.z])

        pred = model.predict(np.array([data]), verbose=0)[0]
        confidence = np.max(pred)
        class_id = np.argmax(pred)

        if confidence >= THRESHOLD:
            label = labels.inverse_transform([class_id])[0]
            accuracy = int(confidence * 100)
            display_label = f"{label} ({accuracy}%)"

            # ===== BACKSPACE LOGIC =====
            if label == "backspace":
                if backspace_start_time is None:
                    backspace_start_time = current_time

                elif (current_time - backspace_start_time >= BACKSPACE_HOLD_TIME) and not backspace_triggered:
                    if len(sentence.strip()) > 0:
                        words = sentence.strip().split(" ")
                        words = words[:-1]
                        sentence = " ".join(words) + " "
                    backspace_triggered = True
                    lock_until = current_time + LOCK_TIME

                last_label = None
                gesture_start_time = None

            else:
                backspace_start_time = None
                backspace_triggered = False

                # ===== NORMAL HOLD LOGIC =====
                if label == last_label:
                    if gesture_start_time is None:
                        gesture_start_time = current_time

                    elif current_time - gesture_start_time >= HOLD_TIME:
                        if label == ".":
                            sentence += ". "
                        elif label == "SPACE":
                            sentence += " "
                        else:
                            sentence += label + " "

                        last_label = None
                        gesture_start_time = None
                        lock_until = current_time + LOCK_TIME
                else:
                    last_label = label
                    gesture_start_time = current_time

        else:
            last_label = None
            gesture_start_time = None
            backspace_start_time = None
            backspace_triggered = False
    else:
        last_label = None
        gesture_start_time = None
        backspace_start_time = None
        backspace_triggered = False

    # ===== DIALOGUE BOX =====
    box_x, box_y, box_w, box_h = 20, 350, 600, 120

    cv2.rectangle(frame, (box_x, box_y),
                  (box_x + box_w, box_y + box_h),
                  (0, 0, 0), -1)

    cv2.rectangle(frame, (box_x, box_y),
                  (box_x + box_w, box_y + box_h),
                  (0, 255, 0), 2)

    cv2.putText(frame, "Sentence:",
                (box_x + 10, box_y + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 255, 0), 2)

    draw_multiline_text(
        frame,
        sentence.strip(),
        box_x + 10,
        box_y + 60,
        max_width=box_w - 20,
        line_height=30
    )

    # ===== CURRENT GESTURE =====
    cv2.putText(frame, f"Gesture: {display_label}",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1,
                (0, 255, 0), 2)

    cv2.imshow("Gesture Sentence Builder", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('c'):
        pyperclip.copy(sentence.strip())
        print("Sentence copied to clipboard")

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Prediction stopped")
