import cv2
import numpy as np
import os
import sys
import time

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
# GET PERSON NAME
# =========================================================

if len(sys.argv) < 2:

    print()
    print("ERROR: Person name দেওয়া হয়নি.")
    print()
    print("Example:")
    print("python enroll_faces.py Nurul")
    print()

    sys.exit(1)


person_name = sys.argv[1].strip()


if person_name == "":

    print("ERROR: Invalid person name")

    sys.exit(1)


# =========================================================
# CHECK MODEL FILES
# =========================================================

if not os.path.exists(YUNET_MODEL):

    print()
    print("ERROR: YuNet model পাওয়া যায়নি:")
    print(YUNET_MODEL)

    sys.exit(1)


if not os.path.exists(SFACE_MODEL):

    print()
    print("ERROR: SFace model পাওয়া যায়নি:")
    print(SFACE_MODEL)

    sys.exit(1)


# =========================================================
# CREATE PERSON DIRECTORY
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
# LOAD YUNET
# =========================================================

print("Loading YuNet face detector...")


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


# =========================================================
# LOAD SFACE
# =========================================================

print("Loading SFace recognizer...")


recognizer = cv2.FaceRecognizerSF.create(
    SFACE_MODEL,
    ""
)


# =========================================================
# CAMERA SETUP
# =========================================================

print("Starting Raspberry Pi Camera...")


picam2 = Picamera2()


camera_config = picam2.create_preview_configuration(

    main={

        "size": (
            CAMERA_WIDTH,
            CAMERA_HEIGHT
        ),

        "format": "RGB888"
    }
)


picam2.configure(
    camera_config
)


picam2.start()


# Camera warm-up
time.sleep(2)


# =========================================================
# VARIABLES
# =========================================================

embeddings = []

sample_count = 0

last_capture_time = 0


# =========================================================
# START MESSAGE
# =========================================================

print()
print("============================================")
print("          FACE ENROLLMENT STARTED")
print("============================================")

print()
print("Person:", person_name)

print()
print("Camera-এর দিকে তাকান।")

print()
print("ধীরে ধীরে:")
print("- সোজা তাকান")
print("- একটু বামে তাকান")
print("- একটু ডানে তাকান")
print("- একটু উপরে তাকান")
print("- একটু নিচে তাকান")

print()
print("একজন মানুষ camera সামনে থাকবেন।")

print()
print("Q চাপলে বন্ধ হবে.")

print()
print("============================================")
print()


# =========================================================
# MAIN LOOP
# =========================================================

