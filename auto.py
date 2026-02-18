# Code originally created by maksimKorzh on Github https://github.com/maksimKorzh
# Code adjusted by Xi-v on Github https://github.com/Xi-v
# Code adapted to linux by elza on Github https://github.com/khuza08/autoblox

import time
import threading
import sys

# Backend selection
try:
    import evdev
    from evdev import UInput, ecodes as e
    LINUX_EVDEV = True
except ImportError:
    LINUX_EVDEV = False

from pynput.keyboard import Controller, Key

class PianoPlayer:
    def __init__(self, delay=0.095):
        self.delay = delay
        self._stop_event = threading.Event()
        
        # Initialize backend
        if LINUX_EVDEV and sys.platform.startswith('linux'):
            try:
                self.ui = UInput()
                self.backend = 'evdev'
                print("Backend: evdev (Wayland/Linux supported)")
            except Exception as err:
                print(f"evdev failed: {err}. Falling back to pynput.")
                self.keyboard = Controller()
                self.backend = 'pynput'
        else:
            self.keyboard = Controller()
            self.backend = 'pynput'
            print("Backend: pynput")

        self.special_characters = {
            '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
            '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
            '_': '-', '+': '=', '{': '[', '}': ']', ':': ';',
            '"': "'", '<': ',', '>': '.', '?': '/'
        }
        
        # Scancode mapping for Linux evdev (partial, common keys)
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

    def press_key(self, note):
        if self.backend == 'evdev':
            self._press_evdev(note)
        else:
            self._press_pynput(note)

    def _press_pynput(self, note):
        if note in self.special_characters:  
            self.keyboard.press(Key.shift)
            self.keyboard.press(self.special_characters[note])
            self.keyboard.release(self.special_characters[note])
            self.keyboard.release(Key.shift)
        elif note.isupper():
            self.keyboard.press(Key.shift)
            self.keyboard.press(note.lower())
            self.keyboard.release(note.lower())
            self.keyboard.release(Key.shift)
        else: 
            self.keyboard.press(note)
            self.keyboard.release(note)

    def _press_evdev(self, note):
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
            self.ui.write(e.EV_KEY, code, 0)
            
            if needs_shift:
                self.ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)
            
            self.ui.syn()

    def stop(self):
        self._stop_event.set()

    def play(self, sheet_content):
        self._stop_event.clear()
        notes = sheet_content
        index = 0

        while index < len(notes) and not self._stop_event.is_set():
            if notes[index].isalnum() or notes[index] in self.special_characters:
                self.press_key(notes[index])

            else:
                if notes[index] == '|': 
                    time.sleep(self.delay * 8)

                if notes[index] == '[':
                    chord = []
                    index += 1
                    while index < len(notes) and notes[index] != ']':
                        if notes[index].isalnum() or notes[index] in self.special_characters:
                            chord.append(notes[index])
                        index += 1

                    for note in chord:
                        self.press_key(note)

            time.sleep(self.delay)
            index += 1

if __name__ == "__main__":
    print("Quickly head over to your desired choice of playing")
    print('Music will start playing in 2 seconds...')
    time.sleep(2)
    
    player = PianoPlayer()
    try:
        with open('sheet.txt') as f:
            content = f.read()
            player.play(content)
    except FileNotFoundError:
        print("Error: sheet.txt not found.")
