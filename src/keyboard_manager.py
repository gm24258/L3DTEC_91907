from libraries import *
from utils import *

from pynput import keyboard
from threading import Lock, Thread

class KeyboardManager:
    def __init__(self):
        self.current_handler = None
        self.lock = Lock()
        self.pressed_keys = set()
        self.listener = None
        self.shutdown = False
        self.last_key_time = 0  # Track last key press time for debouncing

    def start(self):
        """Start the keyboard listener (call ONCE at game launch)."""
        if not self.listener or not self.listener.is_alive():
            self.shutdown = False  # Reset on restart
            self.listener = keyboard.Listener(
                on_press=self._handle_press,
                on_release=self._handle_release
            )
            self.listener.start()

    def _handle_press(self, key):
        """Process key presses (no repeats when holding)."""
        if self.shutdown:  # Immediately return if shutting down
            return
    
        try:
            key_str = key.char if hasattr(key, 'char') else str(key).replace('Key.', '').lower()
            
            with self.lock:
                # Debounce: Ignore keys pressed too quickly (within 50ms)
                current_time = time.time() * 1000  # Convert to milliseconds
                if (current_time - self.last_key_time) < 50:
                    return
                self.last_key_time = current_time

                if self.shutdown or not is_terminal_in_focus():  # Extra check
                    return
                if key_str not in self.pressed_keys:
                    self.pressed_keys.add(key_str)
                    if self.current_handler:
                        Thread(target=self._safe_handler_exec, args=(key_str,), daemon=True).start()
        except Exception as e:
            print(f"[Key Error] {e}")

    def _safe_handler_exec(self, key_str):
        """Safely execute handler with shutdown check."""
        if self.shutdown or not self.current_handler:
            return
        try:
            self.current_handler(key_str)
        except Exception as e:
            print(f"[Handler Error] {e}")

    def _handle_release(self, key):
        """Track key releases (required for no-repeat behavior)."""
        if self.shutdown:  # Skip if shutting down
            return
        try:
            key_str = key.char if hasattr(key, 'char') else str(key).replace('Key.', '').lower()
            with self.lock:
                self.pressed_keys.discard(key_str)
        except Exception as e:
            print(f"[Key Release Error] {e}")

    def set_handler(self, handler):
        """Set the active key handler (call when changing menus)."""
        with self.lock:
            if not self.shutdown:  # Only allow if not shutting down
                self.current_handler = handler
                self.pressed_keys.clear()

    def stop(self):
        """Force-stop the keyboard listener and all key processing."""
        with self.lock:
            self.shutdown = True  # Block all new key processing
            self.current_handler = None
            self.pressed_keys.clear()
        if self.listener:
            self.listener.stop()
            
# Global instance
keyboard_manager = KeyboardManager()