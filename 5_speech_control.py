import speech_recognition as sr
import pyautogui
import subprocess
import webbrowser

from pycaw.pycaw import AudioUtilities

device = AudioUtilities.GetSpeakers()
volume_ctrl = device.EndpointVolume
vol_range = volume_ctrl.GetVolumeRange()
MIN_VOL, MAX_VOL = vol_range[0], vol_range[1]


def adjust_volume(step):
    current_vol = volume_ctrl.GetMasterVolumeLevel()
    new_vol = max(MIN_VOL, min(MAX_VOL, current_vol + step))
    volume_ctrl.SetMasterVolumeLevel(new_vol, None)
    print(f"    (volume level now: {new_vol:.1f} dB, range {MIN_VOL:.1f} to {MAX_VOL:.1f})")


def open_app(name):
    try:
        if name == "chrome":
            subprocess.Popen(["start", "chrome"], shell=True)
        elif name == "notepad":
            subprocess.Popen(["notepad.exe"])
        elif name == "vscode":
            subprocess.Popen(["code"], shell=True)
        print(f"    (launched {name})")
    except Exception as e:
        print(f"    ERROR launching {name}: {e}")


def handle_command(command):
    command = command.lower().strip()
    print(f"Heard: '{command}'")

    if "open chrome" in command:
        open_app("chrome")
        print(" -> Action: Open Chrome")
    elif "open youtube" in command:
        webbrowser.open("https://youtube.com")
        print(" -> Action: Open YouTube")
    elif "open notepad" in command:
        open_app("notepad")
        print(" -> Action: Open Notepad")
    elif "open vscode" in command or "open vs code" in command:
        open_app("vscode")
        print(" -> Action: Open VS Code")
    elif "play" in command or "pause" in command:
        pyautogui.press("space")
        print(" -> Action: Play/Pause (make sure the video window is focused)")
    elif "volume up" in command:
        adjust_volume(5.0)
        print(" -> Action: Volume Up")
    elif "volume down" in command:
        adjust_volume(-5.0)
        print(" -> Action: Volume Down")
    elif "zoom in" in command:
        pyautogui.hotkey("ctrl", "=")
        print(" -> Action: Zoom In")
    elif "zoom out" in command:
        pyautogui.hotkey("ctrl", "-")
        print(" -> Action: Zoom Out")
    elif "stop listening" in command:
        print("Stopping voice control.")
        return False
    else:
        print(" -> No matching command recognized.")

    return True


def main():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("Calibrating for background noise... stay quiet for a second.")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

    print("\nVoice control ready. Try saying: 'play', 'pause', 'volume up',")
    print("'volume down', 'zoom in', 'zoom out', 'open chrome', 'open youtube',")
    print("'open notepad', 'open vscode', or 'stop listening'.\n")

    running = True
    while running:
        with mic as source:
            print("Listening...")
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)
            except sr.WaitTimeoutError:
                continue

        try:
            text = recognizer.recognize_google(audio)
            running = handle_command(text)
        except sr.UnknownValueError:
            print("Could not understand audio, try again.")
        except sr.RequestError as e:
            print(f"Speech recognition service error: {e}")


if __name__ == "__main__":
    main()
