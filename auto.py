# Code originally created by maksimKorzh on Github https://github.com/maksimKorzh
# Code adjusted by Xi-v on Github https://github.com/Xi-v
# Code adapted to linux by elza on Github https://github.com/khuza08/autoblox

import time
import threading
import sys
import random

# Backend selection
try:
    import evdev
    from evdev import UInput, ecodes as e
    LINUX_EVDEV = True
except ImportError:
    LINUX_EVDEV = False

from pynput.keyboard import Controller, Key

class PianoPlayer:
    def __init__(self, delay=0.095, hold_percent=0.8, humanize=False):
        self.delay = delay
        self.hold_percent = hold_percent
        self.humanize = humanize
        self._stop_event = threading.Event()
        
        # Initialize backend
        if LINUX_EVDEV and sys.platform.startswith('linux'):
            try:
                self.ui = UInput()
                self.backend = 'evdev'
                print(f"[LOG] Backend: evdev (Wayland Support)")
            except Exception as err:
                print(f"[LOG] evdev failed: {err}. Falling back to pynput.")
                self.keyboard = Controller()
                self.backend = 'pynput'
        else:
            self.keyboard = Controller()
            self.backend = 'pynput'
            print(f"[LOG] Backend: pynput")

        self.special_characters = {
            '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
            '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
            '_': '-', '+': '=', '{': '[', '}': ']', ':': ';',
            '"': "'", '<': ',', '>': '.', '?': '/'
        }
        
        # Scancode mapping for Linux evdev
        if hasattr(self, 'backend') and self.backend == 'evdev':
            self.key_map = {
                '1': e.KEY_1, '2': e.KEY_2, '3': e.KEY_3, '4': e.KEY_4, '5': e.KEY_5,
                '6': e.KEY_6, '7': e.KEY_7, '8': e.KEY_8, '9': e.KEY_9, '0': e.KEY_0,
                'a': e.KEY_A, 'b': e.KEY_B, 'c': e.KEY_C, 'd': e.KEY_D, 'e': e.KEY_E,
                'f': e.KEY_F, 'g': e.KEY_G, 'h': e.KEY_H, 'i': e.KEY_I, 'j': e.KEY_J,
                'k': e.KEY_K, 'l': e.KEY_L, 'm': e.KEY_M, 'n': e.KEY_N, 'o': e.KEY_O,
                'p': e.KEY_P, 'q': e.KEY_Q, 'r': e.KEY_R, 's': e.KEY_S, 't': e.KEY_T,
                'u': e.KEY_U, 'v': e.KEY_V, 'w': e.KEY_W, 'x': e.KEY_X, 'y': e.KEY_Y,
                'z': e.KEY_Z,
                '-': e.KEY_MINUS, '=': e.KEY_EQUAL, '[': e.KEY_LEFTBRACE, ']': e.KEY_RIGHTBRACE,
                ';': e.KEY_SEMICOLON, "'": e.KEY_APOSTROPHE, ',': e.KEY_COMMA, '.': e.KEY_DOT,
                '/': e.KEY_SLASH
            }

    def press_key(self, note, duration=0.02):
        if self.backend == 'evdev':
            self._press_evdev(note, duration)
        else:
            self._press_pynput(note, duration)

    def _press_pynput(self, note, duration):
        if note in self.special_characters:  
            self.keyboard.press(Key.shift)
            self.keyboard.press(self.special_characters[note])
            time.sleep(duration)
            self.keyboard.release(self.special_characters[note])
            self.keyboard.release(Key.shift)
        elif note.isupper():
            self.keyboard.press(Key.shift)
            self.keyboard.press(note.lower())
            time.sleep(duration)
            self.keyboard.release(note.lower())
            self.keyboard.release(Key.shift)
        else: 
            self.keyboard.press(note)
            time.sleep(duration)
            self.keyboard.release(note)

    def _press_evdev(self, note, duration):
        char = note
        needs_shift = False

        if note in self.special_characters:
            char = self.special_characters[note]
            needs_shift = True
        elif note.isupper():
            char = note.lower()
            needs_shift = True

        code = self.key_map.get(char)
        if code:
            if needs_shift:
                self.ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1)
            
            self.ui.write(e.EV_KEY, code, 1)
            self.ui.syn()
            
            time.sleep(duration)
            
            self.ui.write(e.EV_KEY, code, 0)
            if needs_shift:
                self.ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)
            
            self.ui.syn()

    def stop(self):
        self._stop_event.set()
        print("[LOG] Playing stopped.")

    def _wait_until(self, target_time):
        """High-precision spin-wait loop."""
        while time.perf_counter() < target_time:
            if self._stop_event.is_set():
                break
            # Small yield to OS if we have enough time
            diff = target_time - time.perf_counter()
            if diff > 0.002:
                time.sleep(0.001)

    def play(self, sheet_content):
        self._stop_event.clear()
        notes = sheet_content
        print(f"[LOG] Play with Humanization: {'ON' if self.humanize else 'OFF'}")

        schedule = []
        current_time_offset = 0.0
        index = 0
        
        while index < len(notes):
            if notes[index].isalnum() or notes[index] in self.special_characters:
                schedule.append((current_time_offset, [notes[index]]))
            elif notes[index] == '|':
                current_time_offset += self.delay * 8
                index += 1
                continue
            elif notes[index] == '[':
                chord = []
                index += 1
                while index < len(notes) and notes[index] != ']':
                    if notes[index].isalnum() or notes[index] in self.special_characters:
                        chord.append(notes[index])
                    index += 1
                if chord:
                    schedule.append((current_time_offset, chord))
            
            current_time_offset += self.delay
            index += 1

        start_time = time.perf_counter()

        for offset, events in schedule:
            if self._stop_event.is_set():
                break
            
            # Apply Timing Jitter
            jitter = 0
            if self.humanize:
                jitter = random.uniform(-0.005, 0.005)
            
            target = start_time + offset + jitter
            self._wait_until(target)
            
            # Dynamic Hold Duration
            duration = self.delay * self.hold_percent
            if self.humanize:
                duration *= random.uniform(0.9, 1.1)
                duration = max(0.01, duration) # Don't go too low

            for i, note in enumerate(events):
                # Chord Strum: Delay between notes in a chord
                if i > 0 and self.humanize:
                    time.sleep(random.uniform(0.005, 0.015))
                
                # We need to launch the key press in a short-lived thread for chords
                # or just use duration manually if it's a single note.
                # To keep it simple and accurate, for chords we'll just press them fast
                # unless a more complex async logic is needed.
                self.press_key(note, duration)
        
        if not self._stop_event.is_set():
            print("[LOG] Finished playing.")

if __name__ == "__main__":
    player = PianoPlayer()
    try:
        with open('sheet.txt') as f:
            content = f.read()
            player.play(content)
    except FileNotFoundError:
        print("[ERR] sheet.txt not found.")
