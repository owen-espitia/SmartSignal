import json
import logging
import time
from pathlib import Path

from flask import Flask, request, jsonify, render_template, Response

from led_controller import LEDController
from patterns import PatternRunner
from vision import VisionDetector, STATE_IDLE, STATE_PERSON, STATE_FACE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.json"
config = json.loads(CONFIG_PATH.read_text())

app = Flask(__name__)
led = LEDController(config)
runner = PatternRunner(led)

NAMED_COLORS: dict[str, tuple[int, int, int]] = {
    name: tuple(rgb) for name, rgb in config["colors"].items()  # type: ignore[assignment]
}

VALID_PATTERNS = {"solid", "blink", "pulse", "wave", "strobe"}


def resolve_color(name: str) -> tuple[int, int, int]:
    return NAMED_COLORS.get(name.lower(), (255, 255, 255))


def _on_vision_state(state: str) -> None:
    if not config.get("vision", {}).get("auto_alert", True):
        return
    if state == STATE_FACE:
        runner.run("blink", resolve_color("red"), speed=0.3)
    elif state == STATE_PERSON:
        runner.run("pulse", resolve_color("orange"), speed=0.5)
    elif state == STATE_IDLE:
        runner.stop()


vision = VisionDetector(config, _on_vision_state)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "pixels": led.num_pixels})


@app.route("/alert", methods=["POST"])
def alert():
    """Trigger a named alert by color + pattern.

    Body: { "color": "red", "pattern": "blink", "duration": 60, "speed": 0.5 }
    """
    data = request.get_json(force=True, silent=True) or {}

    color_name = str(data.get("color", "red"))
    pattern = str(data.get("pattern", "blink"))
    duration = _parse_float(data.get("duration"))
    speed = float(data.get("speed", 0.5))

    if pattern not in VALID_PATTERNS:
        return jsonify({"error": f"Unknown pattern '{pattern}'. Valid: {sorted(VALID_PATTERNS)}"}), 400

    color = resolve_color(color_name)
    runner.run(pattern, color, speed=speed, duration=duration)

    logger.info("Alert — color=%s pattern=%s duration=%s", color_name, pattern, duration)
    return jsonify({"status": "ok", "color": color_name, "pattern": pattern, "duration": duration})


@app.route("/rgb", methods=["POST"])
def rgb():
    """Show a solid custom RGB color.

    Body: { "r": 255, "g": 50, "b": 0 }
    """
    data = request.get_json(force=True, silent=True) or {}

    try:
        r = _clamp(int(data["r"]))
        g = _clamp(int(data["g"]))
        b = _clamp(int(data["b"]))
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Body must include integer fields r, g, b (0–255)"}), 400

    runner.run("solid", (r, g, b))

    logger.info("RGB — r=%d g=%d b=%d", r, g, b)
    return jsonify({"status": "ok", "r": r, "g": g, "b": b})


@app.route("/pattern", methods=["POST"])
def pattern():
    """Run an animation pattern with fine-grained control.

    Body: { "pattern": "wave", "color": "blue", "speed": 0.1, "duration": 30 }
    """
    data = request.get_json(force=True, silent=True) or {}

    pattern_name = str(data.get("pattern", "solid"))
    color_name = str(data.get("color", "white"))
    speed = float(data.get("speed", 0.5))
    duration = _parse_float(data.get("duration"))

    if pattern_name not in VALID_PATTERNS:
        return jsonify({"error": f"Unknown pattern '{pattern_name}'. Valid: {sorted(VALID_PATTERNS)}"}), 400

    color = resolve_color(color_name)
    runner.run(pattern_name, color, speed=speed, duration=duration)

    logger.info("Pattern — %s color=%s speed=%s duration=%s", pattern_name, color_name, speed, duration)
    return jsonify({"status": "ok", "pattern": pattern_name, "color": color_name, "speed": speed})


@app.route("/off", methods=["POST"])
def off():
    """Stop all animations and turn off the LEDs."""
    runner.stop()
    logger.info("LEDs turned off")
    return jsonify({"status": "ok"})


@app.route("/vision/start", methods=["POST"])
def vision_start():
    if not vision.available:
        return jsonify({"error": "opencv-python is not installed"}), 503
    vision.start()
    return jsonify({"status": "ok", "running": vision.is_running()})


@app.route("/vision/stop", methods=["POST"])
def vision_stop():
    vision.stop()
    return jsonify({"status": "ok"})


@app.route("/vision/status", methods=["GET"])
def vision_status():
    return jsonify({
        "available": vision.available,
        "running":   vision.is_running(),
        "state":     vision.state,
    })


@app.route("/vision/stream")
def vision_stream():
    if not vision.is_running():
        return jsonify({"error": "Vision is not running"}), 400

    def generate():
        while vision.is_running():
            frame = vision.get_frame()
            if frame is None:
                time.sleep(0.05)
                continue
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(v: int) -> int:
    return max(0, min(255, v))


def _parse_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    host = config["server"]["host"]
    port = config["server"]["port"]
    debug = config["server"]["debug"]
    logger.info("SmartSignal starting on %s:%d", host, port)
    app.run(host=host, port=port, debug=debug, threaded=True)
