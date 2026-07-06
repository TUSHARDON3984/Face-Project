"""
STEP 1: Capture face images from your webcam to build a training dataset.

Usage:
    python 1_capture_faces.py

- Enter a numeric ID and a name when prompted.
- Look at the webcam; it will automatically capture ~60 face images.
- Press 'q' at any time to stop early.
"""

import cv2
import os

# Path where the Haar Cascade file lives (comes bundled with opencv-contrib-python)
CASCADE_PATH ="haarcascade_frontalface_default.xml"
DATASET_DIR = "dataset"
NUM_SAMPLES = 60  # number of face images to capture per person


def main():
    if not os.path.exists(DATASET_DIR):
        os.makedirs(DATASET_DIR)

    face_id = input("Enter a numeric ID for this person (e.g. 1, 2, 3): ").strip()
    face_name = input("Enter this person's name: ").strip()

    # Save name-to-id mapping so we can display names later
    labels_file = os.path.join(DATASET_DIR, "labels.csv")
    with open(labels_file, "a") as f:
        f.write(f"{face_id},{face_name}\n")

    face_detector = cv2.CascadeClassifier(CASCADE_PATH)
    cam = cv2.VideoCapture(0)  # 0 = default webcam

    if not cam.isOpened():
        print("ERROR: Could not access webcam. Check permissions/other apps using it.")
        return

    print("\nLook at the camera. Capturing images... Press 'q' to stop early.\n")

    count = 0
    while True:
        ret, frame = cam.read()
        if not ret:
            print("Failed to grab frame from webcam.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            count += 1
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Save the cropped, grayscale face image
            face_img = gray[y:y + h, x:x + w]
            filename = os.path.join(DATASET_DIR, f"user.{face_id}.{count}.jpg")
            cv2.imwrite(filename, face_img)

            cv2.putText(frame, f"Captured: {count}/{NUM_SAMPLES}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Capturing Faces - Press q to quit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        elif count >= NUM_SAMPLES:
            break

    print(f"\nDone. Captured {count} images for '{face_name}' (ID: {face_id}).")
    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()