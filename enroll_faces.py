import os
import sys
import time

import cv2
import numpy as np

from picamera2 import Picamera2

from config import (
    YUNET_MODEL,
    SFACE_MODEL,
    KNOWN_FACES_DIR,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    SAMPLES_NEEDED,
    CAPTURE_INTERVAL,
    FACE_CONFIDENCE
)


# =========================================================
# PERSON NAME
# =========================================================

if len(sys.argv) < 2:

    print()
    print("Person name required.")
    print()
    print("Example:")
    print("python enroll_faces.py Nurul")

    sys.exit(1)


person_name = sys.argv[1].strip()


if not person_name:

    print("Invalid person name.")

    sys.exit(1)


# =========================================================
# MODEL CHECK
# =========================================================

if not os.path.exists(
    YUNET_MODEL
):

    print(
        "YuNet model not found:",
        YUNET_MODEL
    )

    sys.exit(1)


if not os.path.exists(
    SFACE_MODEL
):

    print(
        "SFace model not found:",
        SFACE_MODEL
    )

    sys.exit(1)


# =========================================================
# PERSON FOLDER
# =========================================================

os.makedirs(
    KNOWN_FACES_DIR,
    exist_ok=True
)


person_dir = os.path.join(
    KNOWN_FACES_DIR,
    person_name
)


os.makedirs(
    person_dir,
    exist_ok=True
)


# =========================================================
# FACE MODELS
# =========================================================

detector = cv2.FaceDetectorYN.create(
    YUNET_MODEL,
    "",
    (
        CAMERA_WIDTH,
        CAMERA_HEIGHT
    ),
    FACE_CONFIDENCE,
    0.3,
    5000
)


recognizer = cv2.FaceRecognizerSF.create(
    SFACE_MODEL,
    ""
)


# =========================================================
# CAMERA
# =========================================================

picam2 = Picamera2()


camera_config = (
    picam2.create_preview_configuration(

        main={
            "size": (
                CAMERA_WIDTH,
                CAMERA_HEIGHT
            ),
            "format": "RGB888"
        }
    )
)


picam2.configure(
    camera_config
)


picam2.start()


time.sleep(2)


# =========================================================
# VARIABLES
# =========================================================

embeddings = []

sample_count = 0

last_capture_time = 0.0


print()
print("============================================")
print("          FACE ENROLLMENT START")
print("============================================")
print("Person:", person_name)
print()
print("Look at camera.")
print("Move your head slowly left/right/up/down.")
print("Only one person should be visible.")
print("Press Q to cancel.")
print()


# =========================================================
# LOOP
# =========================================================

try:

    while (
        sample_count
        <
        SAMPLES_NEEDED
    ):

        frame = picam2.capture_array()


        height, width = frame.shape[:2]


        detector.setInputSize(
            (
                width,
                height
            )
        )


        _, faces = detector.detect(
            frame
        )


        display = frame.copy()


        status_text = "No face"

        status_color = (
            0,
            0,
            255
        )


        if faces is not None:

            if len(faces) == 1:

                face = faces[0]


                x = int(face[0])
                y = int(face[1])
                w = int(face[2])
                h = int(face[3])


                cv2.rectangle(
                    display,
                    (
                        x,
                        y
                    ),
                    (
                        x + w,
                        y + h
                    ),
                    (
                        0,
                        255,
                        0
                    ),
                    2
                )


                status_text = (
                    f"Face {sample_count}/"
                    f"{SAMPLES_NEEDED}"
                )


                status_color = (
                    0,
                    255,
                    0
                )


                now = time.time()


                if (
                    now
                    -
                    last_capture_time
                    >=
                    CAPTURE_INTERVAL
                ):

                    try:

                        aligned = recognizer.alignCrop(
                            frame,
                            face
                        )


                        feature = recognizer.feature(
                            aligned
                        )


                        feature = (
                            feature
                            .flatten()
                            .astype(np.float32)
                        )


                        norm = np.linalg.norm(
                            feature
                        )


                        if norm == 0:

                            continue


                        feature = (
                            feature
                            /
                            norm
                        )


                        embeddings.append(
                            feature
                        )


                        sample_count += 1

                        last_capture_time = now


                        filename = (
                            f"face_{sample_count:02d}.jpg"
                        )


                        cv2.imwrite(
                            os.path.join(
                                person_dir,
                                filename
                            ),
                            aligned
                        )


                        print(
                            f"Captured "
                            f"{sample_count}/"
                            f"{SAMPLES_NEEDED}"
                        )


                    except Exception as error:

                        print(
                            "Face processing error:",
                            error
                        )


            elif len(faces) > 1:

                status_text = (
                    "Multiple faces detected"
                )


                status_color = (
                    0,
                    165,
                    255
                )


        cv2.putText(
            display,
            status_text,
            (
                20,
                35
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            status_color,
            2
        )


        cv2.putText(
            display,
            f"Person: {person_name}",
            (
                20,
                70
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (
                255,
                255,
                255
            ),
            2
        )


        cv2.putText(
            display,
            "Press Q to exit",
            (
                20,
                460
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (
                255,
                255,
                255
            ),
            2
        )


        cv2.imshow(
            "Face Enrollment",
            display
        )


        key = cv2.waitKey(1) & 0xFF


        if key == ord("q"):

            break


finally:

    picam2.stop()

    picam2.close()

    cv2.destroyAllWindows()


# =========================================================
# SAVE
# =========================================================

if (
    len(embeddings)
    ==
    SAMPLES_NEEDED
):

    embeddings_array = np.array(
        embeddings,
        dtype=np.float32
    )


    path = os.path.join(
        person_dir,
        "embeddings.npy"
    )


    np.save(
        path,
        embeddings_array
    )


    print()
    print("============================================")
    print("         ENROLLMENT SUCCESSFUL")
    print("============================================")
    print("Person:", person_name)
    print("Samples:", len(embeddings))
    print("Saved:", path)


else:

    print()
    print("Enrollment incomplete.")

    print(
        "Captured:",
        len(embeddings),
        "/",
        SAMPLES_NEEDED
    )   
