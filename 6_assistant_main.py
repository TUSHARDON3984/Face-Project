"""
6_assistant_main.py

Unified assistant launcher: runs face recognition + hand gestures (vision
thread) and wake-word voice control (voice thread) together, with a modern
dark-themed GUI dashboard (built with customtkinter -- free, open source)
showing live status and activity log.

Usage:
    python 6_assistant_main.py

Then say "hey assistant" followed by a command, e.g.:
    "hey assistant, open chrome"
    "hey assistant, volume up"
    "hey assistant, what time is it"
"""

import os
import threading
import customtkinter as ctk

import assistant_state as state
import assistant_tts as tts
import assistant_logger as logger
import assistant_vision as vision
import assistant_voice as voice

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

stop_event = threading.Event()


def start_threads():
    tts.start()
    vision_thread = threading.Thread(target=vision.run_vision_loop, args=(stop_event,), daemon=True)
    voice_thread = threading.Thread(target=voice.run_voice_loop, args=(stop_event,), daemon=True)
    vision_thread.start()
    voice_thread.start()


class AssistantDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Assistant Dashboard")
        self.geometry("560x640")
        self.minsize(480, 560)
        self.configure(fg_color="#0f1117")

        # ---------- Header ----------
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(28, 10))

        ctk.CTkLabel(
            header_frame, text="Assistant Dashboard",
            font=ctk.CTkFont(size=26, weight="bold"), text_color="#ffffff"
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_frame, text="Face recognition  |  Hand gestures  |  Voice control",
            font=ctk.CTkFont(size=13), text_color="#8b93a7"
        ).pack(anchor="w", pady=(2, 0))

        # ---------- Status card ----------
        status_card = ctk.CTkFrame(self, fg_color="#1a1d29", corner_radius=16)
        status_card.pack(fill="x", padx=24, pady=12)

        status_inner = ctk.CTkFrame(status_card, fg_color="transparent")
        status_inner.pack(fill="x", padx=20, pady=18)

        self.status_dot = ctk.CTkLabel(status_inner, text="o", font=ctk.CTkFont(size=18),
                                        text_color="#e74c3c", width=20)
        self.status_dot.grid(row=0, column=0, sticky="w")

        self.status_text = ctk.CTkLabel(
            status_inner, text="No recognized face in view",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#ffffff", anchor="w"
        )
        self.status_text.grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.command_text = ctk.CTkLabel(
            status_inner, text="Last command: --",
            font=ctk.CTkFont(size=12), text_color="#8b93a7", anchor="w"
        )
        self.command_text.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))

        status_inner.grid_columnconfigure(1, weight=1)

        # ---------- Activity log card ----------
        log_card = ctk.CTkFrame(self, fg_color="#1a1d29", corner_radius=16)
        log_card.pack(fill="both", expand=True, padx=24, pady=12)

        ctk.CTkLabel(
            log_card, text="ACTIVITY LOG",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#8b93a7"
        ).pack(anchor="w", padx=20, pady=(16, 6))

        self.log_box = ctk.CTkTextbox(
            log_card, fg_color="#12141c", text_color="#c7ccd8",
            font=ctk.CTkFont(size=12, family="Consolas"),
            corner_radius=10, wrap="word"
        )
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.log_box.configure(state="disabled")

        # ---------- Quit button ----------
        self.quit_button = ctk.CTkButton(
            self, text="Quit Assistant", command=self.on_quit,
            fg_color="#e74c3c", hover_color="#c0392b",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44, corner_radius=12
        )
        self.quit_button.pack(fill="x", padx=24, pady=(6, 24))

        self.protocol("WM_DELETE_WINDOW", self.on_quit)
        self.refresh()

    def refresh(self):
        face = state.get_current_face()
        if face:
            self.status_dot.configure(text_color="#2ecc71")
            self.status_text.configure(text=f"Recognized: {face}")
        else:
            self.status_dot.configure(text_color="#e74c3c")
            self.status_text.configure(text="No recognized face in view")

        last_cmd = state._state.get("last_voice_command", "") if hasattr(state, "_state") else ""
        if last_cmd:
            self.command_text.configure(text=f"Last command: {last_cmd}")

        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        for line in logger.get_recent_events()[-30:]:
            self.log_box.insert("end", line + "\n")
        self.log_box.configure(state="disabled")
        self.log_box.see("end")

        if not stop_event.is_set():
            self.after(1000, self.refresh)
        else:
            self.destroy()
            os._exit(0)

    def on_quit(self):
        stop_event.set()
        self.destroy()
        os._exit(0)  # force-kill immediately -- avoids hanging on stuck mic/camera threads


if __name__ == "__main__":
    start_threads()
    app = AssistantDashboard()
    app.mainloop()