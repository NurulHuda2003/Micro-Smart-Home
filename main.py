import time
import threading

from datetime import datetime

import cv2

from picamera2 import Picamera2

from config import (
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_WARMUP,
    FACE_SCAN_WINDOW,
    FACE_RECHECK_DELAY,
    PIR_WARMUP_TIME
)

from face_engine import FaceEngine

from hardware import HardwareController

from esp32_reader import run_esp32_reader

from dashboard import run_dashboard

from notifier import (
    send_unknown_notification
)

from system_state import (
    update_state,
    get_state
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


        # =================================================
        # FACE ENGINE
        # =================================================

        self.face_engine = FaceEngine()


        if not self.face_engine.known_database:

            print(
                "WARNING: No enrolled faces found."
            )

            print(
                "Run:"
            )

            print(
                "python enroll_faces.py Nurul"
            )


        # =================================================
        # HARDWARE
        # =================================================

        self.hardware = HardwareController()


        # =================================================
        # CAMERA
        # =================================================

        self.picam2 = Picamera2()


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


        update_state(
            motion=False,
            camera="OFF",
            face_status="WAITING",
            person="-",
            face_score=0.0,
            gate="LOCKED",
            pi_buzzer="OFF",
            pir2_active=False,
            pir2_motion=False
        )


    # =====================================================
    # CAMERA
    # =====================================================

    def start_camera(self):

        if self.camera_running:

            return


        print("Camera ON")


        self.picam2.start()


        self.camera_running = True


        update_state(
            camera="ON"
        )


        time.sleep(
            CAMERA_WARMUP
        )


    def stop_camera(self):

        if self.camera_running:

            try:

                self.picam2.stop()

            except Exception:

                pass


            self.camera_running = False


        update_state(
            camera="OFF"
        )


        try:

            cv2.destroyWindow(
                "Door Camera"
            )

            cv2.waitKey(1)

        except Exception:

            pass


        print("Camera OFF")


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


        x = int(face[0])
        y = int(face[1])
        w = int(face[2])
        h = int(face[3])


        score = person.get(
            "score",
            0.0
        )


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
                f"{name} {score:.2f}"
            )


            color = (
                0,
                255,
                0
            )

        else:

            label = (
                f"UNKNOWN {score:.2f}"
            )


            color = (
                0,
                0,
                255
            )


        cv2.rectangle(
            frame,
            (
                x,
                y
            ),
            (
                x + w,
                y + h
            ),
            color,
            2
        )


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
    # FACE SCAN
    # =====================================================

    def scan_face_window(self):

        self.start_camera()


        start = time.monotonic()


        face_seen = False

        best_unknown_score = 0.0


        try:

            while (
                self.running
                and
                (
                    time.monotonic()
                    -
                    start
                )
                <
                FACE_SCAN_WINDOW
            ):

                frame = (
                    self.picam2
                    .capture_array()
                )


                display = frame.copy()


                result = (
                    self.face_engine
                    .recognize_frame(
                        frame
                    )
                )


                if (
                    result.get(
                        "status"
                    )
                    ==
                    "FACES_DETECTED"
                ):

                    people = result.get(
                        "faces",
                        []
                    )


                    if people:

                        face_seen = True


                    for person in people:

                        self.draw_face(
                            display,
                            person
                        )


                        status = person.get(
                            "status"
                        )


                        score = float(
                            person.get(
                                "score",
                                0.0
                            )
                        )


                        # =================================
                        # KNOWN PERSON
                        # =================================

                        if status == "KNOWN":

                            name = person.get(
                                "name",
                                "KNOWN"
                            )


                            print()
                            print(
                                "KNOWN FACE:",
                                name,
                                score
                            )


                            update_state(
                                face_status="KNOWN",
                                person=name,
                                face_score=score
                            )


                            cv2.imshow(
                                "Door Camera",
                                display
                            )

                            cv2.waitKey(1)


                            return {
                                "known": True,
                                "name": name,
                                "score": score
                            }


                        # =================================
                        # UNKNOWN
                        # =================================

                        if (
                            score
                            >
                            best_unknown_score
                        ):

                            best_unknown_score = score


                            update_state(
                                face_status="UNKNOWN",
                                person="Unknown",
                                face_score=score
                            )


                else:

                    if not face_seen:

                        update_state(
                            face_status="SEARCHING",
                            person="-",
                            face_score=0.0
                        )


                # =========================================
                # SHOW CAMERA
                # =========================================

                cv2.imshow(
                    "Door Camera",
                    display
                )


                key = (
                    cv2.waitKey(1)
                    &
                    0xFF
                )


                if key == ord("q"):

                    break


                time.sleep(
                    FACE_RECHECK_DELAY
                )


        finally:

            self.stop_camera()


        # =================================================
        # NO KNOWN PERSON FOUND
        # =================================================

        if face_seen:

            update_state(
                face_status="UNKNOWN",
                person="Unknown",
                face_score=best_unknown_score
            )


        else:

            update_state(
                face_status="NO_FACE",
                person="-",
                face_score=0.0
            )


        return {
            "known": False,
            "face_seen": face_seen,
            "score": best_unknown_score
        }


    # =====================================================
    # PIR-1 MOTION SESSION
    # =====================================================

    def process_motion_session(self):

        print()
        print("============================================")
        print("           PIR-1 MOTION DETECTED")
        print("============================================")


        update_state(
            motion=True,
            face_status="SEARCHING",
            person="-",
            face_score=0.0
        )


        result = self.scan_face_window()


        # =================================================
        # KNOWN
        # =================================================

        if result.get(
            "known"
        ):

            update_state(
                gate="OPEN",
                pi_buzzer="OFF"
            )


            try:

                self.hardware.open_gate()

            finally:

                update_state(
                    gate="LOCKED"
                )


        # =================================================
        # UNKNOWN / NO FACE
        # =================================================

        else:

            update_state(
                gate="LOCKED",
                pi_buzzer="ON"
            )


            try:

                self.hardware.sound_buzzer()

            finally:

                update_state(
                    pi_buzzer="OFF"
                )


            send_unknown_notification()


        update_state(
            motion=False
        )


    # =====================================================
    # PIR-2 SCHEDULE
    # =====================================================

    def is_pir2_schedule_active(self):

        state = get_state()


        if not state.get(
            "pir2_enabled",
            False
        ):

            return False


        start_text = state.get(
            "pir2_start_time",
            "22:00"
        )


        end_text = state.get(
            "pir2_end_time",
            "06:00"
        )


        try:

            start_time = datetime.strptime(
                start_text,
                "%H:%M"
            ).time()


            end_time = datetime.strptime(
                end_text,
                "%H:%M"
            ).time()


        except Exception:

            return False


        now = datetime.now().time()


        # Same-day schedule
        if start_time < end_time:

            return (
                start_time
                <=
                now
                <
                end_time
            )


        # Overnight schedule
        if start_time > end_time:

            return (
                now
                >=
                start_time
                or
                now
                <
                end_time
            )


        # Same start and end = 24 hours
        return True


    # =====================================================
    # PIR-2 MONITOR
    # =====================================================

    def run_pir2_monitor(self):

        print(
            "PIR-2 monitor started."
        )


        previous_active = None


        while self.running:

            active = (
                self.is_pir2_schedule_active()
            )


            update_state(
                pir2_active=active
            )


            if active != previous_active:

                if active:

                    print(
                        "PIR-2 schedule ACTIVE"
                    )

                else:

                    print(
                        "PIR-2 schedule OFF"
                    )


                previous_active = active


            # Outside schedule
            if not active:

                update_state(
                    pir2_motion=False
                )

                time.sleep(
                    0.3
                )

                continue


            # Read PIR2
            try:

                motion = (
                    self.hardware
                    .pir2_motion_detected()
                )


            except Exception as error:

                print(
                    "PIR-2 error:",
                    error
                )

                time.sleep(
                    0.5
                )

                continue


            if motion:

                print()
                print(
                    "PIR-2 MOTION DETECTED"
                )


                update_state(
                    pir2_motion=True,
                    pi_buzzer="ON"
                )


                try:

                    self.hardware.sound_buzzer()

                finally:

                    update_state(
                        pir2_motion=False,
                        pi_buzzer="OFF"
                    )


                # Rearm
                time.sleep(1)


            else:

                update_state(
                    pir2_motion=False
                )

                time.sleep(
                    0.1
                )


    # =====================================================
    # BACKGROUND SERVICES
    # =====================================================

    def start_background_services(self):

        # ESP32
        thread = threading.Thread(
            target=run_esp32_reader,
            daemon=True
        )

        thread.start()


        print(
            "ESP32 thread started."
        )


        # Dashboard
        thread = threading.Thread(
            target=run_dashboard,
            daemon=True
        )

        thread.start()


        print(
            "Dashboard thread started."
        )


        # PIR2
        thread = threading.Thread(
            target=self.run_pir2_monitor,
            daemon=True
        )

        thread.start()


        print(
            "PIR-2 thread started."
        )


    # =====================================================
    # RUN
    # =====================================================

    def run(self):

        self.start_background_services()


        print()
        print(
            f"PIR warming up "
            f"{PIR_WARMUP_TIME} sec..."
        )


        time.sleep(
            PIR_WARMUP_TIME
        )


        print()
        print("============================================")
        print("              SYSTEM READY")
        print("============================================")


        try:

            while self.running:

                print(
                    "Waiting for PIR-1 motion..."
                )


                self.hardware.wait_for_motion()


                if not self.running:

                    break


                self.process_motion_session()


                # Wait until PIR1 becomes LOW
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
                "CTRL+C"
            )


        finally:

            self.cleanup()


    # =====================================================
    # CLEANUP
    # =====================================================

    def cleanup(self):

        self.running = False


        print()
        print("Stopping system...")


        try:
            self.stop_camera()
        except Exception:
            pass


        try:
            self.picam2.close()
        except Exception:
            pass


        try:
            self.hardware.cleanup()
        except Exception:
            pass


        try:
            cv2.destroyAllWindows()
        except Exception:
            pass


        print(
            "System stopped safely."
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    controller = CentralController()

    controller.run()
