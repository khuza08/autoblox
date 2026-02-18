import customtkinter as ctk
import os
import threading
import time
import selectors
from auto import PianoPlayer
from tkinter import filedialog

# evdev for global hotkey on Wayland
try:
    import evdev
    from evdev import ecodes as e
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False

def find_keyboard_devices():
    """Find all real physical keyboard devices via evdev."""
    if not EVDEV_AVAILABLE:
        return []
    kbd_list = []
    try:
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        print(f"[LOG] Scanning {len(devices)} devices for physical keyboards...")
        for dev in devices:
            # EXCLUDE virtual devices
            name_lower = dev.name.lower()
            if "uinput" in name_lower or "virtual" in name_lower:
                continue
                
            caps = dev.capabilities()
            # A physical keyboard must have EV_KEY and common keys
            if e.EV_KEY in caps:
                key_caps = caps[e.EV_KEY]
                if e.KEY_A in key_caps and e.KEY_Z in key_caps:
                    print(f"[LOG] OK: Found physical keyboard: {dev.name} ({dev.path})")
                    kbd_list.append(dev)
    except Exception as ex:
        print(f"[ERR] Error listing devices: {ex}")
    return kbd_list

class PianoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Roblox Piano Auto Player")
        self.geometry("600x720")
        
        # Appearance
        ctk.set_appearance_mode("dark")
        
        # ThEme
        COLOR_WHITE = "#FFFFFF"
        COLOR_GRAPHITE = "#303030"
        COLOR_CHARCOAL = "#595959"
        COLOR_SILVER = "#B5B5B5"
        COLOR_ALABASTER = "#E0E0E0"

        self.configure(fg_color=COLOR_GRAPHITE)

        print("[LOG] Initializing PianoPlayer...")
        self.player = PianoPlayer(delay=60.0/67.0, hold_percent=0.67, humanize=False)
        self.playing = False
        self.loop_mode = False
        self.sheet_content = ""
        self.hotkey_key = "F5"
        self.recording_hotkey = False
        self._stop_listener = threading.Event()

        # Backend status for Wayland
        self.backend_msg = f"Backend: {self.player.backend}"
        if self.player.backend == 'pynput' and os.name == 'posix':
            self.backend_msg += " (Wayland? Run: sudo chmod 666 /dev/uinput)"

        # --- UI Elements ---
        self.label_title = ctk.CTkLabel(self, text="Roblox Piano Player", 
                                        font=ctk.CTkFont(size=24, weight="bold"),
                                        text_color=COLOR_WHITE)
        self.label_title.pack(pady=(20, 5))

        # Sheet Input Area (Textbox)
        self.label_box = ctk.CTkLabel(self, text="Paste or Edit Music Sheet Below:", 
                                      font=ctk.CTkFont(size=14), text_color=COLOR_ALABASTER)
        self.label_box.pack(pady=5)
        
        self.textbox = ctk.CTkTextbox(self, height=220, fg_color=COLOR_CHARCOAL, 
                                      text_color=COLOR_WHITE, font=("Courier", 12))
        self.textbox.pack(pady=5, padx=20, fill="both", expand=True)


        self.frame_combined = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_combined.pack(pady=5, padx=20, fill="x")
        self.frame_combined.grid_columnconfigure((0, 1), weight=1)

        self.frame_tempo = ctk.CTkFrame(self.frame_combined, fg_color="transparent", 
                                        border_width=2, border_color=COLOR_CHARCOAL)
        self.frame_tempo.grid(row=0, column=0, padx=(0, 5), sticky="nsew")

        initial_bpm = 67
        self.label_tempo = ctk.CTkLabel(self.frame_tempo, text=f"Tempo (BPM: {initial_bpm})",
                                        text_color=COLOR_WHITE)
        self.label_tempo.pack(pady=5)

        self.slider_tempo = ctk.CTkSlider(self.frame_tempo, from_=30, to=1067, 
                                          number_of_steps=1037, 
                                          command=self.update_tempo,
                                          button_color=COLOR_SILVER,
                                          button_hover_color=COLOR_WHITE,
                                          progress_color=COLOR_SILVER)
        self.slider_tempo.set(initial_bpm)
        self.slider_tempo.pack(pady=10, padx=10, fill="x")

        # Hold Percentage Column
        self.frame_hold = ctk.CTkFrame(self.frame_combined, fg_color="transparent", 
                                       border_width=2, border_color=COLOR_CHARCOAL)
        self.frame_hold.grid(row=0, column=1, padx=(5, 0), sticky="nsew")

        self.label_hold = ctk.CTkLabel(self.frame_hold, text="Hold Percentage: 67%",
                                        text_color=COLOR_WHITE)
        self.label_hold.pack(pady=5)

        self.slider_hold = ctk.CTkSlider(self.frame_hold, from_=0.1, to=1.0, 
                                          number_of_steps=90, 
                                          command=self.update_hold_percent,
                                          button_color=COLOR_SILVER,
                                          button_hover_color=COLOR_WHITE,
                                          progress_color=COLOR_SILVER)
        self.slider_hold.set(0.67)
        self.slider_hold.pack(pady=10, padx=10, fill="x")

        # Options Container (Humanize & Loop)
        self.frame_options = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_options.pack(pady=5, padx=20, fill="x")
        self.frame_options.grid_columnconfigure((0, 1), weight=1)

        # Humanize Control
        self.frame_human = ctk.CTkFrame(self.frame_options, fg_color="transparent", 
                                        border_width=2, border_color=COLOR_CHARCOAL)
        self.frame_human.grid(row=0, column=0, padx=(0, 5), sticky="nsew")

        self.switch_human = ctk.CTkSwitch(self.frame_human, text="Humanize Mode",
                                          command=self.update_humanize,
                                          progress_color=COLOR_SILVER,
                                          button_color=COLOR_WHITE,
                                          button_hover_color=COLOR_ALABASTER)
        self.switch_human.pack(pady=10, padx=10)

        # Loop Control
        self.frame_loop = ctk.CTkFrame(self.frame_options, fg_color="transparent", 
                                       border_width=2, border_color=COLOR_CHARCOAL)
        self.frame_loop.grid(row=0, column=1, padx=(5, 0), sticky="nsew")

        self.switch_loop = ctk.CTkSwitch(self.frame_loop, text="Loop Mode",
                                         command=self.update_loop,
                                         progress_color=COLOR_SILVER,
                                         button_color=COLOR_WHITE,
                                         button_hover_color=COLOR_ALABASTER)
        self.switch_loop.pack(pady=10, padx=10)

        # Hotkey Setting
        self.frame_hotkey = ctk.CTkFrame(self, fg_color="transparent", 
                                         border_width=2, border_color=COLOR_CHARCOAL)
        self.frame_hotkey.pack(pady=5, padx=20, fill="x")

        self.label_hotkey_title = ctk.CTkLabel(self.frame_hotkey, text="Hotkey (Start/Stop):",
                                               text_color=COLOR_ALABASTER)
        self.label_hotkey_title.grid(row=0, column=0, padx=10, pady=10)

        self.label_hotkey_display = ctk.CTkLabel(self.frame_hotkey, text=f"[ {self.hotkey_key} ]",
                                                  font=ctk.CTkFont(size=14, weight="bold"),
                                                  text_color=COLOR_WHITE)
        self.label_hotkey_display.grid(row=0, column=1, padx=10, pady=10)

        self.btn_set_hotkey = ctk.CTkButton(self.frame_hotkey, text="Change Hotkey",
                                             command=self.start_hotkey_recording,
                                             fg_color=COLOR_SILVER,
                                             text_color=COLOR_GRAPHITE,
                                             hover_color=COLOR_ALABASTER,
                                             width=130)
        self.btn_set_hotkey.grid(row=0, column=2, padx=10, pady=10)

        # Countdown Label
        self.label_countdown = ctk.CTkLabel(self, text="", 
                                             font=ctk.CTkFont(size=24, weight="bold"),
                                             text_color=COLOR_SILVER)
        self.label_countdown.pack(pady=0)

        # Start/Stop Button
        self.btn_toggle = ctk.CTkButton(self, text="START MUSIC", 
                                        font=ctk.CTkFont(size=18, weight="bold"), 
                                        height=50, 
                                        command=self.toggle_playing, 
                                        fg_color=COLOR_ALABASTER, 
                                        text_color=COLOR_GRAPHITE,
                                        hover_color=COLOR_WHITE)
        self.btn_toggle.pack(pady=(0, 10), padx=20, fill="x")

        self.label_status = ctk.CTkLabel(self, text=self.backend_msg, 
                                         font=ctk.CTkFont(size=10), 
                                         text_color=COLOR_SILVER)
        self.label_status.pack(side="bottom", pady=5)

        # Load initial sheet
        self.load_initial_sheet("sheet.txt")

        # Start global hotkey listener
        self._start_global_hotkey_listener()

    def load_initial_sheet(self, path):
        if os.path.exists(path):
            print(f"[LOG] Loading initial sheet: {path}")
            try:
                with open(path, "r") as f:
                    self.textbox.insert("1.0", f.read())
            except:
                pass

    # ---- Tempo ----
    def update_tempo(self, value):
        bpm = int(value)
        # Convert BPM to Delay (Seconds): delay = 60 / BPM
        delay = 60.0 / bpm
        self.player.delay = delay
        self.label_tempo.configure(text=f"Tempo (BPM: {bpm})")
        # print(f"[LOG] Tempo changed: {bpm} BPM (Delay: {delay:.4f}s)")

    def update_hold_percent(self, value):
        self.player.hold_percent = float(value)
        self.label_hold.configure(text=f"Hold Percentage: {int(float(value)*100)}%")

    def update_humanize(self):
        self.player.humanize = self.switch_human.get()
        state = "ON" if self.player.humanize else "OFF"
        print(f"[LOG] Humanize Mode: {state}")

    def update_loop(self):
        self.loop_mode = bool(self.switch_loop.get())
        state = "ON" if self.loop_mode else "OFF"
        print(f"[LOG] Loop Mode: {state}")

    # ---- Global Hotkey via evdev (Multi-Device) ----
    def _start_global_hotkey_listener(self):
        """Start a background thread that reads keyboard events from ALL found keyboards."""
        if not EVDEV_AVAILABLE:
            print("[ERR] evdev not available for global hotkey listener.")
            return
        
        self._stop_listener.clear()
        threading.Thread(target=self._evdev_listener_loop, daemon=True).start()
        print("[LOG] Global hotkey listener (Multi-Device) started.")

    def _evdev_listener_loop(self):
        """Monitor multiple keyboard devices simultaneously using selectors."""
        kbds = find_keyboard_devices()
        if not kbds:
            print("[ERR] No physical keyboards found for global listener.")
            return

        selector = selectors.DefaultSelector()
        for k in kbds:
            selector.register(k, selectors.EVENT_READ)
            print(f"[LOG] Monitoring: {k.name}")

        try:
            while not self._stop_listener.is_set():
                for key, mask in selector.select(timeout=0.5):
                    device = key.fileobj
                    for event in device.read():
                        if self.recording_hotkey: continue
                        if event.type == e.EV_KEY and event.value == 1:
                            key_name = evdev.ecodes.KEY[event.code].replace("KEY_", "")
                            if key_name.upper() == self.hotkey_key.upper():
                                print(f"[LOG] Hotkey {self.hotkey_key} triggered on {device.name}!")
                                self.after(0, self.toggle_playing)
        except Exception as ex:
            print(f"[ERR] Multi-listener error: {ex}")
        finally:
            selector.close()

    # ---- Hotkey Recording ----
    def start_hotkey_recording(self):
        if self.recording_hotkey: return
        
        print("[LOG] Entering hotkey recording mode (All Keyboards)...")
        self.recording_hotkey = True
        self._stop_listener.set()
        
        self.btn_set_hotkey.configure(text="Press any key...", fg_color="#595959")
        self.label_hotkey_display.configure(text="[ ? ]")
        
        threading.Thread(target=self._record_hotkey_evdev, daemon=True).start()

    def _record_hotkey_evdev(self):
        """Record from any physical keyboard."""
        kbds = find_keyboard_devices()
        if not kbds:
            self.after(0, lambda: self.btn_set_hotkey.configure(text="Change Hotkey", fg_color="#B5B5B5"))
            self.recording_hotkey = False
            self._start_global_hotkey_listener()
            return

        selector = selectors.DefaultSelector()
        for k in kbds:
            selector.register(k, selectors.EVENT_READ)

        captured_key = None
        try:
            finished = False
            while not finished:
                for key, mask in selector.select():
                    device = key.fileobj
                    for event in device.read():
                        if event.type == e.EV_KEY and event.value == 1:
                            captured_key = evdev.ecodes.KEY[event.code].replace("KEY_", "")
                            print(f"[LOG] Captured {captured_key} from {device.name}")
                            finished = True
                            break
                    if finished: break
        except Exception as ex:
            print(f"[ERR] Recording error: {ex}")

        if captured_key:
            self.hotkey_key = captured_key.upper()
            self.after(0, self._update_hotkey_ui)

        selector.close()
        self.recording_hotkey = False
        self._start_global_hotkey_listener()

    def _update_hotkey_ui(self):
        self.label_hotkey_display.configure(text=f"[ {self.hotkey_key} ]")
        self.btn_set_hotkey.configure(text="Change Hotkey", fg_color="#B5B5B5")

    # ---- Play Logic ----
    def toggle_playing(self):
        if not self.playing:
            self.sheet_content = self.textbox.get("1.0", "end-1c")
            if not self.sheet_content.strip():
                print("[LOG] Play attempt with empty input box.")
                self.label_box.configure(text_color="red", text="INPUT BOX IS EMPTY!")
                self.after(2000, lambda: self.label_box.configure(text_color="#E0E0E0", text="Paste or Edit Music Sheet Below:"))
                return
            
            try:
                with open("sheet.txt", "w") as f:
                    f.write(self.sheet_content)
            except:
                pass

            print("[LOG] Starting playback process...")
            self.playing = True
            self.btn_toggle.configure(text="STOP MUSIC", fg_color="#FF5555", text_color="white", hover_color="#CC0000")
            threading.Thread(target=self.play_music, daemon=True).start()
        else:
            print("[LOG] Manual stop triggered.")
            self.playing = False
            self.player.stop()
            self.label_countdown.configure(text="")
            self.btn_toggle.configure(text="START AUTO", fg_color="#E0E0E0", text_color="#303030", hover_color="#FFFFFF")

    def play_music(self):
        # Countdown only once
        for i in range(3, 0, -1):
            if not self.playing: return 
            self.after(0, lambda n=i: self.label_countdown.configure(text=f"Starting in {n}..."))
            time.sleep(1)
        
        while self.playing:
            self.after(0, lambda: self.label_countdown.configure(text="Playing..."))
            self.player.play(self.sheet_content)
            
            # If loop is off or we stopped manually, break the cycle
            if not self.loop_mode or not self.playing:
                break
            
            print("[LOG] Loop enabled. Restarting playback...")
            time.sleep(0.5) # Short gap before restart
        
        self.playing = False
        self.after(0, lambda: self.label_countdown.configure(text=""))
        self.after(0, lambda: self.btn_toggle.configure(text="START AUTO", fg_color="#E0E0E0", text_color="#303030", hover_color="#FFFFFF"))

if __name__ == "__main__":
    app = PianoApp()
    app.mainloop()
