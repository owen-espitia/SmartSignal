"""SmartSignal laptop client.

Runs face and person detection on the local webcam and forwards
alert signals to a SmartSignal Pi server over HTTP.

Usage:
    python client.py --pi http://<pi-ip>:5000
    python client.py --pi http://<pi-ip>:5000 --camera 1
"""

import argparse
import sys

import cv2
import requests

# ---------------------------------------------------------------------------
# Detection config
# ---------------------------------------------------------------------------

DETECT_EVERY = 3   # run detection every N frames (keeps CPU reasonable)
DEBOUNCE     = 5   # consecutive frames required before a state change fires

STATE_IDLE   = "idle"
STATE_PERSON = "person"
STATE_FACE   = "face"

_FACE_COLOR   = (0, 200, 255)
_PERSON_COLOR = (50, 255, 50)
_STATE_COLORS = {
    STATE_IDLE:   (150, 150, 150),
    STATE_PERSON: _PERSON_COLOR,
    STATE_FACE:   _FACE_COLOR,
}

# ---------------------------------------------------------------------------
# Pi communication
# ---------------------------------------------------------------------------

def _post(pi_url: str, path: str, body: dict) -> None:
    try:
        requests.post(pi_url + path, json=body, timeout=2)
    except requests.RequestException as e:
        print(f"[warn] Pi unreachable: {e}")


def send_alert(pi_url: str, state: str) -> None:
    if state == STATE_FACE:
        _post(pi_url, "/alert", {"color": "red",    "pattern": "blink", "speed": 0.3})
    elif state == STATE_PERSON:
        _post(pi_url, "/alert", {"color": "orange", "pattern": "pulse", "speed": 0.5})
    else:
        _post(pi_url, "/off", {})


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(pi_url: str, camera_index: int) -> None:
    # Verify Pi is reachable before starting the camera
    try:
        r = requests.get(pi_url + "/health", timeout=3)
        d = r.json()
        print(f"Pi online — {d['pixels']} pixels")
    except requests.RequestException as e:
        print(f"[warn] Could not reach Pi at {pi_url}: {e}")
        print("Continuing anyway — alerts will retry each detection event.")

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        sys.exit(f"[error] Cannot open camera {camera_index}")

    print(f"Camera {camera_index} open. Sending alerts to {pi_url}")
    print("Press Q in the camera window to quit.")

    state           = STATE_IDLE
    candidate       = STATE_IDLE
    candidate_count = 0
    frame_n         = 0
    faces: list     = []
    people: list    = []

    while True:
        ok, frame = cap.read()
        if not ok:
            print("[error] Camera read failed — exiting")
            break

        frame_n += 1

        if frame_n % DETECT_EVERY == 0:
            gray   = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces  = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40)
            )
            people, _ = hog.detectMultiScale(
                frame, winStride=(8, 8), padding=(4, 4), scale=1.05
            )

        # Annotate bounding boxes
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), _FACE_COLOR, 2)
            cv2.putText(frame, "face", (x, y - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, _FACE_COLOR, 1)
        for (x, y, w, h) in people:
            cv2.rectangle(frame, (x, y), (x + w, y + h), _PERSON_COLOR, 2)
            cv2.putText(frame, "person", (x, y - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, _PERSON_COLOR, 1)

        # State + Pi URL overlay
        cv2.putText(frame, f"state: {state}", (8, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                    _STATE_COLORS.get(state, (150, 150, 150)), 2)
        cv2.putText(frame, f"pi: {pi_url}", (8, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1)

        # Debounced state machine
        new_state = STATE_FACE if len(faces) > 0 else (
                    STATE_PERSON if len(people) > 0 else STATE_IDLE)

        if new_state == candidate:
            candidate_count += 1
        else:
            candidate       = new_state
            candidate_count = 1

        if candidate_count >= DEBOUNCE and new_state != state:
            state           = new_state
            candidate_count = 0
            print(f"[detection] {state}")
            send_alert(pi_url, state)

        cv2.imshow("SmartSignal Client", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    _post(pi_url, "/off", {})
    print("LEDs cleared. Bye.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SmartSignal laptop vision client")
    parser.add_argument(
        "--pi", default="http://smartsignal.local:5000",
        help="Base URL of the SmartSignal Pi server (default: http://smartsignal.local:5000)"
    )
    parser.add_argument(
        "--camera", type=int, default=0,
        help="Local camera index to use (default: 0)"
    )
    args = parser.parse_args()
    run(args.pi, args.camera)
