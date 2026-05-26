import math
import time
import threading
import logging
from typing import Optional, Tuple

from led_controller import LEDController

logger = logging.getLogger(__name__)

RGB = Tuple[int, int, int]


class PatternRunner:
    """Manages a single background thread that drives LED animations.

    Calling run() stops any active pattern before starting the new one,
    so callers never need to worry about overlapping threads.
    """

    def __init__(self, led: LEDController):
        self.led = led
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        pattern: str,
        color: RGB,
        speed: float = 0.5,
        duration: Optional[float] = None,
    ) -> None:
        self._cancel()
        self._stop_event = threading.Event()

        fn = {
            "solid":  self._solid,
            "blink":  self._blink,
            "pulse":  self._pulse,
            "wave":   self._wave,
            "strobe": self._strobe,
        }.get(pattern, self._solid)

        self._thread = threading.Thread(
            target=fn,
            args=(color, speed, self._stop_event, duration),
            daemon=True,
            name=f"pattern-{pattern}",
        )
        self._thread.start()
        logger.info("Started pattern '%s' color=%s speed=%s duration=%s", pattern, color, speed, duration)

    def stop(self) -> None:
        self._cancel()
        self.led.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cancel(self) -> None:
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=2.0)

    def _deadline(self, duration: Optional[float]) -> Optional[float]:
        return time.monotonic() + duration if duration else None

    def _expired(self, deadline: Optional[float]) -> bool:
        return deadline is not None and time.monotonic() >= deadline

    # ------------------------------------------------------------------
    # Pattern implementations
    # ------------------------------------------------------------------

    def _solid(self, color: RGB, speed: float, stop: threading.Event, duration: Optional[float]) -> None:
        r, g, b = color
        self.led.set_all(r, g, b)
        deadline = self._deadline(duration)
        while not stop.wait(timeout=0.1):
            if self._expired(deadline):
                break
        self.led.clear()

    def _blink(self, color: RGB, speed: float, stop: threading.Event, duration: Optional[float]) -> None:
        r, g, b = color
        deadline = self._deadline(duration)
        state = True
        while not stop.is_set():
            if self._expired(deadline):
                break
            self.led.set_all(r, g, b) if state else self.led.set_all(0, 0, 0)
            state = not state
            stop.wait(timeout=max(0.05, speed))
        self.led.clear()

    def _pulse(self, color: RGB, speed: float, stop: threading.Event, duration: Optional[float]) -> None:
        r, g, b = color
        deadline = self._deadline(duration)
        phase = 0.0
        while not stop.is_set():
            if self._expired(deadline):
                break
            factor = (math.sin(phase * math.pi * 2) + 1) / 2
            self.led.set_all(int(r * factor), int(g * factor), int(b * factor))
            phase = (phase + speed * 0.03) % 1.0
            stop.wait(timeout=0.02)
        self.led.clear()

    def _wave(self, color: RGB, speed: float, stop: threading.Event, duration: Optional[float]) -> None:
        r, g, b = color
        n = self.led.num_pixels
        deadline = self._deadline(duration)
        offset = 0.0
        while not stop.is_set():
            if self._expired(deadline):
                break
            for i in range(n):
                factor = (math.sin((i / n + offset) * math.pi * 2) + 1) / 2
                self.led.set_pixel(i, int(r * factor), int(g * factor), int(b * factor))
            self.led.show()
            offset = (offset + speed * 0.02) % 1.0
            stop.wait(timeout=0.02)
        self.led.clear()

    def _strobe(self, color: RGB, speed: float, stop: threading.Event, duration: Optional[float]) -> None:
        r, g, b = color
        deadline = self._deadline(duration)
        interval = max(0.03, speed * 0.1)
        while not stop.is_set():
            if self._expired(deadline):
                break
            self.led.set_all(r, g, b)
            if stop.wait(timeout=interval):
                break
            self.led.set_all(0, 0, 0)
            stop.wait(timeout=interval)
        self.led.clear()
