import cv2
import time
import threading


from picamera2 import (
    Picamera2
)


from config import (
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_WARMUP,
    FACE_SCAN_WINDOW,
    FACE_RECHECK_DELAY,
    AUTH_SESSION_TIMEOUT,
    MOTION_REARM_WAIT,
    PIR_WARMUP_TIME
)


from face_engine import (
    FaceEngine
)


from hardware import (
    HardwareController
)


from esp32_reader import (
    run_esp32_reader
)


from dashboard import (
    run_dashboard
)


from system_state import (
    update_state
)


# =========================================================
# CENTRAL CONTROLLER
# =========================================================

class CentralController:

    def __init__(self):

        print()
        print("============================================")
        print("          CENTRAL CONTROL SYSTEM")
        print("============================================")
        print()


        # =================================================
        # FACE ENGINE
        # =================================================

        self.face_engine = (
            FaceEngine()
        )


        if not self.face_engine.known_database:

            print()
            print(
                "ERROR: No enrolled faces found."
            )

            print(
                "Run enroll_faces.py first."
            )

            raise RuntimeError(
                "No enrolled faces found."
            )


        # =================================================
        # PI HARDWARE
        # =================================================

        self.hardware = (
            HardwareController()
        )


        # =================================================
        # CAMERA
        # =================================================

        print(
            "Initializing camera..."
        )


        self.picam2 = (
            Picamera2()
        )


        camera_config = (
            self.picam2
            .create_preview_configuration(

                main={

                    "size": (
                        CAMERA_WIDTH,
                        CAMERA_HEIGHT
                    ),

                    "format":
                        "RGB888"
                }
            )
        )


        self.picam2.configure(
            camera_config
        )


        self.camera_running = False

        self.running = True


        # =================================================
        # INITIAL WEB STATE
        # =================================================

        update_state(

            motion=
                False,

            camera=
                "OFF",

            face_status=
                "WAITING",

            person=
                "-",

            face_score=
                0.0,

            gate=
                "LOCKED",

            pi_buzzer=
                "OFF"
        )


    # =====================================================
    # CAMERA START
    # =====================================================

    def start_camera(self):

        if self.camera_running:

            return


        print()
        print(
            "Camera ON"
        )


        self.picam2.start()


        self.camera_running = True


        update_state(
            camera="ON"
        )


        time.sleep(
            CAMERA_WARMUP
        )


    # =====================================================
    # CAMERA STOP
    # =====================================================

    def stop_camera(self):

        if self.camera_running:

            try:

                self.picam2.stop()

            except Exception as error:

                print(
                    "Camera stop warning:",
                    error
                )


            self.camera_running = False


        update_state(
            camera="OFF"
        )


        # =================================================
        # CLOSE POPUP
        # =================================================

        try:

            cv2.destroyWindow(
                "Door Camera"
            )


            cv2.waitKey(
                1
            )


        except Exception:

            pass


        print(
            "Camera OFF"
        )


    # =====================================================
    # DRAW FACE
    # =====================================================

    def draw_face(
        self,
        frame,
        person
    ):

        face = person.get(
            "face"
        )


        if face is None:

            return


        x = int(
            face[0]
        )

        y = int(
            face[1]
        )

        width = int(
            face[2]
        )

        height = int(
            face[3]
        )


        score = person.get(
            "score",
            0.0
        )


        # =================================================
        # KNOWN
        # =================================================

        if (
            person.get(
                "status"
            )
            ==
            "KNOWN"
        ):

            name = person.get(
                "name",
                "KNOWN"
            )


            label = (
                f"{name} "
                f"{score:.2f}"
            )


            color = (
                0,
                255,
                0
            )


        # =================================================
        # UNKNOWN
        # =================================================

        else:

            label = (
                f"UNKNOWN "
                f"{score:.2f}"
            )


            color = (
                0,
                0,
                255
            )


        # =================================================
        # RECTANGLE
        # =================================================

        cv2.rectangle(

            frame,

            (
                x,
                y
            ),

            (
                x + width,
                y + height
            ),

            color,

            2
        )


        # =================================================
        # LABEL
        # =================================================

        cv2.putText(

            frame,

            label,

            (
                x,
                max(
                    30,
                    y - 10
                )
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.7,

            color,

            2
        )


    # =====================================================
    # ONE CAMERA POPUP WINDOW
    #
    # Known:
    # closes immediately
    #
    # Unknown/no face:
    # runs maximum FACE_SCAN_WINDOW = 8 sec
    # then closes
    # =====================================================

    def scan_face_window(self):

        self.start_camera()


        started = (
            time.monotonic()
        )


        any_face_detected = False

        best_unknown_score = 0.0


        result_to_return = {

            "authorized":
                False,

            "name":
                None,

            "score":
                0.0,

            "face_detected":
                False
        }


        try:

            while (
                self.running
                and
                (
                    time.monotonic()
                    -
                    started
                )
                <
                FACE_SCAN_WINDOW
            ):


                # =========================================
                # CAPTURE
                # =========================================

                frame = (
                    self.picam2
                    .capture_array()
                )


                display_frame = (
                    frame.copy()
                )


                # =========================================
                # RECOGNITION
                # =========================================

                recognition = (
                    self.face_engine
                    .recognize_frame(
                        frame
                    )
                )


                # =========================================
                # FACES FOUND
                # =========================================

                if (
                    recognition.get(
                        "status"
                    )
                    ==
                    "FACES_DETECTED"
                ):


                    faces = recognition.get(
                        "faces",
                        []
                    )


                    if faces:

                        any_face_detected = True


                    print()
                    print(
                        "Faces detected:",
                        len(faces)
                    )


                    for person in faces:


                        self.draw_face(

                            display_frame,

                            person
                        )


                        score = person.get(
                            "score",
                            0.0
                        )


                        if (
                            score
                            >
                            best_unknown_score
                        ):

                            best_unknown_score = (
                                score
                            )


                        # =================================
                        # KNOWN
                        # =================================

                        if (
                            person.get(
                                "status"
                            )
                            ==
                            "KNOWN"
                        ):


                            name = person.get(
                                "name",
                                "KNOWN"
                            )


                            print(

                                f"KNOWN: "
                                f"{name} "
                                f"Score: "
                                f"{score:.3f}"
                            )


                            update_state(

                                face_status=
                                    "KNOWN",

                                person=
                                    name,

                                face_score=
                                    score
                            )


                            # Show successful frame briefly

                            cv2.imshow(

                                "Door Camera",

                                display_frame
                            )


                            cv2.waitKey(
                                200
                            )


                            return {

                                "authorized":
                                    True,

                                "name":
                                    name,

                                "score":
                                    score,

                                "face_detected":
                                    True
                            }


                        # =================================
                        # UNKNOWN
                        # =================================

                        else:

                            print(

                                f"UNKNOWN "
                                f"Score: "
                                f"{score:.3f}"
                            )


                    # =====================================
                    # WEB UNKNOWN
                    # =====================================

                    update_state(

                        face_status=
                            "UNKNOWN",

                        person=
                            "-",

                        face_score=
                            best_unknown_score
                    )


                # =========================================
                # NO FACE
                # =========================================

                else:

                    update_state(

                        face_status=
                            "NO FACE",

                        person=
                            "-",

                        face_score=
                            0.0
                    )


                # =========================================
                # REMAINING TIME
                # =========================================

                elapsed = (
                    time.monotonic()
                    -
                    started
                )


                remaining = max(

                    0.0,

                    FACE_SCAN_WINDOW
                    -
                    elapsed
                )


                cv2.putText(

                    display_frame,

                    (
                        f"Scan Time: "
                        f"{remaining:.1f}s"
                    ),

                    (
                        15,
                        30
                    ),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (
                        255,
                        255,
                        255
                    ),

                    2
                )


                # =========================================
                # SHOW POPUP
                # =========================================

                cv2.imshow(

                    "Door Camera",

                    display_frame
                )


                key = (
                    cv2.waitKey(1)
                    &
                    0xFF
                )


                # Manual window close using Q

                if key == ord("q"):

                    print(
                        "Camera scan manually stopped."
                    )

                    break


            # =================================================
            # UNKNOWN / NO FACE WINDOW FINISHED
            # =================================================

            result_to_return = {

                "authorized":
                    False,

                "name":
                    None,

                "score":
                    best_unknown_score,

                "face_detected":
                    any_face_detected
            }


            return result_to_return


        finally:

            # Camera popup always closes
            self.stop_camera()


    # =====================================================
    # WAIT FOR MOTION TO RETURN
    # =====================================================

    def wait_for_motion_rearm(
        self,
        timeout
    ):

        started = (
            time.monotonic()
        )


        while (
            self.running
            and
            (
                time.monotonic()
                -
                started
            )
            <
            timeout
        ):


            if (
                self.hardware
                .motion_detected()
            ):

                return True


            time.sleep(
                0.1
            )


        return False


    # =====================================================
    # MOTION AUTHENTICATION SESSION
    #
    # PIR
    # ↓
    # popup maximum 8 seconds
    # ↓
    # UNKNOWN / NO FACE
    # ↓
    # popup closes
    # ↓
    # buzzer
    # ↓
    # wait 1 second
    # ↓
    # scan again
    #
    # Maximum whole session = 30 sec.
    # =====================================================

    def process_motion_session(self):

        print()
        print("============================================")
        print("            MOTION DETECTED")
        print("============================================")


        update_state(
            motion=True
        )


        session_started = (
            time.monotonic()
        )


        try:

            while (
                self.running
                and
                (
                    time.monotonic()
                    -
                    session_started
                )
                <
                AUTH_SESSION_TIMEOUT
            ):


                print()
                print(
                    "Starting face scan window..."
                )


                # =========================================
                # CAMERA POPUP
                # =========================================

                result = (
                    self.scan_face_window()
                )


                # =========================================
                # KNOWN FACE
                # =========================================

                if result.get(
                    "authorized"
                ):


                    name = result.get(
                        "name"
                    )


                    score = result.get(
                        "score",
                        0.0
                    )


                    print()
                    print("============================================")
                    print("             ACCESS GRANTED")
                    print("============================================")

                    print(
                        "Person:",
                        name
                    )

                    print(
                        f"Score: "
                        f"{score:.3f}"
                    )


                    update_state(

                        face_status=
                            "KNOWN",

                        person=
                            name,

                        face_score=
                            score,

                        gate=
                            "OPEN",

                        pi_buzzer=
                            "OFF"
                    )


                    # =====================================
                    # OPEN GATE
                    # =====================================

                    self.hardware.open_gate()


                    update_state(
                        gate="LOCKED"
                    )


                    return


                # =========================================
                # UNKNOWN
                # =========================================

                if result.get(
                    "face_detected"
                ):


                    score = result.get(
                        "score",
                        0.0
                    )


                    print()
                    print("============================================")
                    print("             UNKNOWN FACE")
                    print("============================================")

                    print(
                        f"Best Score: "
                        f"{score:.3f}"
                    )


                    update_state(

                        face_status=
                            "UNKNOWN",

                        person=
                            "-",

                        face_score=
                            score,

                        gate=
                            "LOCKED"
                    )


                # =========================================
                # NO FACE
                # =========================================

                else:

                    print()
                    print("============================================")
                    print("            NO FACE DETECTED")
                    print("============================================")


                    update_state(

                        face_status=
                            "NO FACE",

                        person=
                            "-",

                        face_score=
                            0.0,

                        gate=
                            "LOCKED"
                    )


                # =========================================
                # BUZZER
                # =========================================

                update_state(
                    pi_buzzer="ON"
                )


                self.hardware.sound_buzzer()


                update_state(
                    pi_buzzer="OFF"
                )


                # =========================================
                # SMALL DELAY
                # =========================================

                time.sleep(
                    FACE_RECHECK_DELAY
                )


                # =========================================
                # PIR STILL HIGH
                # =========================================

                if (
                    self.hardware
                    .motion_detected()
                ):

                    print()
                    print(
                        "Motion still detected."
                    )

                    print(
                        "Starting another face check..."
                    )


                    update_state(
                        motion=True
                    )


                    continue


                # =========================================
                # PIR LOW
                #
                # Wait up to 5 seconds for another motion.
                # =========================================

                update_state(
                    motion=False
                )


                print()
                print(

                    f"Motion ended. "
                    f"Waiting "
                    f"{MOTION_REARM_WAIT}s "
                    f"for another motion..."
                )


                motion_returned = (
                    self.wait_for_motion_rearm(
                        MOTION_REARM_WAIT
                    )
                )


                if motion_returned:

                    print(
                        "Motion detected again."
                    )


                    update_state(
                        motion=True
                    )


                    continue


                print(
                    "No new motion. "
                    "Authentication session ended."
                )


                break


        finally:

            self.stop_camera()


            update_state(
                motion=False
            )


    # =====================================================
    # START BACKGROUND SERVICES
    # =====================================================

    def start_background_services(self):

        # =================================================
        # ESP32 READER THREAD
        # =================================================

        esp32_thread = (
            threading.Thread(

                target=
                    run_esp32_reader,

                daemon=
                    True
            )
        )


        esp32_thread.start()


        print(
            "ESP32 reader thread started."
        )


        # =================================================
        # WEB DASHBOARD THREAD
        # =================================================

        dashboard_thread = (
            threading.Thread(

                target=
                    run_dashboard,

                daemon=
                    True
            )
        )


        dashboard_thread.start()


        print(
            "Web dashboard thread started."
        )


    # =====================================================
    # MAIN RUN
    # =====================================================

    def run(self):

        # =================================================
        # START ESP32 + WEB
        # =================================================

        self.start_background_services()


        # =================================================
        # PIR WARMUP
        # =================================================

        print()
        print(

            f"PIR warming up for "
            f"{PIR_WARMUP_TIME} seconds..."
        )


        time.sleep(
            PIR_WARMUP_TIME
        )


        print()
        print("============================================")
        print("              SYSTEM READY")
        print("============================================")
        print()


        try:

            while self.running:


                print(
                    "Waiting for motion..."
                )


                # =========================================
                # WAIT FOR PIR
                # =========================================

                self.hardware.wait_for_motion()


                # =========================================
                # START SECURITY SESSION
                # =========================================

                self.process_motion_session()


                # =========================================
                # WAIT UNTIL OLD PIR HIGH ENDS
                # =========================================

                while (
                    self.running
                    and
                    self.hardware
                    .motion_detected()
                ):

                    time.sleep(
                        0.1
                    )


        except KeyboardInterrupt:

            print()
            print(
                "CTRL+C pressed."
            )


        finally:

            self.cleanup()


    # =====================================================
    # CLEANUP
    # =====================================================

    def cleanup(self):

        self.running = False


        print()
        print("============================================")
        print("          STOPPING CENTRAL SYSTEM")
        print("============================================")


        # =================================================
        # CAMERA
        # =================================================

        try:

            self.stop_camera()

        except Exception:

            pass


        try:

            self.picam2.close()

        except Exception:

            pass


        # =================================================
        # GPIO
        # =================================================

        try:

            self.hardware.cleanup()

        except Exception as error:

            print(
                "Hardware cleanup error:",
                error
            )


        # =================================================
        # WINDOWS
        # =================================================

        try:

            cv2.destroyAllWindows()

        except Exception:

            pass


        print()
        print(
            "Central system stopped safely."
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    controller = (
        CentralController()
    )


    controller.run()
