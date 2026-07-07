"""
assistant_vision.py

Combined face recognition + hand gesture control, running in a background
thread using a SINGLE webcam feed for both features. Updates shared
assistant_state so the voice assistant and GUI know who is currently in
frame, speaks personalized greetings, and raises stranger alerts.
"""

import cv2
import mediapipe as mp
import pyautogui
import time
import math
import os

from pycaw.pycaw import AudioUtilities

import assistant_state as state
import assistant_tts as tts
import assistant_logger as logger

CASCADE_PATH = "haarcascade_frontalface_default.xml"
TRAINER_PATH = "trainer/trainer.yml"
LABELS_PATH = "dataset/labels.csv"

DETECT_EVERY_N_FRAMES = 15
CONFIDENCE_THRESHOLD = 70
ZOOM_CHANGE_THRESHOLD = 15
ACTION_COOLDOWN = 1.0
GREETING_COOLDOWN_SECONDS = 60   # don't re-greet the same person constantly
STRANGER_ALERT_COOLDOWN = 30     # seconds between repeated stranger alerts
UNKNOWN_STREAK_THRESHOLD = 20    # frames of "Unknown" before raising an alert


def load_labels(path):
    labels = {}
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                face_id, name = line.split(",", 1)
                labels[int(face_id)] = name
    return labels


def fingers_up(hand_landmarks, handedness_label):
    lm = hand_landmarks.landmark
    fingers = []
    if handedness_label == "Right":
        fingers.append(lm[4].x < lm[3].x)
    else:
        fingers.append(lm[4].x > lm[3].x)
    tips = [8, 12, 16, 20]
    joints = [6, 10, 14, 18]
    for tip, joint in zip(tips, joints):
        fingers.append(lm[tip].y < lm[joint].y)
    return fingers


def run_vision_loop(stop_event):
    """Main combined loop. Intended to run in a background thread."""
    if not os.path.exists(TRAINER_PATH):
        print("WARNING: No trained face model found (run 1_capture_faces.py "
              "and 2_train_model.py first). Face recognition disabled.")
        recognizer = None
    else:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(TRAINER_PATH)

    face_detector = cv2.CascadeClassifier(CASCADE_PATH)
    labels = load_labels(LABELS_PATH)

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7,
                            min_tracking_confidence=0.7)

    device = AudioUtilities.GetSpeakers()
    volume_ctrl = device.EndpointVolume
    vol_range = volume_ctrl.GetVolumeRange()
    MIN_VOL, MAX_VOL = vol_range[0], vol_range[1]

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("ERROR: Could not access webcam.")
        return

    tracker = None
    tracking = False
    frame_count = 0
    current_name = "Unknown"

    last_greeted = {}
    last_stranger_alert = 0
    unknown_streak = 0

    last_action_time = 0
    prev_pinch_distance = None

    print("Vision loop running (face recognition + hand gestures). Press 'q' in the window to quit.")

    while not stop_event.is_set():
        ret, frame = cam.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_count += 1
        x = y = w = h = 0

        # ---------------- FACE RECOGNITION + TRACKING ----------------
        if recognizer is not None:
            if not tracking or frame_count % DETECT_EVERY_N_FRAMES == 0:
                faces = face_detector.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
                if len(faces) > 0:
                    (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
                    face_crop = cv2.resize(gray[y:y + h, x:x + w], (200, 200))
                    face_crop = cv2.equalizeHist(face_crop)
                    face_id, confidence = recognizer.predict(face_crop)

                    current_name = labels.get(face_id, "Unknown") if confidence < CONFIDENCE_THRESHOLD else "Unknown"

                    tracker = cv2.TrackerCSRT_create()
                    tracker.init(frame, (int(x), int(y), int(w), int(h)))
                    tracking = True
                else:
                    tracking = False
                    current_name = "Unknown"
            elif tracking:
                success, box = tracker.update(frame)
                if success:
                    (x, y, w, h) = [int(v) for v in box]
                else:
                    tracking = False

            now = time.time()
            if tracking and current_name != "Unknown":
                state.set_current_face(current_name)
                unknown_streak = 0
                if now - last_greeted.get(current_name, 0) > GREETING_COOLDOWN_SECONDS:
                    tts.speak(f"Hello {current_name}, welcome back!")
                    logger.log_event("Face Recognized", current_name)
                    last_greeted[current_name] = now
            elif tracking and current_name == "Unknown":
                state.set_current_face(None)
                unknown_streak += 1
                if unknown_streak > UNKNOWN_STREAK_THRESHOLD and now - last_stranger_alert > STRANGER_ALERT_COOLDOWN:
                    tts.speak("Warning: unrecognized person detected.")
                    logger.log_event("Stranger Alert", "Unrecognized face in frame")
                    last_stranger_alert = now
            else:
                state.set_current_face(None)
                unknown_streak = 0

            if tracking:
                color = (0, 255, 0) if current_name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, current_name, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # ---------------- HAND GESTURE CONTROL ----------------
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)
        gesture_text = ""

        if result.multi_hand_landmarks and result.multi_handedness:
            hand_landmarks = result.multi_hand_landmarks[0]
            handedness_label = result.multi_handedness[0].classification[0].label
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            h_, w_, _ = frame.shape
            lm = hand_landmarks.landmark
            fingers = fingers_up(hand_landmarks, handedness_label)
            total_fingers = sum(fingers)

            thumb_tip = (int(lm[4].x * w_), int(lm[4].y * h_))
            index_tip = (int(lm[8].x * w_), int(lm[8].y * h_))
            pinch_distance = math.hypot(index_tip[0] - thumb_tip[0], index_tip[1] - thumb_tip[1])

            now = time.time()

            if fingers == [False, True, True, False, False]:
                gesture_text = "Peace Sign -> Play/Pause"
                if now - last_action_time > ACTION_COOLDOWN:
                    pyautogui.press("playpause")
                    last_action_time = now
                    state.set_gesture_action("Play/Pause")
                    logger.log_event("Gesture", "Play/Pause")

            elif total_fingers == 5:
                gesture_text = "Open Palm -> Volume Up"
                current_vol = volume_ctrl.GetMasterVolumeLevel()
                volume_ctrl.SetMasterVolumeLevel(min(current_vol + 1.5, MAX_VOL), None)
                state.set_gesture_action("Volume Up")

            elif total_fingers == 0:
                gesture_text = "Fist -> Volume Down"
                current_vol = volume_ctrl.GetMasterVolumeLevel()
                volume_ctrl.SetMasterVolumeLevel(max(current_vol - 1.5, MIN_VOL), None)
                state.set_gesture_action("Volume Down")

            else:
                gesture_text = f"Tracking hand... ({total_fingers} fingers)"
                if prev_pinch_distance is not None:
                    diff = pinch_distance - prev_pinch_distance
                    if abs(diff) > ZOOM_CHANGE_THRESHOLD and now - last_action_time > 0.4:
                        if diff > 0:
                            pyautogui.hotkey("ctrl", "=")
                            gesture_text = "Zooming In"
                        else:
                            pyautogui.hotkey("ctrl", "-")
                            gesture_text = "Zooming Out"
                        last_action_time = now
                        state.set_gesture_action(gesture_text)
                        logger.log_event("Gesture", gesture_text)

            prev_pinch_distance = pinch_distance
        else:
            prev_pinch_distance = None

        cv2.putText(frame, gesture_text, (10, frame.shape[0] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow("Assistant Vision - Press q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break

    cam.release()
    cv2.destroyAllWindows()