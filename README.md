# Personal Assistant Project (Face Recognition, Gestures, Voice Control)

A multi-modal personal assistant built in Python using 100% free, open-source
tools -- no paid APIs, no cloud services required. Combines computer vision,
hand gesture control, voice commands, and text-to-speech into one unified
assistant with a live GUI dashboard.

## Features

- **Face detection, recognition, and tracking** -- recognizes specific people
  by name in real time via webcam
- **Hand gesture control** -- pinch to zoom, open palm/fist for volume,
  peace sign for play/pause
- **Voice control with wake word** -- say "hey assistant" followed by a
  command (open apps, control volume/zoom/playback, search Google, take
  screenshots, tell the time/date)
- **Text-to-speech** -- the assistant speaks responses and greetings back
- **Personalized greetings** -- greets recognized individuals by name
- **Security gating** -- sensitive voice commands (opening apps, screenshots,
  searches) only execute if a recognized face is currently in view; unknown
  faces trigger a spoken stranger alert
- **Modern GUI dashboard** -- live status indicator and scrolling activity
  log (built with customtkinter)
- **Activity logging** -- every recognized face, gesture, and voice command
  is timestamped and saved to `activity_log.csv`

## Tech stack (all free & open source)
- **OpenCV (`opencv-contrib-python`)** -- face detection (Haar Cascade),
  face recognition (LBPH), object tracking (CSRT)
- **MediaPipe** (Google) -- hand landmark detection for gestures
- **SpeechRecognition** -- voice command transcription (Google's free
  speech API, no key needed for personal use)
- **pyttsx3** -- fully offline text-to-speech
- **Pycaw** -- Windows system volume control
- **PyAutoGUI** -- keyboard/zoom simulation and screenshots
- **customtkinter** -- modern dashboard GUI

## Project structure
```
face_project/
├── requirements.txt              # base deps (face recognition only)
├── requirements_assistant.txt    # full deps (gestures, voice, TTS, GUI)
├── haarcascade_frontalface_default.xml
│
├── 1_capture_faces.py            # Step 1: build face dataset from webcam
├── 2_train_model.py              # Step 2: train LBPH recognizer
├── 3_recognize_and_track.py      # Step 3: standalone face recognition + tracking
├── 4_hand_gesture_control.py     # standalone hand gesture control
├── 5_speech_control.py           # standalone voice control
├── 6_assistant_main.py           # unified assistant (all features + GUI)
│
├── assistant_tts.py              # text-to-speech engine (thread-safe)
├── assistant_logger.py           # activity logging (CSV + in-memory)
├── assistant_state.py            # shared state between threads
├── assistant_vision.py           # combined face recognition + gestures
├── assistant_voice.py            # wake-word voice control + commands
│
├── dataset/                      # captured face images + labels (gitignored)
├── trainer/                      # trained face model (gitignored)
├── screenshots/                  # saved screenshots (gitignored)
└── activity_log.csv              # generated log of all assistant activity
```

## Setup

This project uses **two Python environments**:
- **Base Python** -- for the simple face recognition scripts (1-3), which
  only need OpenCV + NumPy
- **`gesture_env` (Python 3.12 virtual environment)** -- for gestures,
  voice, TTS, and the unified assistant (4, 5, 6), which need heavier
  dependencies (MediaPipe, PyAudio, etc.) that work best on a stable,
  slightly older Python version

### 1. Clone the repo
```bash
git clone https://github.com/TUSHARDON3984/Face-Project.git
cd Face-Project
```

### 2. Set up the base environment (for scripts 1-3)
```bash
pip install -r requirements.txt
```

### 3. Set up gesture_env (for scripts 4, 5, 6)
```bash
py -3.12 -m venv gesture_env
gesture_env\Scripts\activate      # Windows
pip install -r requirements_assistant.txt
```

> **Note:** `PyAudio` and `mediapipe` can be picky about very new Python
> versions -- Python 3.12 is the tested, stable choice here. `mediapipe`
> is pinned to `0.10.14` since newer releases have a known bug breaking
> the `mp.solutions` API.

## How to run

### Step 1 -- Capture a face dataset
```bash
python 1_capture_faces.py
```
Enter a numeric ID and name, look at the webcam. Repeat for each person.

### Step 2 -- Train the recognizer
```bash
python 2_train_model.py
```

### Step 3 -- Test standalone face recognition (optional)
```bash
python 3_recognize_and_track.py
```

### Run the full unified assistant
```bash
gesture_env\Scripts\activate
python 6_assistant_main.py
```

This opens:
- A webcam window (face recognition + hand gestures)
- A dashboard window (status + live activity log)

Say **"hey assistant"** followed by a command, e.g.:
- "hey assistant, open chrome"
- "hey assistant, open youtube"
- "hey assistant, volume up" / "volume down"
- "hey assistant, zoom in" / "zoom out"
- "hey assistant, play" / "pause"
- "hey assistant, what time is it" / "what's the date"
- "hey assistant, search google for [query]"
- "hey assistant, take a screenshot"
- "hey assistant, open [any app name]" (dynamic app launch)
- "hey assistant, stop listening" / "goodbye" (exits)

You can also say the wake word and command together in one sentence, e.g.
"hey assistant open notepad."

Hand gestures (no voice needed):
- **Pinch fingers apart/together** -> zoom in/out (works on the focused
  window, e.g. a browser)
- **Open palm** (held) -> volume up
- **Closed fist** (held) -> volume down
- **Peace sign** -> play/pause (media key)

Press `q` in the webcam window, or click "Quit Assistant" in the
dashboard, to stop everything.

## Security note
Commands like opening apps, taking screenshots, and searching are gated
behind face recognition -- they'll only execute while a recognized face is
in view. If no recognized face is present, the assistant verbally declines
and logs a security alert. Prolonged unrecognized faces also trigger a
spoken stranger warning.

## Known limitations
- LBPH is a classical (non-deep-learning) algorithm and can struggle to
  distinguish very similar faces (e.g. identical twins) -- mitigated with
  more training samples, varied angles/expressions, lighting normalization,
  and a stricter confidence threshold.
- Zoom and play/pause simulate keyboard input, so they act on whichever
  window is currently focused/frontmost.
- Requires a local webcam and microphone -- this cannot run in a browser or
  on GitHub's servers; clone and run it locally.
- Voice recognition depends on Google's free public speech API, so an
  internet connection is required for voice features.

## Troubleshooting
- **`ModuleNotFoundError`** -- check you're using the right environment/
  interpreter for the script you're running (see Setup above).
- **`cv2.error: ... !empty() in detectMultiScale`** -- the Haar Cascade XML
  file is missing; make sure `haarcascade_frontalface_default.xml` is in
  the project folder.
- **`mp.solutions` AttributeError** -- you likely have a newer, buggy
  mediapipe version; run `pip install mediapipe==0.10.14`.
- **pycaw `AttributeError: 'AudioDevice' object has no attribute 'Activate'`**
  -- newer pycaw versions changed their API; this project already uses the
  current `device.EndpointVolume` pattern.
- **TTS `CoInitialize has not been called`** -- `pyttsx3` needs COM
  initialized on its worker thread; already handled via `pythoncom.CoInitialize()`
  in `assistant_tts.py`.
- **Webcam won't open** -- close other apps using the camera (Zoom/Teams)
  and check camera permissions in Windows settings.

## Privacy note
`dataset/`, `trainer/`, and `screenshots/` are excluded from version control
via `.gitignore`, since they contain personal biometric data and screen
captures. Each user should generate their own by running Steps 1-2 locally.
