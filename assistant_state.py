"""
assistant_state.py

Shared state between the vision thread, voice thread, and GUI, protected
by a lock since multiple threads read/write it concurrently. This is how
the voice assistant knows "is a recognized face currently in view" (used
for the security gate), and how the GUI knows what to display.
"""

import threading
import time

_lock = threading.Lock()

_state = {
    "current_face": None,       # name of currently recognized face, or None
    "last_seen_time": 0,        # timestamp of last time current_face was seen
    "last_gesture_action": "",
    "last_voice_command": "",
}


def set_current_face(name):
    with _lock:
        if name is not None:
            _state["current_face"] = name
            _state["last_seen_time"] = time.time()
        else:
            _state["current_face"] = None


def get_current_face(timeout_seconds=5):
    """Returns the current recognized face name, or None if not seen recently."""
    with _lock:
        if _state["current_face"] is None:
            return None
        if time.time() - _state["last_seen_time"] > timeout_seconds:
            return None
        return _state["current_face"]


def set_gesture_action(text):
    with _lock:
        _state["last_gesture_action"] = text


def set_voice_command(text):
    with _lock:
        _state["last_voice_command"] = text