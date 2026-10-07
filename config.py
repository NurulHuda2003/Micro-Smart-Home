import os


# =========================================================
# PROJECT
# =========================================================

BASE_DIR = "/home/pi/object_detection"


# =========================================================
# FACE MODEL
# =========================================================

YUNET_MODEL = os.path.join(
    BASE_DIR,
    "models",
    "yunet.onnx"
)

SFACE_MODEL = os.path.join(
    BASE_DIR,
    "models",
    "sface.onnx"
)

KNOWN_FACES_DIR = os.path.join(
    BASE_DIR,
    "known_faces"
)


# =========================================================
# CAMERA
# =========================================================

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_WARMUP = 1.0


# =========================================================
# FACE ENROLLMENT
# =========================================================

SAMPLES_NEEDED = 15
CAPTURE_INTERVAL = 0.6


# =========================================================
# FACE RECOGNITION
# =========================================================

FACE_CONFIDENCE = 0.85
MATCH_THRESHOLD = 0.50

FACE_SCAN_WINDOW = 8.0
RECOGNITION_TIMEOUT = 8.0

FACE_RECHECK_DELAY = 0.15

AUTH_SESSION_TIMEOUT = 30.0

MOTION_REARM_WAIT = 5.0
MOTION_COOLDOWN = 2.0


# =========================================================
# GPIO
# =========================================================
#
# PIR-1         GPIO17 -> Physical Pin 11
# Gate Servo    GPIO18 -> Physical Pin 12
# Pi Buzzer     GPIO23 -> Physical Pin 16
# Window Servo  GPIO24 -> Physical Pin 18
# PIR-2         GPIO27 -> Physical Pin 13
#
# =========================================================

PIR_PIN = 17

SERVO_PIN = 18

BUZZER_PIN = 23

WINDOW_SERVO_PIN = 24

PIR2_PIN = 27


# =========================================================
# PIR
# =========================================================

PIR_WARMUP_TIME = 10


# =========================================================
# GATE SERVO
# =========================================================

SERVO_LOCK_ANGLE = 0
SERVO_UNLOCK_ANGLE = 90

GATE_OPEN_TIME = 5


# =========================================================
# WINDOW SERVO
#
# GAS TRUE  -> OPEN
# GAS FALSE -> CLOSED
#
# Flame does NOT control the window.
# =========================================================

WINDOW_CLOSED_ANGLE = 0
WINDOW_OPEN_ANGLE = 90


# =========================================================
# PIR-2 SCHEDULE
# =========================================================

PIR2_DEFAULT_ENABLED = False

PIR2_DEFAULT_START = "22:00"

PIR2_DEFAULT_END = "06:00"

PIR2_SCHEDULE_FILE = os.path.join(
    BASE_DIR,
    "pir2_schedule.json"
)


# =========================================================
# BUZZER
# =========================================================

BUZZER_TIME = 2


# =========================================================
# ESP32 UART
# =========================================================

ESP32_SERIAL_PORT = "/dev/ttyAMA0"

ESP32_BAUD = 115200

ESP32_CONNECTION_TIMEOUT = 3.0


# =========================================================
# WEB DASHBOARD
# =========================================================

WEB_HOST = "0.0.0.0"

WEB_PORT = 5000
