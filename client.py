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
STATE_NO_HAT = "no_hat"

_NO_HAT_COLOR = (0, 0, 255)
_PERSON_COLOR = (0, 255, 255)
_STATE_COLORS = {
    STATE_IDLE:   (150, 150, 150),
    STATE_PERSON: _PERSON_COLOR,
    STATE_NO_HAT: _NO_HAT_COLOR,
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
    if state == STATE_NO_HAT:
        _post(pi_url, "/alert", {"color": "red",    "pattern": "blink", "speed": 0.3})
    elif state == STATE_PERSON:
        _post(pi_url, "/alert", {"color": "yellow", "pattern": "pulse", "speed": 0.5})
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

    state                  = STATE_IDLE
    candidate              = STATE_IDLE
    candidate_count        = 0
    frame_n                = 0
    people: list           = []
    people_hat_status: list = []

    while True:
        ok, frame = cap.read()
        if not ok:
            print("[error] Camera read failed — exiting")
            break

        frame_n += 1

        if frame_n % DETECT_EVERY == 0:
            people, _ = hog.detectMultiScale(
                frame, winStride=(8, 8), padding=(4, 4), scale=1.05
            )
            people_hat_status = []
            for (px, py, pw, ph) in people:
                head_h = max(1, int(ph * 0.35))
                head_roi = frame[py:py + head_h, px:px + pw]
                has_hat = True
                if head_roi.size > 0:
                    gray_head = cv2.cvtColor(head_roi, cv2.COLOR_BGR2GRAY)
                    head_faces = face_cascade.detectMultiScale(
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

        # State + Pi URL overlay
        cv2.putText(frame, f"state: {state}", (8, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                    _STATE_COLORS.get(state, (150, 150, 150)), 2)
        cv2.putText(frame, f"pi: {pi_url}", (8, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1)

        # Debounced state machine
        no_hat_detected = any(not has_hat for has_hat in people_hat_status)
        new_state = (STATE_NO_HAT if no_hat_detected else
                     STATE_PERSON if len(people) > 0 else
                     STATE_IDLE)

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
