import json
import time
import serial


from config import (
    ESP32_SERIAL_PORT,
    ESP32_BAUD
)


from system_state import (
    update_state,
    update_esp32_state
)


# =========================================================
# ESP32 SERIAL READER
# =========================================================

def run_esp32_reader():

    print()
    print("============================================")
    print("          ESP32 SERIAL READER")
    print("============================================")


    while True:

        ser = None


        try:

            print()
            print(
                f"Opening ESP32 UART: "
                f"{ESP32_SERIAL_PORT}"
            )


            # =================================================
            # OPEN UART
            # =================================================

            ser = serial.Serial(

                port=ESP32_SERIAL_PORT,

                baudrate=ESP32_BAUD,

                bytesize=serial.EIGHTBITS,

                parity=serial.PARITY_NONE,

                stopbits=serial.STOPBITS_ONE,

                timeout=1
            )


            # Clear any old garbage
            ser.reset_input_buffer()


            print(
                "ESP32 UART OPEN."
            )

            print(
                "Waiting for kitchen data..."
            )


            # =================================================
            # CONTINUOUS READ
            # =================================================

            while True:


                raw = ser.readline()


                if not raw:

                    continue


                # =================================================
                # DECODE
                # =================================================

                line = raw.decode(
                    "utf-8",
                    errors="ignore"
                ).strip()


                if not line:

                    continue


                print()
                print(
                    "[ESP32 RAW]",
                    line
                )


                # =================================================
                # JSON
                # =================================================

                try:

                    data = json.loads(
                        line
                    )


                except json.JSONDecodeError as error:

                    print(
                        "[ESP32 JSON ERROR]",
                        error
                    )

                    continue


                # =================================================
                # VERIFY KITCHEN DATA
                # =================================================

                if "gas_adc" not in data:

                    print(
                        "[ESP32] Received JSON, "
                        "but kitchen fields not found."
                    )

                    continue


                # =================================================
                # READ VALUES
                # =================================================

                gas_adc = int(
                    data.get(
                        "gas_adc",
                        0
                    )
                )


                gas_ppm = int(
                    data.get(
                        "gas_ppm",
                        0
                    )
                )


                gas_detected = bool(
                    data.get(
                        "gas_detected",
                        False
                    )
                )


                flame_detected = bool(
                    data.get(
                        "flame_detected",
                        False
                    )
                )


                esp32_state = str(
                    data.get(
                        "state",
                        "UNKNOWN"
                    )
                )


                pump = str(
                    data.get(
                        "pump",
                        "OFF"
                    )
                )


                esp32_buzzer = str(
                    data.get(
                        "buzzer",
                        "OFF"
                    )
                )


                # =================================================
                # UPDATE SHARED WEB STATE
                # =================================================

                update_esp32_state(

                    gas_adc=gas_adc,

                    gas_ppm=gas_ppm,

                    gas_detected=gas_detected,

                    flame_detected=flame_detected,

                    esp32_state=esp32_state,

                    pump=pump,

                    esp32_buzzer=esp32_buzzer
                )


                # =================================================
                # CONFIRM UPDATE
                # =================================================

                print(
                    "[KITCHEN UPDATED] "
                    f"ADC={gas_adc} | "
                    f"PPM={gas_ppm} | "
                    f"Gas={gas_detected} | "
                    f"Flame={flame_detected} | "
                    f"State={esp32_state} | "
                    f"Pump={pump} | "
                    f"Buzzer={esp32_buzzer}"
                )


        except serial.SerialException as error:

            print()
            print(
                "[ESP32 SERIAL ERROR]",
                error
            )


            update_state(
                esp32_connected=False
            )


        except Exception as error:

            print()
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


        print()
        print(
            "Retrying ESP32 in 2 seconds..."
        )


        time.sleep(2)
