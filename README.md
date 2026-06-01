***

# 📡 SmartSignal (HTTP Edition)

### IoT LED Alert System for Mobile Surveillance Units

**Author:** Owen Espitia  
**Project Type:** IoT / Embedded Systems / Raspberry Pi  
**Year:** 2026

***

## 📖 Overview

SmartSignal is a compact, low-cost IoT device designed to provide real-time, highly visible alerts for Mobile Surveillance Units (MSUs).

Instead of relying on mobile apps and push notifications, SmartSignal uses a **WS2812 addressable LED strip** controlled via HTTP requests, enabling dynamic, highly visible alert patterns.

The system runs a lightweight HTTP server on a Raspberry Pi, allowing external systems to trigger alerts directly over a network.

***

## 🚨 The Problem

Modern MSU alert systems rely heavily on mobile applications and notifications, which introduces several critical issues:

* Alerts are frequently missed or delayed
* Notification fatigue reduces responsiveness
* Teams must monitor multiple devices and platforms
* High system costs ($50,000–$500,000 for full deployments)

***

## ✅ The Solution

SmartSignal replaces app-based alerts with a **physical, always-visible signaling system** mounted directly on the surveillance unit.

Using a **WS2812 LED strip**, SmartSignal can display:

* Solid colors for system states
* Blinking alerts for critical events
* Animated patterns for diagnostics or warnings

All controlled via a simple **RESTful HTTP API**, with no message broker required.

***

## 🎨 LED Alert System

| Color     | Meaning                        | Pattern Example   |
| --------- | ------------------------------ | ----------------- |
| 🔴 Red    | Person detected without a hat  | Blinking          |
| 🟡 Yellow | Person detected (hat worn)     | Pulse             |
| 🟢 Green  | Normal operation               | Solid             |
| 🔵 Blue   | System diagnostics             | Slow wave         |

***

## 👁️ Computer Vision

SmartSignal drives a connected camera to detect **people** and determine whether they are wearing a hat, automatically triggering the appropriate LED alert.

| Detection              | LED Response         |
| ---------------------- | -------------------- |
| Person — no hat        | 🔴 Red blink         |
| Person — hat worn      | 🟡 Yellow pulse      |
| Nothing detected       | LEDs off             |

### How it works

* **Detection** — YOLOv8 runs on the laptop, not the Pi. The Pi only receives HTTP alerts and drives the LEDs.
* Pass any YOLO weights file via `--model`. The default (`yolov8n.pt`) downloads automatically on first run. For best hat detection accuracy, use a model fine-tuned on PPE data (hard hat detection datasets are widely available on Roboflow).
* The client maps detected class names to states using a configurable set — common PPE model label variants (`hardhat`, `hard_hat`, `helmet`, `no-hardhat`, `no_hardhat`, etc.) are all handled out of the box.
* State changes are **debounced** over 5 consecutive frames to prevent LED flicker from single bad detections.
* Bounding boxes are annotated per-detection: yellow for hat worn, red for no hat.

### Configuration (`config.json`)

```json
"vision": {
  "camera_index": 0,
  "width": 640,
  "height": 480,
  "detect_every_n_frames": 3,
  "debounce_frames": 5,
  "auto_alert": true
}
```

Set `auto_alert` to `false` to watch the camera feed without triggering the LEDs.

***

## 🚀 Key Features

* 🌐 HTTP-based control (REST API)
* 🎛️ Addressable LED strip (WS2812 / NeoPixel)
* 🎨 Per-pixel color and animation support
* 👁️ Computer vision: real-time hat compliance detection via YOLOv8 (runs on laptop, alerts forwarded to Pi)
* 📹 Live annotated MJPEG camera stream in the web UI
* ⚡ Runs automatically at boot using `systemd`
* 🔁 Auto-restarts on failure
* 🧪 Easy testing via browser, Postman, or curl
* 🛠 Configurable alert patterns and colors
* 📜 Local logging for debugging and monitoring

***

## 🏗️ System Architecture

```
+-------------------+       HTTP Request       +----------------------+
|   MSU System      |  ─────────────────────▶  |  Raspberry Pi        |
| (or Test Client)  |                          |  SmartSignal Server  |
+-------------------+                          +----------------------+
                                                       │
                                                       ▼
                                            WS2812 LED Strip
                                            (GPIO Data Pin)
```

***

## 🧰 Technology Stack

### Hardware

* Raspberry Pi 4 (or Pi Zero 2W)
* WS2812 / NeoPixel LED strip
* External 5V power supply (recommended)
* Logic level shifter (optional but recommended)
* 330Ω resistor (data line protection)
* 1000µF capacitor (power stability)

***

### Software

* Python 3
* Flask (HTTP server)
* `rpi_ws281x` or `neopixel` library
* OpenCV (`opencv-python-headless`) — face and person detection
* systemd (service management)

***

## 📂 Project Structure

```
.
├── main.py                  # Pi HTTP server — LED control only
├── led_controller.py        # WS2812 LED control logic
├── patterns.py              # Animation patterns (blink, pulse, wave)
├── client.py                # Laptop vision client — YOLOv8 inference → Pi alerts
├── config.json              # Pi server settings (LED hardware, colors)
├── requirements.txt         # Pi dependencies (Flask only)
├── requirements-client.txt  # Laptop dependencies (OpenCV, ultralytics, requests)
├── smartsignal.service      # systemd service file
└── README.md
```

***

## ⚙️ Hardware Setup

### Basic Wiring

| Component   | Connection               |
| ----------- | ------------------------ |
| LED Data In | GPIO18 (Pin 12)          |
| Power (5V)  | External 5V power supply |
| Ground      | Shared with Raspberry Pi |

