# Micro Smart Home

A Raspberry Pi based smart-home controller with three integrated functions:

- **Door security:** PIR motion detection, face recognition, automatic gate servo control and buzzer alerting.
- **Kitchen safety:** Receives gas/flame status from an ESP32 and opens or closes a ventilation-window servo when gas is detected.
- **Solar monitoring:** Receives ESP32 solar-tracker telemetry and displays it in a live web dashboard.

> This project is intended to run on a Raspberry Pi with the connected hardware. It will not fully run on a normal Windows/Linux computer because it uses Raspberry Pi GPIO and `Picamera2`.

## How the system works

`main.py` is the central controller. When started, it launches three background services:

1. **ESP32 serial reader** - reads newline-delimited JSON over UART, updates the shared system state, and controls the window servo.
2. **Web dashboard** - shows the current state at port `5000` and lets you configure the PIR-2 schedule.
3. **PIR-2 monitor** - watches the second motion sensor only during its configured schedule and sounds the Raspberry Pi buzzer when it detects movement.

The main thread then waits for **PIR-1** motion at the door:

```text
PIR-1 movement
  -> start Raspberry Pi camera
  -> scan faces for up to 8 seconds
  -> compare each face against enrolled embeddings
       -> known face: unlock gate servo for 5 seconds, then lock it
       -> unknown/no face: keep gate locked, sound buzzer, create notification event
```

Face recognition uses **YuNet** to detect faces and **SFace** to create and compare face embeddings. A person is accepted when their best average similarity score meets `MATCH_THRESHOLD` in `config.py` (default: `0.50`).

The ESP32 sends kitchen and solar data through UART. When `gas_detected` changes to `true`, the Raspberry Pi opens the window servo; when it changes to `false`, the window closes. Flame status is displayed but does not control the window in the current code.

The current notification function writes an event to the console. Connect it to Telegram, email, SMS, or another service in `notifier.py` if you need real notifications.

## Hardware connections

These are the Raspberry Pi BCM GPIO pins defined in `config.py`.

| Device | BCM GPIO | Physical pin | Purpose |
| --- | ---: | ---: | --- |
| PIR-1 | GPIO17 | Pin 11 | Door-motion trigger for camera/face verification |
| Gate servo | GPIO18 | Pin 12 | Locks and unlocks the gate |
| Raspberry Pi buzzer | GPIO23 | Pin 16 | Unknown-person and PIR-2 alarms |
| Window servo | GPIO24 | Pin 18 | Opens on ESP32 gas detection |
| PIR-2 | GPIO27 | Pin 13 | Scheduled security-zone motion sensor |
| ESP32 UART | `/dev/ttyAMA0` | N/A | Receives ESP32 JSON at 115200 baud |

Power servos from a suitable external supply and connect its ground to Raspberry Pi ground. Do **not** power a servo directly from a Pi GPIO pin.

## Project layout

| File | Role |
| --- | --- |
| `main.py` | Central controller and door-security workflow |
| `config.py` | Paths, GPIO pins, durations, recognition thresholds, UART and dashboard settings |
| `hardware.py` | PIR sensors, gate servo and Pi buzzer control |
| `face_engine.py` | Face detection, embedding generation and recognition |
| `enroll_faces.py` | Captures face samples and writes enrolled embeddings |
| `esp32_reader.py` | UART reader, kitchen-window servo control and ESP32 telemetry processing |
| `dashboard.py` | Flask dashboard and PIR-2 schedule API |
| `system_state.py` | Thread-safe state shared by the controller, reader and dashboard |
| `notifier.py` | Unknown-person notification hook |
| `models/` | YuNet and SFace ONNX model files |
| `known_faces/` | Enrolled face images and `embeddings.npy` files |

## Prerequisites

- Raspberry Pi OS with a working Raspberry Pi Camera and `Picamera2`
- Python 3 virtual environment (the existing environment is named `objDetection-env`)
- YuNet and SFace ONNX model files:

  ```text
  models/yunet.onnx
  models/sface.onnx
  ```

- Python packages used by the project: `numpy`, `opencv-contrib-python` (with `FaceDetectorYN` and `FaceRecognizerSF`), `gpiozero`, `pyserial`, `Flask`, and `picamera2`

Before running, open `config.py` and make sure `BASE_DIR` matches your actual project folder. For the standard Raspberry Pi location it should be:

```python
BASE_DIR = "/home/pi/object_detection"
```

If your cloned folder has a different name or location, change this value. The model, enrolled-face and schedule paths are built from it.

## Activate and run the system

On the Raspberry Pi, open Terminal and run:

```bash
cd /home/pi/object_detection
source objDetection-env/bin/activate
python main.py
```

Expected startup messages include `ESP32 thread started.`, `Dashboard thread started.`, `PIR-2 thread started.`, and finally `SYSTEM READY` after the PIR warm-up period (10 seconds by default).

To stop the system safely, press `Ctrl+C`. The controller stops the camera, locks the gate, turns off the buzzer and releases GPIO resources. To leave the Python environment after it stops:

```bash
deactivate
```

### Open the dashboard

While `main.py` is running, find the Pi's IP address:

```bash
hostname -I
```

Then open the following address from a phone or computer connected to the same network:

```text
http://<RASPBERRY_PI_IP>:5000
```

The dashboard refreshes automatically and lets you enable/disable PIR-2 and set its start/end times. A schedule that crosses midnight, such as `22:00` to `06:00`, is supported. The selection is saved as `pir2_schedule.json` under `BASE_DIR`.

## Enroll an authorized face

Enroll each authorized person before using door access control:

```bash
cd /home/pi/object_detection
source objDetection-env/bin/activate
python enroll_faces.py Nurul
```

Replace `Nurul` with the person's name. Keep exactly one face in view, look slowly in several directions, and wait for 15 samples. The script writes face images and `embeddings.npy` to:

```text
known_faces/Nurul/
```

Press `q` to cancel enrollment. Restart `main.py` after enrolling a new person so the new embeddings are loaded.

## ESP32 serial message format

The ESP32 must send one JSON object per serial line at **115200 baud**. The reader accepts kitchen and solar fields such as:

```json
{
  "gas_adc": 1200,
  "gas_ppm": 45,
  "gas_detected": false,
  "flame_detected": false,
  "state": "SAFE",
  "buzzer": "OFF",
  "light": "BRIGHT",
  "servo_angle": 90,
  "solar_direction": "CENTER",
  "solar_voltage": 5.12,
  "solar_current": 120.0,
  "solar_power": 0.614,
  "tracking": "ACTIVE"
}
```

Set `ESP32_SERIAL_PORT` in `config.py` if your UART device is not `/dev/ttyAMA0`.

## Important configuration values

Configure these in `config.py` to suit your hardware:

- `MATCH_THRESHOLD` - face-match strictness; test carefully before lowering it.
- `FACE_SCAN_WINDOW` - number of seconds to search for a face after PIR-1 motion.
- `SERVO_LOCK_ANGLE` / `SERVO_UNLOCK_ANGLE` - correct these if the gate moves in the wrong direction.
- `GATE_OPEN_TIME` and `BUZZER_TIME` - gate-open and alarm durations.
- `PIR2_DEFAULT_*` - initial PIR-2 schedule before a dashboard setting is saved.
- `WEB_PORT` and `ESP32_SERIAL_PORT` - network and serial settings.

## Safety and privacy

- Test the servo movement with the gate disconnected before operating a real gate.
- Do not commit `known_faces/`, API keys, passwords, or other private biometric data to a public GitHub repository.
- Verify the face-recognition threshold with multiple people and lighting conditions; it is an access-control convenience feature, not a certified security system.
