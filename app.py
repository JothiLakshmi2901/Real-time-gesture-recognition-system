import os
import cv2
import numpy as np
import pickle
import tensorflow as tf
import mediapipe as mp
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import base64
from PIL import Image
import io
import tempfile
import threading
import time
from gtts import gTTS
import pygame
import pyttsx3
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# ===== AUDIO =====
pygame.mixer.init()

try:
    tts_engine = pyttsx3.init()
    tts_engine.setProperty("rate", 150)
    tts_engine.setProperty("volume", 0.9)
except Exception as e:
    print(f"Error initializing pyttsx3: {e}")
    tts_engine = None

# ===== GESTURE CLASSES =====
GESTURE_CLASSES = [
    'start_command', 'stop_command', 'speak_command',
    'backspace', 'bill', 'can', 'card', 'cash', 'curry', 'do', 'drink',
    'finished', 'food', 'get', 'have', 'here', 'I', 'is', 'less', 'meals', 'more', 'menu',
    'my', 'non-vegetarian', 'now', 'pay by', 'please', 'repeat', 'rice', 'spicy',
    'thankyou', 'this', 'today', 'vegetarian', 'want', 'water', 'what', 'you'
]

# ===== DISPLAY WORDS =====
GESTURE_MEANINGS = {
    'backspace': 'Delete Last Word',
    'bill': 'Bill',
    'can': 'Can',
    'card': 'Card',
    'cash': 'Cash',
    'curry': 'Curry',
    'do': 'Do',
    'drink': 'Drink',
    'finished': 'Finished',
    'food': 'Food',
    'get': 'Get',
    'have': 'Have',
    'here': 'Here',
    'I': 'I',
    'is': 'Is',
    'less': 'Less',
    'meals': 'Meals',
    'menu': 'Menu',
    'more': 'More',
    'my': 'My',
    'non-vegetarian': 'Non-Vegetarian',
    'now': 'Now',
    'pay by': 'Pay By',
    'please': 'Please',
    'repeat': 'Repeat',
    'rice': 'Rice',
    'spicy': 'Spicy',
    'thankyou': 'Thankyou',
    'this': 'This',
    'today': 'Today',
    'vegetarian': 'Vegetarian',
    'want': 'Want',
    'water': 'Water',
    'what': 'What',
    'you': 'You',
    'start_command': 'Start New Sentence',
    'stop_command': 'Stop Prediction',
    'speak_command': 'Speak Sentence'
}

# ===== MODEL LOAD =====
try:
    model = tf.keras.models.load_model("models/static_model.h5")
    label_encoder = pickle.load(open("models/static_labels.pkl", "rb"))
    print("✅ Model and labels loaded successfully")
    print(f"Model expects {model.input_shape[1]} features")
    print(f"Classes in model: {label_encoder.classes_}")

    model_classes = set(label_encoder.classes_)
    expected_classes = set(GESTURE_CLASSES)

    if model_classes != expected_classes:
        print("⚠️ Warning: Model classes don't match expected classes!")
        print(f"Missing from model: {expected_classes - model_classes}")
        print(f"Extra in model: {model_classes - expected_classes}")

except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None
    label_encoder = None

# ===== MEDIAPIPE =====
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# ===== CONFIG =====
THRESHOLD = 0.85
HOLD_TIME = 0.5
LOCK_TIME = 0.5
BACKSPACE_HOLD_TIME = 0.5
COMMAND_HOLD_TIME = 0.5

# ===== GLOBAL STATE =====
last_label = None
gesture_start_time = None
lock_until = 0

backspace_start_time = None
backspace_triggered = False

sentence = ""
recognized_words = []

speak_start_time = None
speak_triggered = False

start_start_time = None
start_triggered = False

stop_start_time = None
stop_triggered = False

# app modes:
# waiting   -> waiting for start command
# listening -> gesture prediction active
# stopped   -> prediction stopped, waiting for speak command or new start
app_mode = "waiting"

