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
        self.ui = None
        
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

    def __del__(self):
        """Cleanup resources."""
        if self.ui:
            try:
                self.ui.close()
                print("[LOG] evdev UInput closed.")
            except:
                pass

    def _send_key_event(self, note, is_press):
        """Non-blocking key event sender."""
        if self.backend == 'evdev':
            self._send_evdev(note, is_press)
        else:
            self._send_pynput(note, is_press)

    def _send_pynput(self, note, is_press):
        char = note
        needs_shift = False
        if note in self.special_characters:
            char = self.special_characters[note]
            needs_shift = True
        elif note.isupper():
            char = note.lower()
            needs_shift = True

        if is_press:
            if needs_shift: self.keyboard.press(Key.shift)
            self.keyboard.press(char)
        else:
            self.keyboard.release(char)
            if needs_shift: self.keyboard.release(Key.shift)

    def _send_evdev(self, note, is_press):
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
            val = 1 if is_press else 0
            if needs_shift:
                self.ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, val)
            self.ui.write(e.EV_KEY, code, val)
            self.ui.syn()

    def stop(self):
        self._stop_event.set()

    def _wait_until(self, target_time):
        """High-precision spin-wait loop."""
        while time.perf_counter() < target_time:
            if self._stop_event.is_set():
                return False
            diff = target_time - time.perf_counter()
            if diff > 0.002:
                time.sleep(0.001)
        return True

    def play(self, sheet_content):
        self._stop_event.clear()
        print(f"[LOG] Event-Based Play: {'Humanize ON' if self.humanize else 'OFF'}")

        # Pre-process: Create a flat list of events (time, type, note)
        events = [] # List of (timestamp, type, note)
        current_time = 0.0
        index = 0
        notes = sheet_content

        while index < len(notes):
            char = notes[index]
            
            # Simple sanitization
            if char.isspace():
                index += 1
                continue

            if char.isalnum() or char in self.special_characters:
                # SINGLE NOTE
                self._schedule_note(events, current_time, char)
                current_time += self.delay
            elif char == '|':
                current_time += self.delay * 8
            elif char == '[':
                # CHORD
                chord_notes = []
                index += 1
                while index < len(notes) and notes[index] != ']':
                    if not notes[index].isspace() and (notes[index].isalnum() or notes[index] in self.special_characters):
                        chord_notes.append(notes[index])
                    index += 1
                
                # Schedule chord with micro-offsets if humanized
                for i, chord_note in enumerate(chord_notes):
                    offset = 0
                    if self.humanize:
                        offset = i * random.uniform(0.005, 0.012)
                    self._schedule_note(events, current_time + offset, chord_note)
                
                current_time += self.delay
            index += 1

        # Sort events by time
        events.sort(key=lambda x: x[0])
        
        start_time = time.perf_counter()
        print(f"[LOG] Sequence loaded: {len(events)} events scheduled.")

        for ts, action, note in events:
            if not self._wait_until(start_time + ts):
                break
            
            is_press = (action == "press")
            self._send_key_event(note, is_press)

        print("[LOG] Playback finished or stopped.")

    def _schedule_note(self, event_list, startTime, note):
        """Calculate press and release times for a note."""
        jitter = 0
        if self.humanize:
            jitter = random.uniform(-0.005, 0.005)
        
        press_time = startTime + jitter
        
        # Duration calculation
        duration = self.delay * self.hold_percent
        if self.humanize:
            duration *= random.uniform(0.9, 1.1)
        
        duration = max(0.015, duration) # Safety minimum
        
        # Release humanization (slight offset for release)
        release_jitter = 0
        if self.humanize:
            release_jitter = random.uniform(0, 0.01)

        release_time = press_time + duration + release_jitter
        
        event_list.append((press_time, "press", note))
        event_list.append((release_time, "release", note))

if __name__ == "__main__":
    player = PianoPlayer()
    try:
        with open('sheet.txt') as f:
            content = f.read()
            player.play(content)
    except FileNotFoundError:
        print("[ERR] sheet.txt not found.")
