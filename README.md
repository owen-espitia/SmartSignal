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

| Color     | Meaning                    | Pattern Example   |
| --------- | -------------------------- | ----------------- |
| 🔴 Red    | Critical alert (intrusion) | Blinking / strobe |
| 🟠 Orange | Warning (PPE violation)    | Pulse             |
| 🟢 Green  | Normal operation           | Solid             |
| 🔵 Blue   | System diagnostics         | Slow wave         |

***

## 🚀 Key Features

* 🌐 HTTP-based control (REST API)
* 🎛️ Addressable LED strip (WS2812 / NeoPixel)
* 🎨 Per-pixel color and animation support
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
* Flask or FastAPI (HTTP server)
* `rpi_ws281x` or `neopixel` library
* systemd (service management)

***

## 📂 Project Structure

```
.
├── main.py                # HTTP server entry point
├── led_controller.py      # WS2812 LED control logic
├── patterns.py           # Animation patterns (blink, pulse, wave)
├── config.json           # Configurable settings
├── requirements.txt      # Dependencies
├── smartsignal.service   # systemd service file
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
git clone https://github.com/your-username/smartsignal.git
cd smartsignal
```

***

### 2. Install Dependencies

```bash
sudo apt update
sudo apt install python3 python3-pip
pip3 install -r requirements.txt
```

Example `requirements.txt`:

```
flask
rpi_ws281x
adafruit-circuitpython-neopixel
```

***

### 3. Run the Application

```bash
python3 main.py
```

Default server:

```
http://<espitia_dev-ip>:5000
```

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