try:

    while sample_count < SAMPLES_NEEDED:

        # =================================================
        # CAPTURE FRAME
        #
        # RGB888 from Picamera2 gives OpenCV compatible
        # BGR channel order.
        #
        # তাই cvtColor লাগছে না।
        # =================================================

        frame = picam2.capture_array()


        height, width = frame.shape[:2]


        # Detector input size update
        detector.setInputSize(
            (
                width,
                height
            )
        )


        # =================================================
        # FACE DETECTION
        # =================================================

        _, faces = detector.detect(
            frame
        )


        display_frame = frame.copy()


        status_text = "No face detected"

        status_color = (
            0,
            0,
            255
        )


        # =================================================
        # FACE FOUND
        # =================================================

        if faces is not None:


            number_of_faces = len(
                faces
            )


            # =================================================
            # EXACTLY ONE FACE
            # =================================================

            if number_of_faces == 1:


                face = faces[0]


                x = int(
                    face[0]
                )

                y = int(
                    face[1]
                )

                w = int(
                    face[2]
                )

                h = int(
                    face[3]
                )


                cv2.rectangle(

                    display_frame,

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

                    f"Face detected "
                    f"{sample_count}/"
                    f"{SAMPLES_NEEDED}"
                )


                status_color = (
                    0,
                    255,
                    0
                )


                current_time = (
                    time.time()
                )


                # =================================================
                # SAVE SAMPLE
                # =================================================

                if (
                    current_time
                    -
                    last_capture_time
                    >=
                    CAPTURE_INTERVAL
                ):


                    try:

                        # =========================================
                        # ALIGN FACE
                        # =========================================

                        aligned_face = (
                            recognizer.alignCrop(
                                frame,
                                face
                            )
                        )


                        # =========================================
                        # GENERATE EMBEDDING
                        # =========================================

                        feature = recognizer.feature(
                            aligned_face
                        )


                        feature = (

                            feature
                            .flatten()
                            .astype(
                                np.float32
                            )
                        )


                        # =========================================
                        # NORMALIZE EMBEDDING
                        # =========================================

                        norm = np.linalg.norm(
                            feature
                        )


                        if norm == 0:

                            print(
                                "Invalid embedding. Skipping..."
                            )

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


                        last_capture_time = (
                            current_time
                        )


                        # =========================================
                        # SAVE FACE IMAGE
                        # =========================================

                        image_filename = (

                            f"face_"
                            f"{sample_count:02d}.jpg"
                        )


                        image_path = os.path.join(

                            person_dir,

                            image_filename
                        )


                        cv2.imwrite(

                            image_path,

                            aligned_face
                        )


                        print(

                            f"Captured sample "
                            f"{sample_count}/"
                            f"{SAMPLES_NEEDED}"
                        )


                    except Exception as error:

                        print(
                            "Face processing error:",
                            error
                        )


            # =================================================
            # MULTIPLE FACES
            # =================================================

            elif number_of_faces > 1:


                status_text = (
                    "Multiple faces detected"
                )


                status_color = (
                    0,
                    165,
                    255
                )


                for face in faces:


                    x = int(
                        face[0]
                    )

                    y = int(
                        face[1]
                    )

                    w = int(
                        face[2]
                    )

                    h = int(
                        face[3]
                    )


                    cv2.rectangle(

                        display_frame,

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
                            165,
                            255
                        ),

                        2
                    )


        # =================================================
        # DISPLAY TEXT
        # =================================================

        cv2.putText(

            display_frame,

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

            display_frame,

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

            display_frame,

            "Move head slowly",

            (
                20,
                430
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


        cv2.putText(

            display_frame,

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


        # =================================================
        # SHOW CAMERA
        # =================================================

        cv2.imshow(

            "Face Enrollment",

            display_frame
        )


        key = (
            cv2.waitKey(1)
            &
            0xFF
        )


        if key == ord("q"):

            print()
            print(
                "Enrollment cancelled."
            )

            break


# =========================================================
# CLEANUP
# =========================================================

finally:

    picam2.stop()

    picam2.close()

    cv2.destroyAllWindows()


# =========================================================
# SAVE EMBEDDINGS
# =========================================================

if len(embeddings) == SAMPLES_NEEDED:


    embeddings_array = np.array(

        embeddings,

        dtype=np.float32
    )


    embedding_path = os.path.join(

        person_dir,

        "embeddings.npy"
    )


    np.save(

        embedding_path,

        embeddings_array
    )


    print()
    print("============================================")
    print("          ENROLLMENT SUCCESSFUL")
    print("============================================")

    print()
    print(
        "Person:",
        person_name
    )

    print(
        "Samples:",
        len(embeddings)
    )

    print()
    print(
        "Saved at:"
    )

    print(
        person_dir
    )

    print()
    print(
        "Embedding database:"
    )

    print(
        embedding_path
    )

    print()
    print("============================================")


else:

    print()
    print("============================================")
    print("          ENROLLMENT INCOMPLETE")
    print("============================================")

    print(
        "Captured:",
        len(embeddings),
        "/",
        SAMPLES_NEEDED
    )

    print()
    print(
        "Run again:"
    )

    print(
        f"python enroll_faces.py {person_name}"
    )

    print()
    print("============================================")