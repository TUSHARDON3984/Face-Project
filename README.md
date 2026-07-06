Face Recognition + Tracking Project (OpenCV, 100% free & open source)
A real-time face detection, recognition, and tracking system built using classical computer vision -- no paid APIs, no cloud services, no GPU required.

What this uses
OpenCV (opencv-contrib-python) -- free, open-source, BSD-licensed
Haar Cascade -- face detector (bundled locally as haarcascade_frontalface_default.xml)
LBPH (Local Binary Patterns Histogram) -- face recognizer (built into OpenCV's contrib module)
CSRT Tracker -- object tracker for smooth frame-to-frame tracking (the "tracking" part)
Project structure

face_project/
├── requirements.txt
├── haarcascade_frontalface_default.xml   # face detector data file
├── 1_capture_faces.py                    # builds dataset/ from your webcam
├── 2_train_model.py                      # builds trainer/trainer.yml
├── 3_recognize_and_track.py              # live recognition + tracking
├── dataset/                              # your face images + labels.csv (gitignored)
└── trainer/                              # trained model (gitignored)
Setup
1. Clone the repo

bash
git clone https://github.com/TUSHARDON3984/Face-Project.git
cd Face-Project
2. Install dependencies

bash
pip install -r requirements.txt
Note: if your pip/python command runs a different Python install than the one you intend to use, install directly into it with the full path, e.g.:


powershell
& "C:\Path\To\python.exe" -m pip install -r requirements.txt
3. Verify OpenCV installed correctly

bash
python -c "import cv2; print(cv2.__version__); print(cv2.face.LBPHFaceRecognizer_create())"
You should see a version number and an LBPHFaceRecognizer object printed with no errors.

How to run (in order)
Step 1 -- Capture a face dataset

bash
python 1_capture_faces.py
Enter a numeric ID (e.g. 1) and the person's name.
Look at the webcam -- it auto-captures face images (move your head slightly, vary your expression, for more robust training data).
Press q to stop early.
Repeat this step with a new ID for each additional person you want the system to recognize.
Step 2 -- Train the recognizer

bash
python 2_train_model.py
Builds trainer/trainer.yml from everything in dataset/.

Step 3 -- Run real-time recognition + tracking

bash
python 3_recognize_and_track.py
A webcam window opens:

Green box = recognized face, labeled with the person's name
Red box = unrecognized / unknown face
Press q to quit.

How it works (methodology)
Detection -- Haar Cascade scans each frame for face-like regions.
Recognition -- Detected faces are resized to a fixed size, histogram- equalized (to normalize lighting), and passed to the LBPH recognizer, which compares local texture patterns against the trained model and returns a confidence score.
Tracking -- Rather than re-running detection on every frame (slow), a CSRT tracker locks onto the detected face's bounding box and follows it smoothly. Detection + recognition re-run periodically (every DETECT_EVERY_N_FRAMES) to correct any tracker drift.
This is a classical (non-deep-learning) computer vision pipeline -- fast, CPU-only, and fully explainable line-by-line, making it well suited to an academic project or for understanding CV fundamentals before moving to deep-learning-based approaches (e.g. FaceNet, dlib's CNN detector).

Configuration knobs
In 1_capture_faces.py:

NUM_SAMPLES -- how many face images to capture per person (default: 60, increase to 150+ for harder cases like visually similar faces/twins)
In 3_recognize_and_track.py:

CONFIDENCE_THRESHOLD -- LBPH confidence cutoff (lower = stricter match, default: 70; try 50 for fewer false positives)
DETECT_EVERY_N_FRAMES -- how often to re-run detection vs. relying on the tracker (default: 15)
Known limitations
LBPH is a classical algorithm and can struggle to distinguish very similar faces (e.g. identical/close twins) -- accuracy improves with more training samples, varied expressions/angles, and consistent lighting during capture.
Only the largest detected face is tracked at a time in this version (single-face tracking). Multi-face simultaneous tracking would require looping over all detected faces and maintaining a tracker per face.
Requires a working local webcam -- this cannot run in a browser or on GitHub's servers; clone and run it locally.
Troubleshooting
ModuleNotFoundError: No module named 'cv2' -- you likely have multiple Python installations; install opencv-contrib-python into the same Python interpreter your terminal/IDE is actually running (check with python -c "import sys; print(sys.executable)").
cv2.error: ... !empty() in function 'CascadeClassifier::detectMultiScale' -- the Haar Cascade XML file wasn't found. Make sure haarcascade_frontalface_default.xml is present in the project folder (already included in this repo).
Webcam won't open -- close other apps using the camera (Zoom/Teams) and check camera permissions in your OS settings.
Privacy note
The dataset/ (face images) and trainer/ (trained model) folders are excluded from version control via .gitignore, since they contain personal biometric data. Each user should generate their own by running Steps 1-2 locally.
