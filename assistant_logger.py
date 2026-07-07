"""
assistant_logger.py

Simple activity logger. Every event (face recognized, voice/gesture command,
security alert) gets appended to activity_log.csv with a timestamp, and is
also kept in an in-memory list so the GUI can display recent activity live.
"""

import csv
import os
import threading
from datetime import datetime

LOG_FILE = "activity_log.csv"
_lock = threading.Lock()
_recent_events = []  # in-memory list for GUI display
MAX_RECENT = 100


def log_event(event_type, details=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with _lock:
        file_exists = os.path.exists(LOG_FILE)
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "event_type", "details"])
            writer.writerow([timestamp, event_type, details])

        line = f"[{timestamp}] {event_type}: {details}"
        _recent_events.append(line)
        if len(_recent_events) > MAX_RECENT:
            _recent_events.pop(0)


def get_recent_events():
    with _lock:
        return list(_recent_events)