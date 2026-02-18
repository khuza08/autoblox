import customtkinter as ctk
import os
import threading
import time
from auto import PianoPlayer
from tkinter import filedialog

class PianoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Roblox Piano Auto Player")
        self.geometry("450x420")
        
        # ThEme
        COLOR_WHITE = "#FFFFFF"
        COLOR_GRAPHITE = "#303030"
        COLOR_CHARCOAL = "#595959"
        COLOR_SILVER = "#B5B5B5"
        COLOR_ALABASTER = "#E0E0E0"

        # Appearance
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=COLOR_GRAPHITE)

        self.player = PianoPlayer(delay=0.095)
        self.playing = False
        self.sheet_content = ""
        self.file_path = "sheet.txt"

        # Backend status for Wayland
        self.backend_msg = f"Backend: {self.player.backend}"
        if self.player.backend == 'pynput' and os.name == 'posix':
            self.backend_msg += " (Wayland? Run: sudo chmod 666 /dev/uinput)"

        # UI Elements
        self.label_title = ctk.CTkLabel(self, text="Roblox Piano Player", 
                                        font=ctk.CTkFont(size=24, weight="bold"),
                                        text_color=COLOR_WHITE)
        self.label_title.pack(pady=20)

        # File Selection Area
        self.frame_file = ctk.CTkFrame(self, fg_color=COLOR_CHARCOAL)
        self.frame_file.pack(pady=10, padx=20, fill="x")

        self.btn_select = ctk.CTkButton(self.frame_file, text="Select Sheet", 
                                         command=self.select_file,
                                         fg_color=COLOR_SILVER,
                                         text_color=COLOR_GRAPHITE,
                                         hover_color=COLOR_ALABASTER)
        self.btn_select.pack(pady=10, padx=10)

        self.label_file = ctk.CTkLabel(self.frame_file, text="Current file: sheet.txt", 
                                       font=ctk.CTkFont(size=12),
                                       text_color=COLOR_ALABASTER)
        self.label_file.pack(pady=5)

        # Tempo Control
        self.frame_tempo = ctk.CTkFrame(self, fg_color=COLOR_CHARCOAL)
        self.frame_tempo.pack(pady=10, padx=20, fill="x")

        self.label_tempo = ctk.CTkLabel(self.frame_tempo, text="Tempo (Delay: 0.095s)",
                                        text_color=COLOR_WHITE)
        self.label_tempo.pack(pady=5)

        self.slider_tempo = ctk.CTkSlider(self.frame_tempo, from_=0.05, to=0.3, 
                                          number_of_steps=50, 
                                          command=self.update_tempo,
                                          button_color=COLOR_SILVER,
                                          button_hover_color=COLOR_WHITE,
                                          progress_color=COLOR_SILVER)
        self.slider_tempo.set(0.095)
        self.slider_tempo.pack(pady=10, padx=20, fill="x")

        # Start/Stop Button
        self.btn_toggle = ctk.CTkButton(self, text="START MUSIC", 
                                        font=ctk.CTkFont(size=18, weight="bold"), 
                                        height=50, 
                                        command=self.toggle_playing, 
                                        fg_color=COLOR_ALABASTER, 
                                        text_color=COLOR_GRAPHITE,
                                        hover_color=COLOR_WHITE)
        self.btn_toggle.pack(pady=30, padx=20, fill="x")

        self.label_status = ctk.CTkLabel(self, text=self.backend_msg, 
                                         font=ctk.CTkFont(size=10), 
                                         text_color=COLOR_SILVER)
        self.label_status.pack(side="bottom", pady=5)

        # Load initial sheet if exists
        self.load_sheet("sheet.txt")

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            self.file_path = path
            self.label_file.configure(text=f"Current file: {os.path.basename(path)}")
            self.load_sheet(path)

    def load_sheet(self, path):
        try:
            with open(path, "r") as f:
                self.sheet_content = f.read()
        except Exception as e:
            self.label_file.configure(text=f"Error loading file: {str(e)}")

    def update_tempo(self, value):
        self.player.delay = float(value)
        self.label_tempo.configure(text=f"Tempo (Delay: {float(value):.3f}s)")

    def toggle_playing(self):
        if not self.playing:
            if not self.sheet_content:
                self.label_file.configure(text="No sheet loaded!")
                return
            
            self.playing = True
            self.btn_toggle.configure(text="STOP MUSIC", fg_color="#FF5555", text_color="white", hover_color="#CC0000")
            
            threading.Thread(target=self.play_music, daemon=True).start()
        else:
            self.playing = False
            self.player.stop()
            self.btn_toggle.configure(text="START MUSIC", fg_color="#E0E0E0", text_color="#303030", hover_color="#FFFFFF")

    def play_music(self):
        time.sleep(2)
        self.player.play(self.sheet_content)
        
        self.playing = False
        self.btn_toggle.configure(text="START MUSIC", fg_color="#E0E0E0", text_color="#303030", hover_color="#FFFFFF")

if __name__ == "__main__":
    app = PianoApp()
    app.mainloop()
