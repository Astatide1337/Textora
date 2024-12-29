import tkinter as tk
from tkinter import filedialog
import time
import random
import threading
import keyboard
from RealtimeSTT import AudioToTextRecorder
from tkinter import ttk

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        if self.tooltip or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 0
        y += self.widget.winfo_rooty() + 50
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, foreground="#E0E1DD", background="#415A77", relief="solid", borderwidth=1, font=("Inter", 10))
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class Textora:
    QWERTY_NEIGHBORS = {
        "q": "w",
        "w": "qe",
        "e": "wr",
        "r": "et",
        "t": "ry",
        "y": "tu",
        "u": "yi",
        "i": "uo",
        "o": "ip",
        "p": "o",
        "a": "s",
        "s": "ad",
        "d": "sf",
        "f": "dg",
        "g": "fh",
        "h": "gj",
        "j": "hk",
        "k": "jl",
        "l": "k",
        "z": "x",
        "x": "zc",
        "c": "xv",
        "v": "cb",
        "b": "vn",
        "n": "bm",
        "m": "n",
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Textora")
        self.root.geometry("1024x768")
        self.root.configure(bg="#0D1321")
        
        # Modern color scheme
        self.theme = {
            'primary': "#415A77",  # Modern blue
            'secondary': "#1B263B",  # Dark background
            'surface': "#778DA9",   # Slightly lighter surface
            'text': "#E0E1DD",      # White text
            'success': "#22c55e",   # Green
            'warning': "#f59e0b",   # Orange
            'error': "#ef4444",     # Red
            'disabled': "#6b7280",  # Gray
        }

        # Load icons
        self.recordIcon = tk.PhotoImage(file="./Icons/StartRecording.png")
        self.stopRecordIcon = tk.PhotoImage(file="./Icons/StopRecording.png")
        self.playIcon = tk.PhotoImage(file="./Icons/Play.png")
        self.pauseIcon = tk.PhotoImage(file="./Icons/Pause.png")
        self.stopIcon = tk.PhotoImage(file="./Icons/Stop.png")
        self.uploadIcon = tk.PhotoImage(file="./Icons/Upload.png")

        # Configure modern styling
        self.configure_styles()
        
        # Main container with padding
        self.main_container = ttk.Frame(self.root, style="Borderless.TFrame", padding="20")
        self.main_container.pack(fill="both", expand=True)

        # Header section
        self.create_header()
        
        # Status bar
        self.create_status_bar()
        
        # Main content area
        self.create_main_content()
        
        # Control panel
        self.create_control_panel()
        
        # Initialize state variables
        self.typing_active = False
        self.recording_active = False
        self.current_index = 0
        self.previous_text = ""
        self.recorder = None
        
        # Start shortcut listener
        threading.Thread(target=self.listen_for_shortcuts, daemon=True).start()

    def configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Remove borders from all frames
        style.configure("Borderless.TFrame",
                       background=self.theme['secondary'],
                       borderwidth=0,
                       relief="flat")
        
        # Configure label styles without borders
        style.configure("Title.TLabel", 
                       background=self.theme['secondary'],
                       foreground=self.theme['text'],
                       font=("Inter", 24, "bold"),
                       borderwidth=0)
        
        style.configure("Subtitle.TLabel",
                       background=self.theme['secondary'],
                       foreground=self.theme['text'],
                       font=("Inter", 12),
                       borderwidth=0)
        
        # Configure button styles
        style.configure("Primary.TButton",
                       background=self.theme['primary'],
                       foreground=self.theme['text'],
                       font=("Inter", 11),
                       padding=5,
                       borderwidth=0,
                       relief="flat")
        
        style.map("Primary.TButton",
                 background=[("active", self.theme['primary'])],
                 relief=[("pressed", "flat")])
        
        # Configure entry style
        style.configure("Modern.TEntry",
                        fieldbackground=self.theme['surface'],
                        foreground=self.theme['text'],
                        padding=5,
                        borderwidth=0,
                        highlightthickness=0,
                        relief="flat",
                        font=("Inter", 14))
        
        # Status bar style without borders
        style.configure("Status.TLabel",
                       background=self.theme['surface'],
                       foreground=self.theme['text'],
                       font=("Inter", 10),
                       padding=5,
                       borderwidth=0)

        # Remove borders from all other frame variations
        style.configure("Modern.TFrame",
                       background=self.theme['secondary'],
                       borderwidth=0,
                       relief="flat")

    def create_header(self):
        header_frame = ttk.Frame(self.main_container, style="Borderless.TFrame")
        header_frame.pack(fill="x", pady=(0, 20))
        
        title = ttk.Label(header_frame, 
                         text="Textora",
                         style="Title.TLabel")
        title.pack(side="left")
        
        subtitle = ttk.Label(header_frame,
                           text="Type Smarter Not Harder",
                           style="Subtitle.TLabel")
        subtitle.pack(side="left", padx=(10, 0), pady=(8, 0))

    def create_status_bar(self):
        self.status_frame = ttk.Frame(self.main_container, style="Borderless.TFrame")
        self.status_frame.pack(fill="x", pady=(0, 10))
        
        # Status indicators
        self.typing_status = ttk.Label(self.status_frame,
                                     text="Typing: Idle",
                                     style="Status.TLabel")
        self.typing_status.pack(side="left", padx=5)
        
        self.recording_status = ttk.Label(self.status_frame,
                                        text="Recording: Idle",
                                        style="Status.TLabel")
        self.recording_status.pack(side="left", padx=5)
        
        self.progress_status = ttk.Label(self.status_frame,
                                       text="Progress: 0%",
                                       style="Status.TLabel")
        self.progress_status.pack(side="left", padx=5)

    def create_main_content(self):
        # Text area with modern styling and no border
        self.text_area = tk.Text(self.main_container,
                                font=("Inter", 14),
                                bg=self.theme['surface'],
                                fg=self.theme['text'],
                                insertbackground=self.theme['text'],
                                wrap="word",
                                padx=15,
                                pady=15,
                                height=15,
                                relief="flat",
                                borderwidth=0,
                                highlightthickness=0)
        self.text_area.pack(fill="both", expand=True, pady=10)

    def create_control_panel(self):
        control_frame = ttk.Frame(self.main_container, style="Borderless.TFrame")
        control_frame.pack(fill="x", pady=20)
        
        # Left side - Speed and Accuracy controls
        left_frame = ttk.Frame(control_frame, style="Borderless.TFrame")
        left_frame.pack(side="left", fill="x", expand=True)
        
        def validate_number(P):
            if P.isdigit() or P == "":
                return True
            return False
        
        vcmd = (self.root.register(validate_number), '%P')

        # Speed control
        speed_frame = ttk.Frame(left_frame, style="Borderless.TFrame")
        speed_frame.pack(fill="x", pady=5)
        
        ttk.Label(speed_frame,
                 text="Typing Speed (WPM):",
                 style="Subtitle.TLabel").pack(side="left")
        
        self.typing_speed_entry = ttk.Entry(speed_frame,
                                          style="Modern.TEntry",
                                          width=10,
                                          validate="key",
                                          validatecommand=vcmd)
        self.typing_speed_entry.pack(side="left", padx=10)
        
        # Accuracy control
        accuracy_frame = ttk.Frame(left_frame, style="Borderless.TFrame")
        accuracy_frame.pack(fill="x", pady=5)
        
        ttk.Label(accuracy_frame,
                 text="Accuracy (%):",
                 style="Subtitle.TLabel").pack(side="left")
        
        self.accuracy_entry = ttk.Entry(accuracy_frame,
                                      style="Modern.TEntry",
                                      width=10,
                                      validate="key",
                                      validatecommand=vcmd)
        self.accuracy_entry.pack(side="left", padx=10)
        
        # Right side - Action buttons
        button_frame = ttk.Frame(control_frame, style="Borderless.TFrame")
        button_frame.pack(side="right")

        self.upload_button = ttk.Button(button_frame,
                                      text="Upload File",
                                      image=self.uploadIcon,
                                      style="Primary.TButton",
                                      command=self.upload_file)
        self.upload_button.pack(side="left", padx=5)
        ToolTip(self.upload_button, "Upload a text file")

        self.start_button = ttk.Button(button_frame,
                                    text="Start Typing",
                                    image=self.playIcon,
                                    style="Primary.TButton",
                                    command=self.start_typing)
        self.start_button.pack(side="left", padx=5)
        ToolTip(self.start_button, "Start typing")

        self.pause_button = ttk.Button(button_frame,
                                    text="Pause Typing",
                                    image=self.pauseIcon,
                                    style="Primary.TButton",
                                    command=self.toggle_typing)
        self.pause_button.pack(side="left", padx=5)
        ToolTip(self.pause_button, "Pause typing")
        
        self.stop_button = ttk.Button(button_frame,
                                    text="Stop Typing",
                                    image=self.stopIcon,
                                    style="Primary.TButton",
                                    command=self.stop_typing)
        self.stop_button.pack(side="left", padx=5)
        ToolTip(self.stop_button, "Stop typing")
        
        self.record_button = ttk.Button(button_frame,
                                      text="Start Recording",
                                      image=self.recordIcon,
                                      style="Primary.TButton",
                                      command=self.start_recording)
        self.record_button.pack(side="left", padx=5)
        ToolTip(self.record_button, "Start recording audio")

        self.stop_recording_button = ttk.Button(button_frame,
                                    text="Stop Recording",
                                    image=self.stopRecordIcon,
                                    style="Primary.TButton",
                                    command=self.stop_recording)
        self.stop_recording_button.pack(side="left", padx=5)
        ToolTip(self.stop_recording_button, "Stop recording audio")

    def update_status(self, typing_status=None, recording_status=None, progress=None):
        if typing_status is not None:
            self.typing_status.config(text=f"Typing: {typing_status}")
            
        if recording_status is not None:
            self.recording_status.config(text=f"Recording: {recording_status}")
            
        if progress is not None:
            self.progress_status.config(text=f"Progress: {progress}%")

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    text = file.read()
                    if not text:
                        raise ValueError("The file is empty.")
                    self.text_area.delete(1.0, "end")
                    self.text_area.insert("end", text)
            except Exception as e:
                tk.messagebox.showwarning("Error", str(e))

    def type_text(self, min_wpm: int, max_wpm: int) -> None:
        MINDELAY = 60 / min_wpm
        MAXDELAY = 60 / max_wpm

        current_text: str = self.text_area.get(1.0, "end").strip()
        words: list[str] = current_text.split()
        total_words = len(words)

        if current_text != self.previous_text:
            previous_words: list[str] = self.previous_text.split()
            if len(current_text) < len(self.previous_text) or not set(previous_words).intersection(set(words)):
                self.current_index = 0
            else:
                self.current_index = min(self.current_index, len(words))

            self.previous_text = current_text

        error_probability = (100 - int(self.accuracy_entry.get())) / 100

        self.update_status(typing_status="Active", progress=0)
        time.sleep(1)

        while self.current_index < len(words):
            word: str = words[self.current_index]
            typed_word = ""
            
            # Update progress
            progress = int((self.current_index / total_words) * 100)
            self.update_status(progress=progress)

            for letter in word:
                if not self.typing_active:
                    self.update_status(typing_status="Stopped", progress=progress)
                    return

                time.sleep(random.uniform(MINDELAY / len(word), MAXDELAY / len(word)))

                if random.random() < error_probability and letter.isalpha() and letter.lower() in self.QWERTY_NEIGHBORS:
                    # Introduce error
                    random_neighbor = random.choice(self.QWERTY_NEIGHBORS[letter.lower()])
                    keyboard.write(random_neighbor)
                    typed_word += letter

                    # Simulate backspace and retyping
                    if random.choice([True, False, False]):  
                        time.sleep(random.uniform(MINDELAY / len(word) + 0.3, MAXDELAY / len(word)) + 0.5)  
                        for i in range(len(typed_word)):
                            keyboard.write("\b")
                            time.sleep(random.uniform(MINDELAY / len(word), MAXDELAY / len(word)))  
                        
                        for i in range(len(typed_word)):
                            time.sleep(random.uniform(MINDELAY / len(word), MAXDELAY / len(word)))
                            keyboard.write(typed_word[i])
                    else:
                        time.sleep(random.uniform(MINDELAY / len(word) + 0.3, MAXDELAY / len(word)) + 0.5)
                        keyboard.write("\b")
                        time.sleep(random.uniform(MINDELAY / len(word), MAXDELAY / len(word)))
                        keyboard.write(letter)
                else:
                    keyboard.write(letter)
                    typed_word += letter

            time.sleep(random.uniform(len(word) / min_wpm, len(word) / max_wpm))
            keyboard.write(" ")
            self.current_index += 1

        self.update_status(typing_status="Completed", progress=100)
        self.stop_typing()

    def start_typing(self):
        try:
            self.typing_speed = int(self.typing_speed_entry.get())
            self.accuracy = int(self.accuracy_entry.get())
            if self.accuracy > 100 or self.accuracy < 0 or self.typing_speed < 0:
                raise ValueError
        except ValueError:
            self.update_status(typing_status="Invalid typing speed or accuracy")
            return

        if not self.text_area.get("1.0", "end-1c"):
            self.update_status(typing_status="No text")
            return

        if not self.typing_active:
            self.typing_active = True
            self.MINWPM = self.typing_speed - 10
            self.MAXWPM = self.typing_speed + 10
            self.update_status(typing_status="Starting...")
            threading.Thread(target=self.type_text, args=(self.MINWPM, self.MAXWPM), daemon=True).start()

    def stop_typing(self):
        if self.progress_status.cget("text") == "Progress: 100%":
            self.update_status(typing_status="Completed", progress=0)
            self.typing_active = False
            self.text_area.delete(1.0, "end")
            self.current_index = 0
            self.previous_text = ""
            self.typing_speed_entry.delete(0, "end")
            self.accuracy_entry.delete(0, "end")
            self.update_status(typing_status="Stopped")
        else:
            self.update_status(typing_status="Paused", progress=int(self.progress_status.cget("text").split(": ")[1][:-1]))
            self.typing_active = False

    def toggle_typing(self):
        if self.typing_active:
            self.stop_typing()
        else:
            self.start_typing()

    def listen_for_shortcuts(self):
        keyboard.add_hotkey("ctrl+alt+t", self.toggle_typing)

    def start_recording(self):
        if not self.recording_active:
            self.recorder = AudioToTextRecorder()
            self.recorder.start()
            self.recording_active = True
            self.update_status(recording_status="Active")
            threading.Thread(target=self.update_text_area_from_recording, daemon=True).start()

    def stop_recording(self):
        if self.recording_active and self.recorder:
            self.recorder.stop()
            self.recorder.shutdown()
            self.recorder = None
            self.recording_active = False
            self.update_status(recording_status="Stopped")

    def update_text_area_from_recording(self):
        while self.recording_active:
            if self.recorder:
                transcribed_text = self.recorder.text()
                if transcribed_text:
                    self.text_area.insert("end", transcribed_text + " ")
            time.sleep(0.5)

if __name__ == "__main__":
    root = tk.Tk()
    root.iconbitmap("./Icons/favicon.ico")
    app = Textora(root)
    root.mainloop()