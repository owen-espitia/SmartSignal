import logging
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)

try:
    import cv2
    _CV2_AVAILABLE = True
    logger.info("OpenCV %s loaded — vision features enabled", cv2.__version__)
except ImportError:
    _CV2_AVAILABLE = False
    logger.warning("opencv-python not found — vision features disabled")

STATE_IDLE   = "idle"
STATE_PERSON = "person"
STATE_NO_HAT = "no_hat"

# BGR colors for on-frame annotations
_NO_HAT_COLOR = (0, 0, 255)    # red
_PERSON_COLOR = (0, 255, 255)  # yellow


class VisionDetector:
    """Camera capture + detection loop that drives LED state changes.

    Runs a single daemon thread. Frames are JPEG-encoded into a shared
    buffer so any number of MJPEG stream clients can read without stalling
    the capture loop. Detection state is debounced to avoid LED flicker.
    """

    def __init__(self, config: dict, on_state_change: Callable[[str], None]):
        cfg = config.get("vision", {})
        self._camera_index  = cfg.get("camera_index", 0)
        self._width         = cfg.get("width", 640)
        self._height        = cfg.get("height", 480)
        self._detect_every  = cfg.get("detect_every_n_frames", 3)
        self._debounce      = cfg.get("debounce_frames", 5)
        self._on_state_change = on_state_change

        self._state           = STATE_IDLE
        self._candidate       = STATE_IDLE
        self._candidate_count = 0

        self._stop_event  = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._frame_lock  = threading.Lock()
        self._latest_frame: Optional[bytes] = None

        if _CV2_AVAILABLE:
            self._face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            if self._face_cascade.empty():
                logger.error("Face cascade classifier failed to load")
            self._hog = cv2.HOGDescriptor()
            self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        else:
            self._face_cascade = None
            self._hog = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def available(self) -> bool:
        return _CV2_AVAILABLE

    @property
    def state(self) -> str:
        return self._state

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> bool:
        if not _CV2_AVAILABLE:
            return False
        if self.is_running():
            return True
        self._stop_event.clear()
        self._state           = STATE_IDLE
        self._candidate       = STATE_IDLE
        self._candidate_count = 0
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="vision-detector"
        )
        self._thread.start()
        logger.info("Vision detector started (camera %d)", self._camera_index)
        return True

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)
        with self._frame_lock:
            self._latest_frame = None
        self._state = STATE_IDLE
        logger.info("Vision detector stopped")

    def get_frame(self) -> Optional[bytes]:
        with self._frame_lock:
            return self._latest_frame

    # ------------------------------------------------------------------
    # Capture / detection loop
    # ------------------------------------------------------------------

    def _loop(self) -> None:
        cap = cv2.VideoCapture(self._camera_index)
        if not cap.isOpened():
            logger.error("Cannot open camera %d", self._camera_index)
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self._width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)

        frame_n = 0
        people: list = []
        people_hat_status: list = []

        while not self._stop_event.is_set():
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.05)
                continue

            frame_n += 1

            # Run detection every N frames to keep the loop fast on a Pi
            if frame_n % self._detect_every == 0:
                people, _ = self._hog.detectMultiScale(
                    frame, winStride=(8, 8), padding=(4, 4), scale=1.05
                )
                people_hat_status = []
                for (px, py, pw, ph) in people:
                    head_h = max(1, int(ph * 0.35))
                    head_roi = frame[py:py + head_h, px:px + pw]
                    has_hat = True
                    if head_roi.size > 0:
                        gray_head = cv2.cvtColor(head_roi, cv2.COLOR_BGR2GRAY)
                        head_faces = self._face_cascade.detectMultiScale(
                            gray_head, scaleFactor=1.1, minNeighbors=3, minSize=(15, 15)
                        )
                        if len(head_faces) > 0 and head_faces[0][1] < int(head_h * 0.3):
                            has_hat = False
                    people_hat_status.append(has_hat)

            # Annotate bounding boxes
            for i, (x, y, w, h) in enumerate(people):
                has_hat = people_hat_status[i] if i < len(people_hat_status) else True
                color = _PERSON_COLOR if has_hat else _NO_HAT_COLOR
                label = "person" if has_hat else "no hat!"
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, label, (x, y - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            # State overlay (top-left)
            state_color = {
                STATE_IDLE:   (150, 150, 150),
                STATE_PERSON: _PERSON_COLOR,
                STATE_NO_HAT: _NO_HAT_COLOR,
            }
            cv2.putText(frame, self._state, (8, 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                        state_color.get(self._state, (150, 150, 150)), 2)

            # Drive state machine
            no_hat_detected = any(not has_hat for has_hat in people_hat_status)
            if no_hat_detected:
                new_state = STATE_NO_HAT
            elif len(people) > 0:
                new_state = STATE_PERSON
            else:
                new_state = STATE_IDLE
            self._debounce_transition(new_state)

            # Encode and store latest frame
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            with self._frame_lock:
                self._latest_frame = buf.tobytes()

        cap.release()
        with self._frame_lock:
            self._latest_frame = None

    # ------------------------------------------------------------------
    # Debounced state transitions
    # ------------------------------------------------------------------

    def _debounce_transition(self, new_state: str) -> None:
        if new_state == self._candidate:
            self._candidate_count += 1
        else:
            self._candidate       = new_state
            self._candidate_count = 1

        if self._candidate_count >= self._debounce and new_state != self._state:
            old          = self._state
            self._state  = new_state
            self._candidate_count = 0
            logger.info("Detection state: %s → %s", old, new_state)
            self._on_state_change(new_state)
