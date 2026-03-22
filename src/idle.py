import time
import threading

class IdleDetector:
    def __init__(self, threshold_min=5):
        self._threshold = threshold_min * 60
        self._last_input = time.monotonic()
        self._idle = False
        self._listeners = []
        self._lock = threading.Lock()
        self._running = False

    def set_threshold(self, minutes):
        self._threshold = minutes * 60

    @property
    def is_idle(self):
        return self._idle

    def on_state_change(self, cb):
        self._listeners.append(cb)

    def _notify(self, idle):
        for cb in self._listeners:
            try:
                cb(idle)
            except Exception:
                pass

    def _on_input(self, *_args, **_kwargs):
        with self._lock:
            self._last_input = time.monotonic()
            if self._idle:
                self._idle = False
                self._notify(False)

    def start(self):
        if self._running:
            return
        self._running = True
        try:
            from pynput import mouse, keyboard
            self._mouse_listener = mouse.Listener(on_move=self._on_input, on_click=self._on_input)
            self._kb_listener = keyboard.Listener(on_press=self._on_input)
            self._mouse_listener.daemon = True
            self._kb_listener.daemon = True
            self._mouse_listener.start()
            self._kb_listener.start()
        except ImportError:
            pass

        t = threading.Thread(target=self._poll, daemon=True)
        t.start()

    def _poll(self):
        while self._running:
            with self._lock:
                elapsed = time.monotonic() - self._last_input
                if not self._idle and elapsed >= self._threshold:
                    self._idle = True
                    self._notify(True)
            time.sleep(1)

    def stop(self):
        self._running = False
        try:
            self._mouse_listener.stop()
            self._kb_listener.stop()
        except Exception:
            pass
