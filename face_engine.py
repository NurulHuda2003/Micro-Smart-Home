import cv2
import numpy as np
import os
import time

from config import (
    YUNET_MODEL,
    SFACE_MODEL,
    KNOWN_FACES_DIR,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    FACE_CONFIDENCE,
    MATCH_THRESHOLD,
    RECOGNITION_TIMEOUT
)


class FaceEngine:

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def __init__(self):

        print("Loading YuNet face detector...")


        self.detector = cv2.FaceDetectorYN.create(
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


        print("Loading SFace recognizer...")


        self.recognizer = cv2.FaceRecognizerSF.create(
            SFACE_MODEL,
            ""
        )


        self.known_database = {}


        self.load_known_faces()


    # =====================================================
    # LOAD KNOWN FACE DATABASE
    # =====================================================

    def load_known_faces(self):

        self.known_database.clear()


        if not os.path.exists(
            KNOWN_FACES_DIR
        ):

            print(
                "Known faces directory not found."
            )

            return


        for person_name in os.listdir(
            KNOWN_FACES_DIR
        ):


            person_folder = os.path.join(
                KNOWN_FACES_DIR,
                person_name
            )


            if not os.path.isdir(
                person_folder
            ):

                continue


            embedding_file = os.path.join(
                person_folder,
                "embeddings.npy"
            )


            if not os.path.exists(
                embedding_file
            ):

                continue


            try:

                embeddings = np.load(
                    embedding_file
                )


                embeddings = embeddings.astype(
                    np.float32
                )


                self.known_database[
                    person_name
                ] = embeddings


                print(
                    f"Loaded {person_name}: "
                    f"{len(embeddings)} embeddings"
                )


            except Exception as error:

                print(
                    f"Cannot load {person_name}:",
                    error
                )


    # =====================================================
    # GET FACE EMBEDDING
    # =====================================================

    def get_embedding(
        self,
        frame,
        face
    ):

        try:

            # ---------------------------------------------
            # Align detected face
            # ---------------------------------------------

            aligned_face = (
                self.recognizer.alignCrop(
                    frame,
                    face
                )
            )


            # ---------------------------------------------
            # Generate SFace embedding
            # ---------------------------------------------

            feature = self.recognizer.feature(
                aligned_face
            )


            feature = (
                feature
                .flatten()
                .astype(
                    np.float32
                )
            )


            # ---------------------------------------------
            # Normalize
            # ---------------------------------------------

            norm = np.linalg.norm(
                feature
            )


            if norm == 0:

                return None


            feature = (
                feature
                /
                norm
            )


            return feature


        except Exception as error:

            print(
                "Embedding error:",
                error
            )

            return None


    # =====================================================
    # COMPARE ONE FACE AGAINST DATABASE
    # =====================================================

    def compare_face(
        self,
        current_embedding
    ):

        results = []


        # -------------------------------------------------
        # Compare current face with every enrolled person
        # -------------------------------------------------

        for (
            person_name,
            embeddings
        ) in self.known_database.items():


            similarities = []


            for saved_embedding in embeddings:


                saved_embedding = (
                    saved_embedding.astype(
                        np.float32
                    )
                )


                saved_norm = np.linalg.norm(
                    saved_embedding
                )


                if saved_norm == 0:

                    continue


                saved_embedding = (
                    saved_embedding
                    /
                    saved_norm
                )


                # -----------------------------------------
                # Cosine similarity
                # -----------------------------------------

                similarity = np.dot(
                    current_embedding,
                    saved_embedding
                )


                similarities.append(
                    float(
                        similarity
                    )
                )


            if len(similarities) == 0:

                continue


            # Highest score first
            similarities.sort(
                reverse=True
            )


            # Best 3 enrollment samples
            top_scores = (
                similarities[:3]
            )


            score = (
                sum(top_scores)
                /
                len(top_scores)
            )


            results.append(
                (
                    person_name,
                    score
                )
            )


        # -------------------------------------------------
        # No database result
        # -------------------------------------------------

        if len(results) == 0:

            return {

                "known": False,

                "name": None,

                "score": 0.0,

                "results": []
            }


        # -------------------------------------------------
        # Find best person
        # -------------------------------------------------

        results.sort(
            key=lambda item: item[1],
            reverse=True
        )


        best_name = (
            results[0][0]
        )


        best_score = (
            results[0][1]
        )


        # -------------------------------------------------
        # Threshold check
        # -------------------------------------------------

        if best_score >= MATCH_THRESHOLD:

            return {

                "known": True,

                "name": best_name,

                "score": best_score,

                "results": results
            }


        return {

            "known": False,

            "name": None,

            "score": best_score,

            "results": results
        }


    # =====================================================
    # RECOGNIZE ALL FACES IN ONE FRAME
    # =====================================================

    def recognize_frame(
        self,
        frame
    ):

        height, width = frame.shape[:2]


        # YuNet needs actual frame size
        self.detector.setInputSize(
            (
                width,
                height
            )
        )


        # -------------------------------------------------
        # Detect ALL faces
        # -------------------------------------------------

        _, faces = self.detector.detect(
            frame
        )


        # -------------------------------------------------
        # No face
        # -------------------------------------------------

        if (
            faces is None
            or
            len(faces) == 0
        ):

            return {

                "status": "NO_FACE",

                "faces": [],

                "frame": frame
            }


        # =================================================
        # PROCESS EVERY DETECTED FACE
        # =================================================

        face_results = []


        for face in faces:


            # ---------------------------------------------
            # Create embedding for this face only
            # ---------------------------------------------

            current_embedding = (
                self.get_embedding(
                    frame,
                    face
                )
            )


            if current_embedding is None:

                face_results.append({

                    "status": "UNKNOWN",

                    "name": None,

                    "score": 0.0,

                    "face": face,

                    "results": []
                })

                continue


            # ---------------------------------------------
            # Compare this face against enrolled people
            # ---------------------------------------------

            comparison = self.compare_face(
                current_embedding
            )


            # ---------------------------------------------
            # Known
            # ---------------------------------------------

            if comparison["known"]:

                face_results.append({

                    "status": "KNOWN",

                    "name": comparison[
                        "name"
                    ],

                    "score": comparison[
                        "score"
                    ],

                    "face": face,

                    "results": comparison[
                        "results"
                    ]
                })


            # ---------------------------------------------
            # Unknown
            # ---------------------------------------------

            else:

                face_results.append({

                    "status": "UNKNOWN",

                    "name": None,

                    "score": comparison[
                        "score"
                    ],

                    "face": face,

                    "results": comparison[
                        "results"
                    ]
                })


        # =================================================
        # RETURN ALL PEOPLE
        # =================================================

        return {

            "status": "FACES_DETECTED",

            "faces": face_results,

            "frame": frame
        }


    # =====================================================
    # CAMERA RECOGNITION
    #
    # main.py যদি এই function ব্যবহার করে,
    # detected frame results return করবে।
    # =====================================================

    def recognize_from_camera(
        self,
        picam2
    ):

        start_time = time.time()


        while (
            time.time()
            -
            start_time
            <
            RECOGNITION_TIMEOUT
        ):


            frame = picam2.capture_array()


            result = self.recognize_frame(
                frame
            )


            if (
                result["status"]
                ==
                "FACES_DETECTED"
            ):

                return result


        return {

            "status": "NO_FACE",

            "faces": []
        }