"""
assistant_tts.py

Thread-safe text-to-speech helper using pyttsx3 (free, fully offline,
open-source -- no API key, no internet needed). Runs a background worker
thread with a queue, so any part of the assistant can call speak("text")
without worrying about thread conflicts or blocking.
"""

import pyttsx3
import threading
import queue
import pythoncom

_speech_queue = queue.Queue()
_worker_started = False


def _worker():
    pythoncom.CoInitialize()  # required for SAPI5 (Windows speech) to work in a thread
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    while True:
        text = _speech_queue.get()
        if text is None:
            break
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[TTS ERROR] {e}")
    pythoncom.CoUninitialize()


def start():
    """Call once at startup to launch the background speech worker."""
    global _worker_started
    if not _worker_started:
        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        _worker_started = True


def speak(text):
    """Queue text to be spoken. Non-blocking -- safe to call from any thread."""
    print(f"[ASSISTANT SAYS] {text}")
    _speech_queue.put(text)