#!/usr/bin/env python3

import json
import math
import time

import serial

from gpiozero import AngularServo

from config import (
    ESP32_SERIAL_PORT,
    ESP32_BAUD,
    WINDOW_SERVO_PIN,
    WINDOW_CLOSED_ANGLE,
    WINDOW_OPEN_ANGLE
)

from system_state import update_state


# =========================================================
# HELPERS
# =========================================================

def to_bool(value):

    if isinstance(
        value,
        bool
    ):
        return value


    if isinstance(
        value,
        (int, float)
    ):
        return value != 0


    if isinstance(
        value,
        str
    ):

        return (
            value
            .strip()
            .lower()
            in (
                "true",
                "1",
                "yes",
                "on",
                "detected"
            )
        )


    return False


def safe_int(
    value,
    default=0
):

    try:

        return int(
            value
        )

    except Exception:

        return default


def safe_float(
    value,
    default=0.0
):

    try:

        number = float(
            value
        )


        if (
            math.isnan(number)
            or
            math.isinf(number)
        ):

            return default


        return number


    except Exception:

        return default


# =========================================================
# ESP32 READER
# =========================================================

def run_esp32_reader():

    print()
    print("============================================")
    print("          ESP32 SERIAL READER")
    print("============================================")


    # =====================================================
    # WINDOW SERVO
    #
    # Raspberry Pi GPIO24
    #
    # Gas detected -> OPEN
    # Gas safe     -> CLOSED
    # =====================================================

    window_servo = None


    try:

        window_servo = AngularServo(
            WINDOW_SERVO_PIN,
            min_angle=0,
            max_angle=90,
            min_pulse_width=0.0005,
            max_pulse_width=0.0025,
            initial_angle=WINDOW_CLOSED_ANGLE
        )


        print(
            "Window servo ready:",
            f"GPIO{WINDOW_SERVO_PIN}"
        )


    except Exception as error:

        print(
            "[WINDOW SERVO ERROR]",
            repr(error)
        )


    previous_gas = None


    # =====================================================
    # RECONNECT LOOP
    # =====================================================

    while True:

        ser = None


        try:

            print()
            print(
                "Opening ESP32 UART:",
                ESP32_SERIAL_PORT
            )


            ser = serial.Serial(
                port=ESP32_SERIAL_PORT,
                baudrate=ESP32_BAUD,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )


            ser.reset_input_buffer()


            print(
                "ESP32 UART connected."
            )


            # =================================================
            # READ LOOP
            # =================================================

            while True:

                raw = ser.readline()


                if not raw:

                    continue


                line = (
                    raw
                    .decode(
                        "utf-8",
                        errors="ignore"
                    )
                    .strip()
                )


                if not line:

                    continue


                print(
                    "[ESP32 RAW]",
                    line
                )


                # =============================================
                # JSON
                # =============================================

                try:

                    data = json.loads(
                        line
                    )


                except json.JSONDecodeError:

                    # ESP32 Serial debug messages are ignored.
                    continue


                # =============================================
                # VERIFY OUR JSON
                # =============================================

                if (
                    "gas_detected" not in data
                    and
                    "solar_voltage" not in data
                ):

                    continue


                # =============================================
                # KITCHEN
                # =============================================

                gas_adc = safe_int(
                    data.get(
                        "gas_adc",
                        0
                    )
                )


                gas_ppm = safe_int(
                    data.get(
                        "gas_ppm",
                        0
                    )
                )


                gas_detected = to_bool(
                    data.get(
                        "gas_detected",
                        False
                    )
                )


                flame_detected = to_bool(
                    data.get(
                        "flame_detected",
                        False
                    )
                )


                kitchen_state = str(
                    data.get(
                        "state",
                        "UNKNOWN"
                    )
                ).upper()


                kitchen_buzzer = str(
                    data.get(
                        "buzzer",
                        "OFF"
                    )
                ).upper()


                # =============================================
                # SOLAR
                # =============================================

                light_status = str(
                    data.get(
                        "light",
                        "UNKNOWN"
                    )
                ).upper()


                solar_servo_angle = safe_int(
                    data.get(
                        "servo_angle",
                        90
                    ),
                    90
                )


                solar_direction = str(
                    data.get(
                        "solar_direction",
                        "CENTER"
                    )
                ).upper()


                solar_voltage = safe_float(
                    data.get(
                        "solar_voltage",
                        0.0
                    )
                )


                solar_current = safe_float(
                    data.get(
                        "solar_current",
                        0.0
                    )
                )


                solar_power = safe_float(
                    data.get(
                        "solar_power",
                        0.0
                    )
                )


                solar_tracking = str(
                    data.get(
                        "tracking",
                        "UNKNOWN"
                    )
                ).upper()


                # =============================================
                # WINDOW CONTROL
                #
                # GAS ONLY
                # =============================================

                if gas_detected:

                    window_status = "OPEN"

                else:

                    window_status = "CLOSED"


                # =============================================
                # MOVE ONLY WHEN GAS CHANGES
                # =============================================

                if (
                    gas_detected
                    !=
                    previous_gas
                ):

                    if window_servo is not None:

                        try:

                            if gas_detected:

                                window_servo.angle = (
                                    WINDOW_OPEN_ANGLE
                                )

                                print(
                                    "GAS DETECTED -> "
                                    "WINDOW OPEN"
                                )

                            else:

                                window_servo.angle = (
                                    WINDOW_CLOSED_ANGLE
                                )

                                print(
                                    "GAS SAFE -> "
                                    "WINDOW CLOSED"
                                )


                        except Exception as error:

                            print(
                                "[WINDOW SERVO ERROR]",
                                repr(error)
                            )


                    previous_gas = gas_detected


                # =============================================
                # CENTRAL STATE
                # =============================================

                update_state(

                    esp32_connected=True,

                    esp32_last_update=time.time(),


                    # Kitchen
                    gas_adc=gas_adc,

                    gas_ppm=gas_ppm,

                    gas_detected=gas_detected,

                    flame_detected=flame_detected,

                    esp32_state=kitchen_state,

                    esp32_buzzer=kitchen_buzzer,

                    pump="OFF",

                    window=window_status,


                    # Solar
                    light_status=light_status,

                    solar_servo_angle=solar_servo_angle,

                    solar_direction=solar_direction,

                    solar_voltage=solar_voltage,

                    solar_current=solar_current,

                    solar_power=solar_power,

                    solar_tracking=solar_tracking
                )


                print(
                    "[SYSTEM] "
                    f"Gas={gas_detected} | "
                    f"Flame={flame_detected} | "
                    f"Window={window_status} | "
                    f"Solar={solar_voltage:.2f}V "
                    f"{solar_current:.2f}mA "
                    f"{solar_power:.3f}W | "
                    f"Angle={solar_servo_angle} | "
                    f"Light={light_status}"
                )


        except serial.SerialException as error:

            print(
                "[ESP32 SERIAL ERROR]",
                repr(error)
            )


            update_state(
                esp32_connected=False
            )


        except Exception as error:

            print(
                "[ESP32 READER ERROR]",
                repr(error)
            )


            update_state(
                esp32_connected=False
            )


        finally:

            if ser is not None:

                try:
                    ser.close()
                except Exception:
                    pass


        print(
            "Retrying ESP32 in 2 seconds..."
        )


        time.sleep(2)