### Recommended Additions

* **330Ω resistor** between GPIO and data line
* **1000µF capacitor** across power and ground
* **Logic level shifter** (3.3V → 5V)

⚠️ WS2812 strips are sensitive to power spikes—proper wiring is important.

***

## ⚙️ Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/owen-espitia/SmartSignal.git
cd SmartSignal
```

***

### 2. Raspberry Pi — Server Setup

Install system dependencies and create a virtual environment:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

To enable hardware LED control on the Pi, uncomment the `rpi_ws281x` line in `requirements.txt` before installing:

```
# rpi_ws281x>=5.0.0
```

***

### 3. Run the Pi Server

```bash
source .venv/bin/activate
sudo .venv/bin/python main.py
```

> `sudo` is required for GPIO access. The server starts at `http://<pi-ip>:5000`.

Open the web UI in a browser to control alerts manually:

```
http://<pi-ip>:5000
```

***

### 4. Run as a Service (auto-start on boot)

Copy the service file and enable it:

```bash
sudo cp smartsignal.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable smartsignal
sudo systemctl start smartsignal
```

Check status:

```bash
sudo systemctl status smartsignal
```

***

### 5. Laptop Client — Hat Detection

All inference runs on the laptop. The Pi never touches a camera — it only receives HTTP alerts and drives the LEDs.

Install client dependencies (on your laptop, not the Pi):

```bash
pip install -r requirements-client.txt
```

Run the client, pointing it at your Pi:

```bash
python client.py --pi http://<pi-ip>:5000
```

All flags:

```
--pi      Base URL of the Pi server    (default: http://smartsignal.local:5000)
--camera  Local camera index           (default: 0)
--model   Path to YOLO weights file    (default: yolov8n.pt)
```

`yolov8n.pt` downloads automatically on first run. For better hat detection accuracy, supply a YOLO model fine-tuned on PPE/hard hat data via `--model path/to/weights.pt`.

A camera preview window will open with bounding boxes annotated per detection. Press **Q** to quit — the LEDs are cleared automatically on exit.

***

## 🌐 API Endpoints

### ✅ Trigger Alert

```http
POST /alert
```

#### Request Body:

```json
{
  "color": "red",
  "pattern": "blink",
  "duration": 60
}
```

***

### ✅ Custom RGB

```http
POST /rgb
```

```json
{
  "r": 255,
  "g": 50,
  "b": 0
}
```

***

### ✅ Animation Control (Advanced)

```http
POST /pattern
```

```json
{
  "pattern": "wave",
  "color": "blue",
  "speed": 0.1
}
```

***

### ✅ Health Check

```http
GET /health
```

***

### ✅ Start Computer Vision

```http
POST /vision/start
```

***

### ✅ Stop Computer Vision

```http
POST /vision/stop
```

***

### ✅ Vision Status

```http
GET /vision/status
```

Returns:

```json
{
  "available": true,
  "running": true,
  "state": "no_hat"
}
```

***

### ✅ Live Camera Stream (MJPEG)

```http
GET /vision/stream
```

Open directly in a browser or embed as an `<img>` tag. Streams annotated frames with bounding boxes at the camera's native framerate.

***

## 🧪 Testing the System

```bash
curl -X POST http://<espitia_dev-ip>:5000/alert \
-H "Content-Type: application/json" \
-d '{"color":"red","pattern":"blink"}'
```

***

## 🤖 Run on Boot (systemd)

```bash
sudo nano /etc/systemd/system/smartsignal.service
```

```ini
[Unit]
Description=SmartSignal HTTP Server
After=network.target

[Service]
ExecStart=/home/espitia_dev/smartsignal/.venv/bin/python /home/espitia_dev/smartsignal/main.py
WorkingDirectory=/home/espitia_dev/smartsignal
Restart=always
User=espitia_dev

[Install]
WantedBy=multi-user.target
```

***

```bash
sudo systemctl daemon-reload
sudo systemctl enable smartsignal
sudo systemctl start smartsignal
```

***

## 🧪 Example Use Case

1. MSU detects an intrusion
2. System sends HTTP request
3. SmartSignal activates:
   * Red blinking strip
   * High-visibility pattern
4. Personnel immediately see alert

***

## ⚠️ Challenges and Considerations

* Power consumption of LED strips at full brightness
* Timing precision required for WS2812 signals
* Network reliability (especially over LTE)
* Securing HTTP endpoints
* Outdoor enclosure durability

***

## 🛣️ Roadmap

### ✅ MVP

* HTTP control
* WS2812 LED integration
* Basic animation patterns
* systemd auto-start

### 🚀 Future Enhancements

* Dashboard UI for live control
* Pattern editor / animation builder
* Secure API (authentication + HTTPS)
* Remote config updates
* Multi-device synchronization
* More advanced CV models (YOLO, MediaPipe) for improved detection accuracy
* Detection logging and event history

***

## 💡 Key Differentiators

* Addressable LED animations (not just static LEDs)
* Brokerless HTTP architecture
* Highly visible, expressive alerts
* Low cost, scalable, and extensible

***

## 👤 Author

**Owen Espitia**  
Neumont University

***

## 📜 License

MIT License

***

## 🧠 Final Note

SmartSignal is designed with a single objective:

> **Make critical alerts immediately visible and impossible to miss.**

***

## ⭐ Notes for Reviewers

This project demonstrates:

* Embedded systems + real hardware integration
* Addressable LED control (WS2812 timing + patterns)
* REST API design
* Real-time IoT systems
* Practical system-level engineering

***