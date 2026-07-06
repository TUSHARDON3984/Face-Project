"""
STEP 2: Train the face recognizer on the images captured in Step 1.

Usage:
    python 2_train_model.py

This reads every image in dataset/, extracts the numeric ID from the filename
(user.<id>.<n>.jpg), and trains an LBPH (Local Binary Patterns Histogram)
face recognizer -- a classic, lightweight, open-source algorithm built into
OpenCV's contrib module. Output: trainer/trainer.yml
"""

import cv2
import numpy as np
import os

DATASET_DIR = "dataset"
TRAINER_DIR = "trainer"


def get_images_and_labels(path):
    image_paths = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".jpg")]
    face_samples = []
    ids = []

    face_detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

    for image_path in image_paths:
        # filenames look like: user.<id>.<count>.jpg
        try:
            face_id = int(os.path.split(image_path)[-1].split(".")[1])
        except (IndexError, ValueError):
            continue

        gray_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if gray_img is None:
            continue

        faces = face_detector.detectMultiScale(gray_img)
        for (x, y, w, h) in faces:
            face_samples.append(gray_img[y:y + h, x:x + w])
            ids.append(face_id)

    return face_samples, ids


def main():
    if not os.path.exists(TRAINER_DIR):
        os.makedirs(TRAINER_DIR)

    print("Training faces. This will take a few seconds...")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    faces, ids = get_images_and_labels(DATASET_DIR)

    if len(faces) == 0:
        print("ERROR: No faces found in dataset/. Run 1_capture_faces.py first.")
        return

    recognizer.train(faces, np.array(ids))
    recognizer.write(os.path.join(TRAINER_DIR, "trainer.yml"))

    print(f"Done. Trained on {len(np.unique(ids))} unique face(s), "
          f"{len(faces)} total images. Model saved to trainer/trainer.yml")


if __name__ == "__main__":
    main()