"""
assistant_voice.py

Voice control with a wake word ("hey assistant"), extended commands
(time, date, Google search, screenshot, dynamic app launching), and a
security gate: sensitive commands only run if a recognized face is
currently in view (tied to the vision thread via assistant_state).
"""

import speech_recognition as sr
import pyautogui
import subprocess
import webbrowser
import os
from datetime import datetime

from pycaw.pycaw import AudioUtilities

import assistant_state as state
import assistant_tts as tts
import assistant_logger as logger

WAKE_WORD = "hey assistant"

# Commands that require a recognized face in view before they'll execute
SENSITIVE_COMMANDS = ["open chrome", "open notepad", "open vscode", "open ",
                       "take a screenshot", "take screenshot", "search google"]

device = AudioUtilities.GetSpeakers()
volume_ctrl = device.EndpointVolume
vol_range = volume_ctrl.GetVolumeRange()
MIN_VOL, MAX_VOL = vol_range[0], vol_range[1]


def adjust_volume(step):
    current_vol = volume_ctrl.GetMasterVolumeLevel()
    new_vol = max(MIN_VOL, min(MAX_VOL, current_vol + step))
    volume_ctrl.SetMasterVolumeLevel(new_vol, None)


def is_sensitive(command):
    return any(keyword in command for keyword in SENSITIVE_COMMANDS)


def handle_command(command):
    command = command.lower().strip()
    state.set_voice_command(command)
    print(f"Heard: '{command}'")

    # ---- Security gate ----
    if is_sensitive(command):
        recognized = state.get_current_face()
        if recognized is None:
            tts.speak("Sorry, I don't recognize you. Access denied for that command.")
            logger.log_event("Security Alert", f"Blocked command: {command}")
            return True

    if "open chrome" in command:
        subprocess.Popen(["start", "chrome"], shell=True)
        tts.speak("Opening Chrome")
        logger.log_event("Voice Command", "Open Chrome")

    elif "open youtube" in command:
        webbrowser.open("https://youtube.com")
        tts.speak("Opening YouTube")
        logger.log_event("Voice Command", "Open YouTube")

    elif "open notepad" in command:
        subprocess.Popen(["notepad.exe"])
        tts.speak("Opening Notepad")
        logger.log_event("Voice Command", "Open Notepad")

    elif "open vscode" in command or "open vs code" in command:
        subprocess.Popen(["code"], shell=True)
        tts.speak("Opening VS Code")
        logger.log_event("Voice Command", "Open VS Code")

    elif command.startswith("open "):
        # Dynamic fallback for any other app, e.g. "open spotify", "open calculator"
        app_name = command.replace("open ", "").strip()
        try:
            os.system(f"start {app_name}")
            tts.speak(f"Trying to open {app_name}")
            logger.log_event("Voice Command", f"Open (dynamic): {app_name}")
        except Exception as e:
            tts.speak(f"I couldn't open {app_name}")
            print(f"    ERROR: {e}")

    elif "search google for" in command:
        query = command.split("search google for", 1)[1].strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        tts.speak(f"Searching Google for {query}")
        logger.log_event("Voice Command", f"Google search: {query}")

    elif "take a screenshot" in command or "take screenshot" in command:
        os.makedirs("screenshots", exist_ok=True)
        filename = f"screenshots/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        pyautogui.screenshot(filename)
        tts.speak("Screenshot taken")
        logger.log_event("Voice Command", f"Screenshot saved: {filename}")

    elif "what time is it" in command or "current time" in command:
        tts.speak(f"It's {datetime.now().strftime('%I:%M %p')}")

    elif "what's the date" in command or "today's date" in command or "what is the date" in command:
        tts.speak(f"Today is {datetime.now().strftime('%B %d, %Y')}")

    elif "play" in command or "pause" in command:
        pyautogui.press("playpause")
        tts.speak("Toggling play pause")
        logger.log_event("Voice Command", "Play/Pause")

    elif "volume up" in command:
        adjust_volume(5.0)
        tts.speak("Volume up")
        logger.log_event("Voice Command", "Volume Up")

    elif "volume down" in command:
        adjust_volume(-5.0)
        tts.speak("Volume down")
        logger.log_event("Voice Command", "Volume Down")

    elif "zoom in" in command:
        pyautogui.hotkey("ctrl", "=")
        tts.speak("Zooming in")
        logger.log_event("Voice Command", "Zoom In")

    elif "zoom out" in command:
        pyautogui.hotkey("ctrl", "-")
        tts.speak("Zooming out")
        logger.log_event("Voice Command", "Zoom Out")

    elif "stop listening" in command or "shut down" in command or "goodbye" in command:
        tts.speak("Goodbye!")
        return False

    else:
        print(" -> No matching command recognized.")

    return True

def run_voice_loop(stop_event):
    """Main voice loop with wake-word gating. Intended to run in a background thread."""
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    # Tuning for better accuracy -- gives more room for natural pauses/full phrases
    recognizer.pause_threshold = 1.0        # how long a pause means "done talking" (default 0.8)
    recognizer.dynamic_energy_threshold = True

    print("Calibrating microphone for background noise... stay quiet for 2 seconds.")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
    print(f"Energy threshold set to: {recognizer.energy_threshold}")

    tts.speak("Voice assistant ready. Say hey assistant to give a command.")

    while not stop_event.is_set():
        with mic as source:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            except sr.WaitTimeoutError:
                continue

        try:
            text = recognizer.recognize_google(audio).lower()
            print(f"[DEBUG - always listening] Heard: '{text}'")  # shows EVERYTHING heard
        except sr.UnknownValueError:
            print("[DEBUG] Heard something, but couldn't transcribe it.")
            continue
        except sr.RequestError as e:
            print(f"Speech recognition service error: {e}")
            continue

        if WAKE_WORD in text:
            tts.speak("Yes?")
            with mic as source:
                try:
                    audio2 = recognizer.listen(source, timeout=6, phrase_time_limit=6)
                    command_text = recognizer.recognize_google(audio2)
                    print(f"[DEBUG - command] Heard: '{command_text}'")
                    should_continue = handle_command(command_text)
                    if not should_continue:
                        stop_event.set()
                        break
                except sr.WaitTimeoutError:
                    tts.speak("I didn't catch that.")
                    print("[DEBUG] Timed out waiting for command.")
                except sr.UnknownValueError:
                    tts.speak("I didn't catch that.")
                    print("[DEBUG] Could not transcribe the command audio.")
                except sr.RequestError as e:
                    print(f"Speech recognition service error: {e}")