# backend tts state
tts_playing = False
tts_lock = threading.Lock()


def load_gesture_mapping():
    mapping = []
    for gesture in GESTURE_CLASSES:
        mapping.append({
            "gesture": gesture,
            "image": f"images/gestures/{gesture}.png"
        })
    return mapping


gesture_mapping = load_gesture_mapping()


def text_to_speech(text):
    global tts_playing

    with tts_lock:
        tts_playing = True

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_filename = fp.name

        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(temp_filename)

        pygame.mixer.music.load(temp_filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)

        pygame.mixer.music.unload()

        if os.path.exists(temp_filename):
            os.unlink(temp_filename)

    except Exception as e:
        print(f"Error with gTTS: {e}")
        try:
            if tts_engine:
                tts_engine.say(text)
                tts_engine.runAndWait()
        except Exception as e2:
            print(f"Error with pyttsx3 fallback: {e2}")

    finally:
        with tts_lock:
            tts_playing = False


@app.route("/")
def index():
    return render_template("detect.html", gestures=gesture_mapping)


@app.route("/detect")
def detect():
    return render_template("detect.html", gestures=gesture_mapping)


@app.route("/process_frame", methods=["POST"])
def process_frame():
    global last_label, gesture_start_time, lock_until
    global backspace_start_time, backspace_triggered
    global sentence, recognized_words
    global speak_start_time, speak_triggered
    global start_start_time, start_triggered
    global stop_start_time, stop_triggered
    global app_mode, tts_playing

    if model is None or label_encoder is None:
        return jsonify({
            "success": False,
            "error": "Model not loaded properly",
            "tts_playing": tts_playing
        })

    try:
        req_data = request.json or {}
        image_uri = req_data.get("image", "")

        if not image_uri:
            return jsonify({
                "success": False,
                "error": "No image received",
                "hand_detected": False,
                "gesture_recognized": False,
                "current_word": "",
                "word": None,
                "sentence": sentence.strip(),
                "all_words": recognized_words,
                "app_mode": app_mode,
                "action": "none",
                "tts_playing": tts_playing
            })

        image_data = image_uri.split(",")[1]
        image = Image.open(io.BytesIO(base64.b64decode(image_data))).convert("RGB")

        frame = np.array(image)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        result = hands.process(rgb)

        current_time = time.time()
        recognized_word = None
        confidence_score = 0.0
        current_word = ""
        action = "none"

        if not result.multi_hand_landmarks:
            last_label = None
            gesture_start_time = None
            backspace_start_time = None
            backspace_triggered = False
            speak_start_time = None
            speak_triggered = False
            start_start_time = None
            start_triggered = False
            stop_start_time = None
            stop_triggered = False

            return jsonify({
                "success": True,
                "hand_detected": False,
                "gesture_recognized": False,
                "current_word": "",
                "word": None,
                "confidence": 0,
                "sentence": sentence.strip(),
                "all_words": recognized_words,
                "app_mode": app_mode,
                "action": action,
                "tts_playing": tts_playing
            })

        hand = result.multi_hand_landmarks[0]

        landmark_data = []
        for lm in hand.landmark:
            landmark_data.extend([lm.x, lm.y, lm.z])

        if len(landmark_data) != 63:
            landmark_data = landmark_data[:63] if len(landmark_data) > 63 else landmark_data + [0] * (63 - len(landmark_data))

        pred = model.predict(np.array([landmark_data]), verbose=0)[0]
        confidence = float(np.max(pred))
        class_id = int(np.argmax(pred))

        if confidence < THRESHOLD:
            last_label = None
            gesture_start_time = None
            backspace_start_time = None
            backspace_triggered = False
            speak_start_time = None
            speak_triggered = False
            start_start_time = None
            start_triggered = False
            stop_start_time = None
            stop_triggered = False

            return jsonify({
                "success": True,
                "hand_detected": True,
                "gesture_recognized": False,
                "current_word": "",
                "word": None,
                "confidence": round(confidence * 100, 2),
                "sentence": sentence.strip(),
                "all_words": recognized_words,
                "app_mode": app_mode,
                "action": action,
                "tts_playing": tts_playing
            })

        label = label_encoder.inverse_transform([class_id])[0]
        confidence_score = confidence
        current_word = label

        if current_time <= lock_until:
            return jsonify({
                "success": True,
                "hand_detected": True,
                "gesture_recognized": True,
                "current_word": current_word,
                "word": None,
                "confidence": round(confidence_score * 100, 2),
                "sentence": sentence.strip(),
                "all_words": recognized_words,
                "app_mode": app_mode,
                "action": action,
                "tts_playing": tts_playing
            })

        if app_mode == "waiting":
            if label == "start_command":
                backspace_start_time = None
                backspace_triggered = False
                speak_start_time = None
                speak_triggered = False
                stop_start_time = None
                stop_triggered = False

                if start_start_time is None:
                    start_start_time = current_time

                elif (current_time - start_start_time >= COMMAND_HOLD_TIME) and not start_triggered:
                    sentence = ""
                    recognized_words = []
                    app_mode = "listening"
                    recognized_word = "Start New Sentence"
                    action = "started"

                    start_triggered = True
                    lock_until = current_time + LOCK_TIME

                last_label = None
                gesture_start_time = None

                return jsonify({
                    "success": True,
                    "hand_detected": True,
                    "gesture_recognized": True,
                    "current_word": current_word,
                    "word": recognized_word,
                    "confidence": round(confidence_score * 100, 2),
                    "sentence": sentence.strip(),
                    "all_words": recognized_words,
                    "app_mode": app_mode,
                    "action": action,
                    "tts_playing": tts_playing
                })

            else:
                start_start_time = None
                start_triggered = False
                return jsonify({
                    "success": True,
                    "hand_detected": True,
                    "gesture_recognized": True,
                    "current_word": current_word,
                    "word": None,
                    "confidence": round(confidence_score * 100, 2),
                    "sentence": sentence.strip(),
                    "all_words": recognized_words,
                    "app_mode": app_mode,
                    "action": "waiting_for_start",
                    "tts_playing": tts_playing
                })

        if app_mode == "stopped":
            if label == "start_command":
                speak_start_time = None
                speak_triggered = False
                backspace_start_time = None
                backspace_triggered = False
                stop_start_time = None
                stop_triggered = False

                if start_start_time is None:
                    start_start_time = current_time

                elif (current_time - start_start_time >= COMMAND_HOLD_TIME) and not start_triggered:
                    sentence = ""
                    recognized_words = []
                    app_mode = "listening"
                    recognized_word = "Start New Sentence"
                    action = "started"

                    start_triggered = True
                    lock_until = current_time + LOCK_TIME

                last_label = None
                gesture_start_time = None

                return jsonify({
                    "success": True,
                    "hand_detected": True,
                    "gesture_recognized": True,
                    "current_word": current_word,
                    "word": recognized_word,
                    "confidence": round(confidence_score * 100, 2),
                    "sentence": sentence.strip(),
                    "all_words": recognized_words,
                    "app_mode": app_mode,
                    "action": action,
                    "tts_playing": tts_playing
                })
            else:
                start_start_time = None
                start_triggered = False

            if label == "speak_command":
                if speak_start_time is None:
                    speak_start_time = current_time

                elif (current_time - speak_start_time >= COMMAND_HOLD_TIME) and not speak_triggered:
                    if sentence.strip():
                        thread = threading.Thread(target=text_to_speech, args=(sentence.strip(),))
                        thread.daemon = True
                        thread.start()
                        recognized_word = "Speak Sentence"
                        action = "sentence_spoken"
                    else:
                        action = "empty_sentence"

                    speak_triggered = True
                    lock_until = current_time + LOCK_TIME

                last_label = None
                gesture_start_time = None

                return jsonify({
                    "success": True,
                    "hand_detected": True,
                    "gesture_recognized": True,
                    "current_word": current_word,
                    "word": recognized_word,
                    "confidence": round(confidence_score * 100, 2),
                    "sentence": sentence.strip(),
                    "all_words": recognized_words,
                    "app_mode": app_mode,
                    "action": action,
                    "tts_playing": tts_playing
                })
            else:
                speak_start_time = None
                speak_triggered = False

            return jsonify({
                "success": True,
                "hand_detected": True,
                "gesture_recognized": True,
                "current_word": current_word,
                "word": None,
                "confidence": round(confidence_score * 100, 2),
                "sentence": sentence.strip(),
                "all_words": recognized_words,
                "app_mode": app_mode,
                "action": "waiting_for_speak",
                "tts_playing": tts_playing
            })

        if label == "start_command":
            backspace_start_time = None
            backspace_triggered = False
            speak_start_time = None
            speak_triggered = False
            stop_start_time = None
            stop_triggered = False

            if start_start_time is None:
                start_start_time = current_time

            elif (current_time - start_start_time >= COMMAND_HOLD_TIME) and not start_triggered:
                sentence = ""
                recognized_words = []
                app_mode = "listening"
                recognized_word = "Start New Sentence"
                action = "started"

                start_triggered = True
                lock_until = current_time + LOCK_TIME

            last_label = None
            gesture_start_time = None

            return jsonify({
                "success": True,
                "hand_detected": True,
                "gesture_recognized": True,
                "current_word": current_word,
                "word": recognized_word,
                "confidence": round(confidence_score * 100, 2),
                "sentence": sentence.strip(),
                "all_words": recognized_words,
                "app_mode": app_mode,
                "action": action,
                "tts_playing": tts_playing
            })
        else:
            start_start_time = None
            start_triggered = False

        if label == "stop_command":
            backspace_start_time = None
            backspace_triggered = False
            speak_start_time = None
            speak_triggered = False

            if stop_start_time is None:
                stop_start_time = current_time

            elif (current_time - stop_start_time >= COMMAND_HOLD_TIME) and not stop_triggered:
                app_mode = "stopped"
                recognized_word = "Stop Prediction"
                action = "stopped"

                stop_triggered = True
                lock_until = current_time + LOCK_TIME

            last_label = None
            gesture_start_time = None

            return jsonify({
                "success": True,
                "hand_detected": True,
                "gesture_recognized": True,
                "current_word": current_word,
                "word": recognized_word,
                "confidence": round(confidence_score * 100, 2),
                "sentence": sentence.strip(),
                "all_words": recognized_words,
                "app_mode": app_mode,
                "action": action,
                "tts_playing": tts_playing
            })
        else:
            stop_start_time = None
            stop_triggered = False

        if label == "speak_command":
            backspace_start_time = None
            backspace_triggered = False

            if speak_start_time is None:
                speak_start_time = current_time

            elif (current_time - speak_start_time >= COMMAND_HOLD_TIME) and not speak_triggered:
                if sentence.strip():
                    thread = threading.Thread(target=text_to_speech, args=(sentence.strip(),))
                    thread.daemon = True
                    thread.start()
                    recognized_word = "Speak Sentence"
                    action = "sentence_spoken"
                else:
                    action = "empty_sentence"

                speak_triggered = True
                lock_until = current_time + LOCK_TIME

            last_label = None
            gesture_start_time = None

            return jsonify({
                "success": True,
                "hand_detected": True,
                "gesture_recognized": True,
                "current_word": current_word,
                "word": recognized_word,
                "confidence": round(confidence_score * 100, 2),
                "sentence": sentence.strip(),
                "all_words": recognized_words,
                "app_mode": app_mode,
                "action": action,
                "tts_playing": tts_playing
            })
        else:
            speak_start_time = None
            speak_triggered = False

        if label == "backspace":
            if backspace_start_time is None:
                backspace_start_time = current_time

            elif (current_time - backspace_start_time >= BACKSPACE_HOLD_TIME) and not backspace_triggered:
                if len(sentence.strip()) > 0:
                    words = sentence.strip().split()
                    words = words[:-1]
                    sentence = " ".join(words).strip()
                    if sentence:
                        sentence += " "
                    recognized_words = words[-10:] if words else []

                recognized_word = "Delete Last Word"
                action = "backspace"
                backspace_triggered = True
                lock_until = current_time + LOCK_TIME

            last_label = None
            gesture_start_time = None

            return jsonify({
                "success": True,
                "hand_detected": True,
                "gesture_recognized": True,
                "current_word": current_word,
                "word": recognized_word,
                "confidence": round(confidence_score * 100, 2),
                "sentence": sentence.strip(),
                "all_words": recognized_words,
                "app_mode": app_mode,
                "action": action,
                "tts_playing": tts_playing
            })
        else:
            backspace_start_time = None
            backspace_triggered = False

        if label in ["start_command", "stop_command", "speak_command", "backspace"]:
            return jsonify({
                "success": True,
                "hand_detected": True,
                "gesture_recognized": True,
                "current_word": current_word,
                "word": None,
                "confidence": round(confidence_score * 100, 2),
                "sentence": sentence.strip(),
                "all_words": recognized_words,
                "app_mode": app_mode,
                "action": action,
                "tts_playing": tts_playing
            })

        if label == last_label:
            if gesture_start_time is None:
                gesture_start_time = current_time

            elif current_time - gesture_start_time >= HOLD_TIME:
                display_word = GESTURE_MEANINGS.get(label, label.title())
                sentence += display_word + " "
                recognized_word = display_word
                action = "word_added"

                words = sentence.strip().split()
                recognized_words = words[-10:]

                last_label = None
                gesture_start_time = None
                lock_until = current_time + LOCK_TIME
        else:
            last_label = label
            gesture_start_time = current_time

        return jsonify({
            "success": True,
            "hand_detected": True,
            "gesture_recognized": True,
            "current_word": current_word,
            "word": recognized_word,
            "confidence": round(confidence_score * 100, 2),
            "sentence": sentence.strip(),
            "all_words": recognized_words,
            "app_mode": app_mode,
            "action": action,
            "tts_playing": tts_playing
        })

    except Exception as e:
        print(f"Error processing frame: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "hand_detected": False,
            "gesture_recognized": False,
            "current_word": "",
            "word": None,
            "sentence": sentence.strip(),
            "all_words": recognized_words,
            "app_mode": app_mode,
            "action": "none",
            "tts_playing": tts_playing
        })


@app.route("/clear_words", methods=["POST"])
def clear_words():
    global sentence, recognized_words, last_label, gesture_start_time, lock_until
    global backspace_start_time, backspace_triggered
    global speak_start_time, speak_triggered
    global start_start_time, start_triggered
    global stop_start_time, stop_triggered
    global app_mode, tts_playing

    sentence = ""
    recognized_words = []
    last_label = None
    gesture_start_time = None
    lock_until = 0
    backspace_start_time = None
    backspace_triggered = False
    speak_start_time = None
    speak_triggered = False
    start_start_time = None
    start_triggered = False
    stop_start_time = None
    stop_triggered = False
    app_mode = "waiting"

    return jsonify({
        "success": True,
        "tts_playing": tts_playing
    })


@app.route("/get_current_sentence", methods=["GET"])
def get_current_sentence():
    global sentence, recognized_words, tts_playing
    return jsonify({
        "sentence": sentence.strip(),
        "words": recognized_words,
        "tts_playing": tts_playing
    })


@app.route("/get_gesture_classes", methods=["GET"])
def get_gesture_classes():
    global tts_playing
    return jsonify({
        "classes": GESTURE_CLASSES,
        "meanings": GESTURE_MEANINGS,
        "tts_playing": tts_playing
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)