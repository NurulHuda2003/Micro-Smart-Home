import os
import cv2
import numpy as np


from config import (
    YUNET_MODEL,
    SFACE_MODEL,
    KNOWN_FACES_DIR,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    FACE_CONFIDENCE,
    MATCH_THRESHOLD
)


# =========================================================
# FACE ENGINE
# =========================================================

class FaceEngine:

    def __init__(self):

        print(
            "Loading YuNet face detector..."
        )


        self.detector = (
            cv2.FaceDetectorYN.create(

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
        )


        print(
            "Loading SFace recognizer..."
        )


        self.recognizer = (
            cv2.FaceRecognizerSF.create(

                SFACE_MODEL,

                ""
            )
        )


        self.known_database = {}


        self.load_known_faces()


    # =====================================================
    # LOAD KNOWN FACES
    # =====================================================

    def load_known_faces(self):

        self.known_database.clear()


        if not os.path.isdir(
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


            if not os.path.isfile(
                embedding_file
            ):

                continue


            try:

                embeddings = (
                    np.load(
                        embedding_file
                    )
                    .astype(
                        np.float32
                    )
                )


                self.known_database[
                    person_name
                ] = embeddings


                print(

                    f"Loaded "
                    f"{person_name}: "
                    f"{len(embeddings)} "
                    f"embeddings"
                )


            except Exception as error:

                print(

                    f"Cannot load "
                    f"{person_name}:",
                    error
                )


    # =====================================================
    # CREATE EMBEDDING
    # =====================================================

    def get_embedding(
        self,
        frame,
        face
    ):

        try:

            aligned_face = (
                self.recognizer
                .alignCrop(
                    frame,
                    face
                )
            )


            feature = (
                self.recognizer
                .feature(
                    aligned_face
                )
                .flatten()
                .astype(
                    np.float32
                )
            )


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
    # COMPARE WITH DATABASE
    # =====================================================

    def compare_face(
        self,
        current_embedding
    ):

        person_results = []


        for (
            person_name,
            embeddings
        ) in self.known_database.items():


            similarities = []


            for saved_embedding in embeddings:


                saved_embedding = (
                    saved_embedding
                    .astype(
                        np.float32
                    )
                )


                saved_norm = np.linalg.norm(
                    saved_embedding
                )


                if saved_norm == 0:

                    continue


                normalized_saved = (
                    saved_embedding
                    /
                    saved_norm
                )


                similarity = float(

                    np.dot(

                        current_embedding,

                        normalized_saved
                    )
                )


                similarities.append(
                    similarity
                )


            if not similarities:

                continue


            similarities.sort(
                reverse=True
            )


            top_scores = (
                similarities[:3]
            )


            average_score = (
                sum(top_scores)
                /
                len(top_scores)
            )


            person_results.append(

                (
                    person_name,
                    average_score
                )
            )


        # =================================================
        # EMPTY DB
        # =================================================

        if not person_results:

            return {

                "known":
                    False,

                "name":
                    None,

                "score":
                    0.0,

                "results":
                    []
            }


        # =================================================
        # BEST MATCH
        # =================================================

        person_results.sort(

            key=lambda item:
                item[1],

            reverse=True
        )


        best_name = (
            person_results[0][0]
        )


        best_score = (
            person_results[0][1]
        )


        if (
            best_score
            >=
            MATCH_THRESHOLD
        ):

            return {

                "known":
                    True,

                "name":
                    best_name,

                "score":
                    best_score,

                "results":
                    person_results
            }


        return {

            "known":
                False,

            "name":
                None,

            "score":
                best_score,

            "results":
                person_results
        }


    # =====================================================
    # RECOGNIZE ALL FACES IN FRAME
    # =====================================================

    def recognize_frame(
        self,
        frame
    ):

        height, width = (
            frame.shape[:2]
        )


        self.detector.setInputSize(

            (
                width,
                height
            )
        )


        _,
        faces = self.detector.detect(
            frame
        )


        # =================================================
        # NO FACE
        # =================================================

        if (
            faces is None
            or
            len(faces) == 0
        ):

            return {

                "status":
                    "NO_FACE",

                "faces":
                    []
            }


        results = []


        # =================================================
        # MULTIPLE FACES SUPPORTED
        # =================================================

        for face in faces:


            embedding = (
                self.get_embedding(
                    frame,
                    face
                )
            )


            if embedding is None:

                results.append({

                    "status":
                        "UNKNOWN",

                    "name":
                        None,

                    "score":
                        0.0,

                    "face":
                        face,

                    "results":
                        []
                })


                continue


            comparison = (
                self.compare_face(
                    embedding
                )
            )


            if comparison[
                "known"
            ]:

                results.append({

                    "status":
                        "KNOWN",

                    "name":
                        comparison[
                            "name"
                        ],

                    "score":
                        comparison[
                            "score"
                        ],

                    "face":
                        face,

                    "results":
                        comparison[
                            "results"
                        ]
                })


            else:

                results.append({

                    "status":
                        "UNKNOWN",

                    "name":
                        None,

                    "score":
                        comparison[
                            "score"
                        ],

                    "face":
                        face,

                    "results":
                        comparison[
                            "results"
                        ]
                })


        return {

            "status":
                "FACES_DETECTED",

            "faces":
                results
        }
