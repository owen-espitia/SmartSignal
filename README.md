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

* **Person detection** — OpenCV HOG + SVM descriptor (`HOGDescriptor_getDefaultPeopleDetector()`)
* **Hat detection** — for each detected person, the top 35% of their bounding box (head region) is cropped and run through an OpenCV Haar face cascade. If the face sits in the top 30% of that crop (minimal clearance above), there is no room for a hat — the person is flagged as `no_hat`. No additional model downloads required.
* Detection runs every 3rd frame (configurable) to stay responsive on a Raspberry Pi
* State changes are **debounced** over 5 consecutive frames to prevent LED flicker from single bad detections
* Bounding boxes are annotated `"person"` (yellow) or `"no hat!"` (red) per-person in the live feed
* An annotated **MJPEG live stream** is served at `/vision/stream` and embedded directly in the web UI

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
* 👁️ Computer vision: real-time person detection and hat compliance checking via OpenCV
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
├── main.py                # HTTP server entry point
├── led_controller.py      # WS2812 LED control logic
├── patterns.py            # Animation patterns (blink, pulse, wave)
├── vision.py              # Computer vision: person detection and hat compliance
├── config.json            # Configurable settings
├── requirements.txt       # Dependencies
├── smartsignal.service    # systemd service file
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

The laptop client runs person and hat detection on your local webcam and forwards alerts to the Pi over HTTP.

Install client dependencies (on your laptop, not the Pi):

```bash
pip install -r requirements-client.txt
```

Run the client, pointing it at your Pi:

```bash
python client.py --pi http://<pi-ip>:5000
```

Optional flags:

```
--pi      Base URL of the Pi server (default: http://smartsignal.local:5000)
--camera  Local camera index to use   (default: 0)
```

A camera preview window will open. Press **Q** to quit — the LEDs will be cleared automatically on exit.

***

### 6. Enable Vision on the Pi (optional)

If a camera is attached directly to the Pi, you can start vision detection via the API:

```bash
curl -X POST http://<pi-ip>:5000/vision/start
```

View the live annotated stream in a browser:

```
http://<pi-ip>:5000/vision/stream
```

Stop detection:

```bash
curl -X POST http://<pi-ip>:5000/vision/stop
```

Set `"auto_alert": false` in `config.json` to watch the stream without triggering the LEDs.

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