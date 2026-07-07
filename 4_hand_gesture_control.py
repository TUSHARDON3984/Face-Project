"""
4_hand_gesture_control.py

Hand-gesture control using your webcam + MediaPipe (Google's free, open-source
hand-tracking library). No training needed -- MediaPipe already knows how to
find hand landmarks out of the box.

Gestures:
- PINCH (thumb + index finger together, then move apart/closer) -> Zoom in/out
    (simulates Ctrl + '+' / Ctrl + '-', which zooms in most browsers, PDF viewers,
    and image viewers)
- OPEN PALM (all 5 fingers up, held) -> Volume up (steadily, while held)
- CLOSED FIST (0 fingers up, held) -> Volume down (steadily, while held)
- PEACE SIGN (index + middle fingers up only) -> Play/Pause toggle
    (simulates Spacebar, which plays/pauses in YouTube, VLC, most video players)

Press 'q' to quit.
"""

import cv2
import mediapipe as mp
import pyautogui
import time
import math

from pycaw.pycaw import AudioUtilities

# ---------- Volume setup (Windows system volume via pycaw) ----------
device = AudioUtilities.GetSpeakers()
volume_ctrl = device.EndpointVolume
# Volume range is typically (-65.25, 0.0) in decibels
vol_range = volume_ctrl.GetVolumeRange()
MIN_VOL, MAX_VOL = vol_range[0], vol_range[1]

# ---------- MediaPipe setup ----------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)

# ---------- Gesture cooldowns (prevent spamming actions every frame) ----------
last_action_time = 0
ACTION_COOLDOWN = 1.0  # seconds between play/pause / zoom triggers
prev_pinch_distance = None
ZOOM_CHANGE_THRESHOLD = 15  # pixels of change needed to register a zoom step


def fingers_up(hand_landmarks, handedness_label):
    """Returns a list of 5 booleans: [thumb, index, middle, ring, pinky] = up or not."""
    lm = hand_landmarks.landmark
    fingers = []

    # Thumb: compare x-coordinates (flips depending on left/right hand)
    if handedness_label == "Right":
        fingers.append(lm[4].x < lm[3].x)
    else:
        fingers.append(lm[4].x > lm[3].x)

    # Other 4 fingers: tip is above the joint below it (lower y = higher on screen)
    tips = [8, 12, 16, 20]
    joints = [6, 10, 14, 18]
    for tip, joint in zip(tips, joints):
        fingers.append(lm[tip].y < lm[joint].y)

    return fingers


def main():
    global last_action_time, prev_pinch_distance

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("ERROR: Could not access webcam.")
        return

    print("Hand gesture control running. Press 'q' to quit.")
    print("Gestures: Pinch=Zoom | Open Palm=Volume Up | Fist=Volume Down | Peace Sign=Play/Pause")

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)  # mirror view, feels more natural
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)

        gesture_text = "No hand detected"

        if result.multi_hand_landmarks and result.multi_handedness:
            hand_landmarks = result.multi_hand_landmarks[0]
            handedness_label = result.multi_handedness[0].classification[0].label

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            h, w, _ = frame.shape
            lm = hand_landmarks.landmark
            fingers = fingers_up(hand_landmarks, handedness_label)
            total_fingers = sum(fingers)

            thumb_tip = (int(lm[4].x * w), int(lm[4].y * h))
            index_tip = (int(lm[8].x * w), int(lm[8].y * h))
            pinch_distance = math.hypot(index_tip[0] - thumb_tip[0], index_tip[1] - thumb_tip[1])

            now = time.time()

            # --- Peace sign: index + middle up, ring + pinky down = Play/Pause ---
            if fingers == [False, True, True, False, False]:
                gesture_text = "Peace Sign -> Play/Pause"
                if now - last_action_time > ACTION_COOLDOWN:
                    pyautogui.press("space")
                    last_action_time = now

            # --- Open palm: all 5 fingers up = Volume Up (continuous while held) ---
            elif total_fingers == 5:
                gesture_text = "Open Palm -> Volume Up"
                current_vol = volume_ctrl.GetMasterVolumeLevel()
                new_vol = min(current_vol + 1.5, MAX_VOL)
                volume_ctrl.SetMasterVolumeLevel(new_vol, None)

            # --- Closed fist: 0 fingers up = Volume Down (continuous while held) ---
            elif total_fingers == 0:
                gesture_text = "Fist -> Volume Down"
                current_vol = volume_ctrl.GetMasterVolumeLevel()
                new_vol = max(current_vol - 1.5, MIN_VOL)
                volume_ctrl.SetMasterVolumeLevel(new_vol, None)

            # --- Pinch gesture: thumb + index distance changing = Zoom ---
            else:
                gesture_text = f"Tracking... (fingers up: {total_fingers})"
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

            prev_pinch_distance = pinch_distance
            cv2.circle(frame, thumb_tip, 8, (255, 0, 255), -1)
            cv2.circle(frame, index_tip, 8, (255, 0, 255), -1)
            cv2.line(frame, thumb_tip, index_tip, (255, 0, 255), 2)
        else:
            prev_pinch_distance = None

        cv2.putText(frame, gesture_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2)
        cv2.imshow("Hand Gesture Control - Press q to quit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()