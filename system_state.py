import threading
import time

from config import ESP32_CONNECTION_TIMEOUT


# =========================================================
# LOCK
# =========================================================

_state_lock = threading.Lock()


# =========================================================
# GLOBAL STATE
# =========================================================

_state = {

    # -----------------------------------------------------
    # ESP32 Kitchen
    # -----------------------------------------------------

    "esp32_connected": False,

    "esp32_last_update": 0.0,

    "esp32_age": None,

    "gas_adc": 0,

    "gas_ppm": 0,

    "gas_detected": False,

    "flame_detected": False,

    "esp32_state": "WAITING",

    "pump": "OFF",

    "esp32_buzzer": "OFF",


    # -----------------------------------------------------
    # Raspberry Pi Door Security
    # -----------------------------------------------------

    "motion": False,

    "camera": "OFF",

    "face_status": "WAITING",

    "person": "-",

    "face_score": 0.0,

    "gate": "LOCKED",

    "pi_buzzer": "OFF"
}


# =========================================================
# GENERIC UPDATE
# =========================================================

def update_state(**kwargs):

    with _state_lock:

        _state.update(kwargs)


# =========================================================
# UPDATE ESP32
# =========================================================

def update_esp32_state(
    gas_adc,
    gas_ppm,
    gas_detected,
    flame_detected,
    esp32_state,
    pump,
    esp32_buzzer
):

    with _state_lock:

        _state["gas_adc"] = gas_adc

        _state["gas_ppm"] = gas_ppm

        _state["gas_detected"] = gas_detected

        _state["flame_detected"] = flame_detected

        _state["esp32_state"] = esp32_state

        _state["pump"] = pump

        _state["esp32_buzzer"] = esp32_buzzer

        _state["esp32_last_update"] = time.time()

        _state["esp32_connected"] = True


# =========================================================
# GET STATE
# =========================================================

def get_state():

    with _state_lock:

        data = dict(_state)


    last_update = data.get(
        "esp32_last_update",
        0.0
    )


    if last_update <= 0:

        data["esp32_connected"] = False

        data["esp32_age"] = None


    else:

        age = (
            time.time()
            -
            last_update
        )


        data["esp32_age"] = round(
            age,
            1
        )


        if age > ESP32_CONNECTION_TIMEOUT:

            data["esp32_connected"] = False


    return data
