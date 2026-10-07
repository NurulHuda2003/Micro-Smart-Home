import time
import threading

from gpiozero import (
    MotionSensor,
    AngularServo,
    OutputDevice
)

from config import (
    PIR_PIN,
    PIR2_PIN,
    SERVO_PIN,
    BUZZER_PIN,
    SERVO_LOCK_ANGLE,
    SERVO_UNLOCK_ANGLE,
    GATE_OPEN_TIME,
    BUZZER_TIME
)


class HardwareController:

    def __init__(self):

        print()
        print("============================================")
        print("       INITIALIZING PI HARDWARE")
        print("============================================")


        # =================================================
        # PIR-1
        # GPIO17 / Physical Pin 11
        # =================================================

        self.pir = MotionSensor(
            PIR_PIN,
            queue_len=5,
            sample_rate=10,
            threshold=0.8
        )


        # =================================================
        # PIR-2
        # GPIO27 / Physical Pin 13
        # =================================================

        self.pir2 = MotionSensor(
            PIR2_PIN,
            queue_len=5,
            sample_rate=10,
            threshold=0.6
        )


        # =================================================
        # GATE SERVO
        # GPIO18 / Physical Pin 12
        # =================================================

        self.servo = AngularServo(
            SERVO_PIN,
            min_angle=0,
            max_angle=180,
            min_pulse_width=0.0005,
            max_pulse_width=0.0025,
            initial_angle=SERVO_LOCK_ANGLE
        )


        # =================================================
        # PI BUZZER
        # GPIO23 / Physical Pin 16
        # =================================================

        self.buzzer = OutputDevice(
            BUZZER_PIN,
            active_high=True,
            initial_value=False
        )


        self._buzzer_lock = threading.Lock()


        self.buzzer.off()

        self.lock_gate()


        print(f"PIR-1: GPIO{PIR_PIN}")
        print(f"PIR-2: GPIO{PIR2_PIN}")
        print(f"Gate Servo: GPIO{SERVO_PIN}")
        print(f"Buzzer: GPIO{BUZZER_PIN}")

        print("Pi hardware ready.")


    # =====================================================
    # PIR-1
    # =====================================================

    def wait_for_motion(self):

        self.pir.wait_for_motion()


    def motion_detected(self):

        return self.pir.motion_detected


    # =====================================================
    # PIR-2
    # =====================================================

    def pir2_motion_detected(self):

        return self.pir2.motion_detected


    # =====================================================
    # GATE
    # =====================================================

    def lock_gate(self):

        self.servo.angle = SERVO_LOCK_ANGLE

        print("Gate LOCKED")


    def unlock_gate(self):

        self.servo.angle = SERVO_UNLOCK_ANGLE

        print("Gate OPEN")


    def open_gate(self):

        print()
        print("============================================")
        print("              GATE OPENING")
        print("============================================")

        self.unlock_gate()

        time.sleep(
            GATE_OPEN_TIME
        )

        self.lock_gate()


    # =====================================================
    # BUZZER
    # =====================================================

    def sound_buzzer(self):

        with self._buzzer_lock:

            print()
            print("============================================")
            print("          SECURITY BUZZER ON")
            print("============================================")

            self.buzzer.on()

            time.sleep(
                BUZZER_TIME
            )

            self.buzzer.off()

            print("Security buzzer OFF")


    def buzzer_off(self):

        try:

            self.buzzer.off()

        except Exception:

            pass


    # =====================================================
    # CLEANUP
    # =====================================================

    def cleanup(self):

        print("Cleaning hardware...")


        try:
            self.buzzer.off()
        except Exception:
            pass


        try:
            self.servo.angle = SERVO_LOCK_ANGLE
        except Exception:
            pass


        try:
            self.pir.close()
        except Exception:
            pass


        try:
            self.pir2.close()
        except Exception:
            pass


        try:
            self.servo.close()
        except Exception:
            pass


        try:
            self.buzzer.close()
        except Exception:
            pass


        print("Hardware cleanup complete.")
