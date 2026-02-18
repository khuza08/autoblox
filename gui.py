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
        self.geometry("600x650") # Window size increased for textbox
        
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
        self.label_title.pack(pady=(20, 10))

        # Sheet Input Area (Textbox)
        self.label_box = ctk.CTkLabel(self, text="Paste or Edit Music Sheet Below:", 
                                      font=ctk.CTkFont(size=14), text_color=COLOR_ALABASTER)
        self.label_box.pack(pady=5)
        
        self.textbox = ctk.CTkTextbox(self, height=250, fg_color=COLOR_CHARCOAL, 
                                      text_color=COLOR_WHITE, font=("Courier", 12))
        self.textbox.pack(pady=10, padx=20, fill="both", expand=True)

        # File Selection Area
        self.frame_file = ctk.CTkFrame(self, fg_color=COLOR_CHARCOAL)
        self.frame_file.pack(pady=10, padx=20, fill="x")

        self.btn_select = ctk.CTkButton(self.frame_file, text="Load File to Box", 
                                         command=self.select_file,
                                         fg_color=COLOR_SILVER,
                                         text_color=COLOR_GRAPHITE,
                                         hover_color=COLOR_ALABASTER)
        self.btn_select.grid(row=0, column=0, pady=10, padx=10)

        self.label_file = ctk.CTkLabel(self.frame_file, text="File: sheet.txt", 
                                       font=ctk.CTkFont(size=12),
                                       text_color=COLOR_ALABASTER)
        self.label_file.grid(row=0, column=1, pady=10, padx=10)

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
        self.btn_toggle.pack(pady=(20, 10), padx=20, fill="x")

        self.label_status = ctk.CTkLabel(self, text=self.backend_msg, 
                                         font=ctk.CTkFont(size=10), 
                                         text_color=COLOR_SILVER)
        self.label_status.pack(side="bottom", pady=5)

        # Load initial sheet if exists
        self.load_initial_sheet("sheet.txt")

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            self.file_path = path
            self.label_file.configure(text=f"File: {os.path.basename(path)}")
            try:
                with open(path, "r") as f:
                    content = f.read()
                    self.textbox.delete("1.0", "end")
                    self.textbox.insert("1.0", content)
            except Exception as e:
                self.label_file.configure(text=f"Error: {str(e)}")

    def load_initial_sheet(self, path):
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    content = f.read()
                    self.textbox.insert("1.0", content)
            except:
                pass

    def update_tempo(self, value):
        self.player.delay = float(value)
        self.label_tempo.configure(text=f"Tempo (Delay: {float(value):.3f}s)")

    def toggle_playing(self):
        if not self.playing:
            # Get latest content from textbox
            self.sheet_content = self.textbox.get("1.0", "end-1c")
            
            if not self.sheet_content.strip():
                self.label_box.configure(text_color="red", text="INPUT BOX IS EMPTY!")
                self.after(2000, lambda: self.label_box.configure(text_color="#E0E0E0", text="Paste or Edit Music Sheet Below:"))
                return
            
            # Save to sheet.txt for persistence
            try:
                with open("sheet.txt", "w") as f:
                    f.write(self.sheet_content)
            except:
                pass

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
