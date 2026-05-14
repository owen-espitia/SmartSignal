***

# SmartSignal: IoT LED Status Indicator for Mobile Surveillance Units

**Author:** Owen Espitia  
**Project Type:** IoT / Embedded Systems / Raspberry Pi  
**Year:** 2026

***

## Overview

SmartSignal is a compact, low-cost IoT device designed to provide real-time, highly visible alerts for Mobile Surveillance Units (MSUs). Instead of relying on mobile apps and push notifications, SmartSignal uses color-coded LED signals that are immediately visible to anyone on-site.

The system integrates with MSU infrastructure using MQTT over cellular (LTE/4G), enabling fast and reliable event notifications without requiring phones or user interaction.

***

## The Problem

Current MSU alert systems depend heavily on mobile devices and applications, which introduces several issues:

*   Alerts are frequently missed or delayed
*   Notification fatigue reduces responsiveness
*   Teams rely on multiple platforms and devices
*   System costs can exceed $50,000–$500,000

***

## The Solution

SmartSignal provides a physical, always-visible alert system mounted directly on the surveillance unit.

LED status indicators communicate system state clearly:

*   Red — Critical alert (intrusion)
*   Orange — Warning (PPE violation)
*   Green — Normal operation
*   Blue — System diagnostics

This approach eliminates reliance on apps and ensures all personnel can see alerts immediately.

***

## Key Features

*   MQTT-based communication model
*   LTE/4G connectivity independent of Wi-Fi
*   RGB LED alert system with multiple patterns (solid, blink, pulse)
*   Configurable event-to-color mappings
*   Optional web dashboard for testing and configuration
*   Automatic reconnection and resilience to connectivity issues
*   Local logging for monitoring and debugging

***

## Technology Stack

### Hardware

*   Raspberry Pi (4B or Zero 2W)
*   LTE/4G cellular modem
*   RGB LED array
*   GPIO expansion board
*   Weatherproof enclosure (IP65 or better)

### Software

*   Python 3
*   Paho MQTT client
*   gpiozero or RPi.GPIO
*   Flask or FastAPI (optional)
*   Raspberry Pi OS

### Communication

*   MQTT protocol
*   MQTT broker (Mosquitto, AWS IoT, or similar)

***

## How It Works

1.  Event Detection  
    An MSU detects an event such as an intrusion or safety violation.

2.  MQTT Event Published
    ```json
    {
      "eventType": "intrusion",
      "severity": "high"
    }
    ```

3.  Command Sent to Device
    ```json
    {
      "action": "displayAlert",
      "color": "red",
      "pattern": "blink",
      "duration": 60
    }
    ```

4.  Device Response
    *   The Raspberry Pi receives the MQTT message
    *   The LED array displays the corresponding alert

***

## Getting Started

### 1. Set Up Raspberry Pi

```bash
sudo apt update
sudo apt install python3 python3-pip
```

***

### 2. Install Dependencies

```bash
pip3 install paho-mqtt gpiozero flask
```

***

### 3. Configure MQTT

Example configuration file:

```json
{
  "broker": "your-broker-ip",
  "port": 1883,
  "topic": "msu/unit-42/command"
}
```

***

### 4. Run the Application

```bash
python3 main.py
```

***

### 5. Send a Test Command

From your laptop:

```bash
ssh pi@<pi-ip> "mosquitto_pub -t msu/unit-42/command -m '{\"color\":\"red\",\"pattern\":\"blink\"}'"
```

***

## Example Use Case

*   A worker enters a restricted area
*   The MSU detects the event
*   SmartSignal displays a red alert
*   All nearby personnel see the alert immediately

***

## Project Structure (Example)

    SmartSignal/
    │── main.py
    │── mqtt_client.py
    │── led_controller.py
    │── config.json
    │── dashboard/
    │   └── app.py
    │── logs/
    │── docs/

***

## Challenges and Considerations

*   Cellular connectivity variability
*   Power efficiency in continuous operation
*   MQTT latency under varying network conditions
*   Outdoor durability and environmental exposure
*   Hardware reliability over time

***

## Roadmap

### Minimum Viable Product

*   MQTT communication
*   LED control system
*   Local configuration file
*   Basic web dashboard

### Future Enhancements

*   Remote configuration updates via MQTT
*   Device health monitoring
*   Failover broker support
*   TLS encryption and authentication
*   Mobile-friendly dashboard

***

## Development Timeline

| Week | Milestone                            |
| ---- | ------------------------------------ |
| 1    | Hardware setup and GPIO testing      |
| 2    | MQTT integration and LED control     |
| 3    | Dashboard implementation and testing |
| 4    | Documentation and final demo         |

***

## Key Differentiators

*   Low cost compared to proprietary systems
*   Immediate, visible alerts without user interaction
*   Open architecture using standard protocols
*   Real-time event response
*   No vendor lock-in

***

## Author

Owen Espitia  
Neumont University

***

## License

MIT

***

## Final Note

SmartSignal is designed with a single objective:

Make critical alerts immediately visible and impossible to miss.

***

### This README has been generated by Microsoft Copilot based on the Project Proposal for this Project.