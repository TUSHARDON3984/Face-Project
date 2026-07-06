"""
STEP 3: Real-time face recognition + tracking using your webcam.

Usage:
    python 3_recognize_and_track.py

How it works:
- Every N frames, it runs face DETECTION (Haar Cascade) + RECOGNITION (LBPH)
  to identify who is in frame and get a confidence score.
- Between those frames, it uses a fast OpenCV TRACKER (CSRT) to follow the
  face's position smoothly without re-running detection every frame.
  This is the "image tracking" part -- much faster than detecting on
  every single frame, and it's how basic surveillance/webcam apps work.
- Press 'q' to quit.
"""

import cv2
import os

TRAINER_PATH = "trainer/trainer.yml"
LABELS_PATH = "dataset/labels.csv"
CASCADE_PATH = "haarcascade_frontalface_default.xml"

DETECT_EVERY_N_FRAMES = 15   # re-run detection this often to correct tracker drift
CONFIDENCE_THRESHOLD = 65    # LBPH: LOWER value = more confident match (0 = perfect)


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


def create_tracker():
    # CSRT tracker: accurate and still real-time. Built into opencv-contrib.
    return cv2.TrackerCSRT_create()


def main():
    if not os.path.exists(TRAINER_PATH):
        print("ERROR: No trained model found. Run 2_train_model.py first.")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(TRAINER_PATH)
    face_detector = cv2.CascadeClassifier(CASCADE_PATH)
    labels = load_labels(LABELS_PATH)

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("ERROR: Could not access webcam.")
        return

    tracker = None
    tracking = False
    frame_count = 0
    current_name = "Unknown"

    print("Running... press 'q' to quit.")

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_count += 1

        # Re-detect + re-recognize periodically, or if we lost tracking
        if not tracking or frame_count % DETECT_EVERY_N_FRAMES == 0:
            faces = face_detector.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

            if len(faces) > 0:
                # Just handle the largest face for simplicity
                (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])

                face_id, confidence = recognizer.predict(gray[y:y + h, x:x + w])
                if confidence < CONFIDENCE_THRESHOLD:
                    current_name = labels.get(face_id, "Unknown")
                else:
                    current_name = "Unknown"

                tracker = create_tracker()
                tracker.init(frame, (int(x), int(y), int(w), int(h)))
                tracking = True
            else:
                tracking = False

        elif tracking:
            success, box = tracker.update(frame)
            if success:
                (x, y, w, h) = [int(v) for v in box]
            else:
                tracking = False

        # Draw box + label if we currently have a valid position
        if tracking:
            color = (0, 255, 0) if current_name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, current_name, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow("Face Recognition + Tracking - Press q to quit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()