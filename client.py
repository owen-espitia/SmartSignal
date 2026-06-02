"""SmartSignal laptop client.

Runs person and hat detection using YOLOv8 and forwards alert signals
to a SmartSignal Pi server over HTTP.

Usage:
    python client.py --pi http://<pi-ip>:5000
    python client.py --pi http://<pi-ip>:5000 --camera 1 --model path/to/weights.pt
"""

import argparse
import os
import sys

import cv2
import requests
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# Detection config
# ---------------------------------------------------------------------------

DEBOUNCE = 5  # consecutive frames required before a state change fires

STATE_IDLE   = "idle"
STATE_PERSON = "person"
STATE_NO_HAT = "no_hat"

# Class names the model may use — covers common PPE model naming conventions.
# Adjust if your model uses different labels.
_HAT_CLASSES    = {"hardhat", "hard_hat", "helmet", "hard-hat"}
_NO_HAT_CLASSES = {"no-hardhat", "no_hardhat", "no-helmet", "head"}
_PERSON_CLASSES = {"person"}

_NO_HAT_COLOR = (0, 0, 255)    # red   (BGR)
_PERSON_COLOR = (0, 255, 0)  # yellow (BGR)
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
# Model loading
# ---------------------------------------------------------------------------

def _load_model(model_path: str) -> YOLO:
    # If it looks like a HuggingFace repo ID (contains '/' but isn't a local path),
    # download the weights via huggingface_hub then load locally.
    if "/" in model_path and not os.path.exists(model_path):
        from huggingface_hub import hf_hub_download
        print(f"Downloading model from Hugging Face Hub: {model_path}")
        model_path = hf_hub_download(repo_id=model_path, filename="best.pt")
    return YOLO(model_path)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(pi_url: str, camera_index: int, model_path: str) -> None:
    try:
        r = requests.get(pi_url + "/health", timeout=3)
        d = r.json()
        print(f"Pi online — {d['pixels']} pixels")
    except requests.RequestException as e:
        print(f"[warn] Could not reach Pi at {pi_url}: {e}")
        print("Continuing anyway — alerts will retry each detection event.")

    model = _load_model(model_path)
    print(f"Model loaded: {model_path}")
    print(f"Classes: {list(model.names.values())}")

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        sys.exit(f"[error] Cannot open camera {camera_index}")

    print(f"Camera {camera_index} open. Sending alerts to {pi_url}")
    print("Press Q in the camera window to quit.")

    state           = STATE_IDLE
    candidate       = STATE_IDLE
    candidate_count = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            print("[error] Camera read failed — exiting")
            break

        results = model(frame, verbose=False)[0]

        detected_classes: set[str] = set()
        for box in results.boxes:
            cls_name = model.names[int(box.cls)].lower()
            detected_classes.add(cls_name)

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])

            if cls_name in _NO_HAT_CLASSES:
                color, label = _NO_HAT_COLOR, f"no hat {conf:.0%}"
            elif cls_name in _HAT_CLASSES:
                color, label = _PERSON_COLOR, f"hat {conf:.0%}"
            else:
                color, label = (180, 180, 180), f"{cls_name} {conf:.0%}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # State overlay
        cv2.putText(frame, f"state: {state}", (8, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                    _STATE_COLORS.get(state, (150, 150, 150)), 2)
        cv2.putText(frame, f"pi: {pi_url}", (8, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1)

        # Determine new state — no_hat takes priority over person
        if detected_classes & _NO_HAT_CLASSES:
            new_state = STATE_NO_HAT
        elif detected_classes & (_PERSON_CLASSES | _HAT_CLASSES):
            new_state = STATE_PERSON
        else:
            new_state = STATE_IDLE

        # Debounce
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
    parser.add_argument(
        "--model", default="keremberke/yolov8m-hard-hat-detection",
        help="YOLO model weights path or Hugging Face repo (default: keremberke/yolov8m-hard-hat-detection)"
    )
    args = parser.parse_args()
    run(args.pi, args.camera, args.model)
