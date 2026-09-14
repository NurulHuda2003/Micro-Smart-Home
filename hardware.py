import time


from gpiozero import (
    MotionSensor,
    AngularServo,
    OutputDevice
)


from config import (
    PIR_PIN,
    SERVO_PIN,
    BUZZER_PIN,
    SERVO_LOCK_ANGLE,
    SERVO_UNLOCK_ANGLE,
    GATE_OPEN_TIME,
    BUZZER_TIME
)


# =========================================================
# RASPBERRY PI HARDWARE CONTROLLER
# =========================================================

class HardwareController:

    def __init__(self):

        print()
        print("============================================")
        print("       INITIALIZING PI HARDWARE")
        print("============================================")


        # =================================================
        # PIR
        #
        # VCC -> 5V
        # OUT -> GPIO17
        # GND -> GND
        # =================================================

        self.pir = MotionSensor(
            PIR_PIN
        )


        # =================================================
        # SERVO
        #
        # Signal -> GPIO18
        # Power -> external 5V recommended
        # Common GND required
        # =================================================

        self.servo = AngularServo(

            SERVO_PIN,

            min_angle=0,

            max_angle=180,

            min_pulse_width=0.0005,

            max_pulse_width=0.0025,

            initial_angle=
                SERVO_LOCK_ANGLE
        )


        # =================================================
        # ACTIVE BUZZER
        #
        # + -> GPIO23
        # - -> GND
        # =================================================

        self.buzzer = OutputDevice(

            BUZZER_PIN,

            active_high=True,

            initial_value=False
        )


        self.buzzer.off()


        self.lock_gate()


        print(
            "Pi hardware ready."
        )

        print()


    # =====================================================
    # PIR
    # =====================================================

    def wait_for_motion(self):

        self.pir.wait_for_motion()


    def motion_detected(self):

        return (
            self.pir.motion_detected
        )


    # =====================================================
    # GATE LOCK
    # =====================================================

    def lock_gate(self):

        self.servo.angle = (
            SERVO_LOCK_ANGLE
        )


        print(
            "Gate LOCKED"
        )


    # =====================================================
    # GATE OPEN
    # =====================================================

    def open_gate(self):

        print()
        print("============================================")
        print("              GATE OPENING")
        print("============================================")


        self.servo.angle = (
            SERVO_UNLOCK_ANGLE
        )


        print(
            "Gate OPEN"
        )


        time.sleep(
            GATE_OPEN_TIME
        )


        self.lock_gate()


    # =====================================================
    # BUZZER
    # =====================================================

    def sound_buzzer(self):

        print()
        print("============================================")
        print("          SECURITY BUZZER ON")
        print("============================================")


        self.buzzer.on()


        time.sleep(
            BUZZER_TIME
        )


        self.buzzer.off()


        print(
            "Security buzzer OFF"
        )


    # =====================================================
    # FORCE BUZZER OFF
    # =====================================================

    def buzzer_off(self):

        try:

            self.buzzer.off()

        except Exception:

            pass


    # =====================================================
    # CLEANUP
    # =====================================================

    def cleanup(self):

        print()
        print(
            "Cleaning Raspberry Pi hardware..."
        )


        try:

            self.buzzer.off()

        except Exception:

            pass


        try:

            self.servo.angle = (
                SERVO_LOCK_ANGLE
            )

        except Exception:

            pass


        try:

            self.pir.close()

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


        print(
            "Pi hardware cleanup complete."
        )
