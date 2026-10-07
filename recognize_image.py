import os
import time

import cv2
import numpy as np

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
    # LOAD KNOWN PEOPLE
    # =====================================================

    def load_known_faces(self):

        self.known_database.clear()


        if not os.path.exists(
            KNOWN_FACES_DIR
        ):

            print(
                "Known faces folder does not exist."
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
                    f"{len(embeddings)} samples"
                )


            except Exception as error:

                print(
                    f"Cannot load {person_name}:",
                    error
                )


    # =====================================================
    # EMBEDDING
    # =====================================================

    def get_embedding(
        self,
        frame,
        face
    ):

        try:

            aligned = self.recognizer.alignCrop(
                frame,
                face
            )


            feature = self.recognizer.feature(
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

                return None


            return feature / norm


        except Exception as error:

            print(
                "Embedding error:",
                error
            )

            return None


    # =====================================================
    # COMPARE FACE
    # =====================================================

    def compare_face(
        self,
        current_embedding
    ):

        results = []


        for person_name, embeddings in (
            self.known_database.items()
        ):

            similarities = []


            for saved_embedding in embeddings:

                saved_embedding = (
                    saved_embedding
                    .astype(np.float32)
                )


                norm = np.linalg.norm(
                    saved_embedding
                )


                if norm == 0:

                    continue


                saved_embedding = (
                    saved_embedding
                    /
                    norm
                )


                similarity = float(
                    np.dot(
                        current_embedding,
                        saved_embedding
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


            top_scores = similarities[:3]


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


        if not results:

            return {
                "known": False,
                "name": None,
                "score": 0.0,
                "results": []
            }


        results.sort(
            key=lambda item: item[1],
            reverse=True
        )


        best_name = results[0][0]

        best_score = results[0][1]


        return {
            "known": (
                best_score >=
                MATCH_THRESHOLD
            ),
            "name": (
                best_name
                if
                best_score >= MATCH_THRESHOLD
                else
                None
            ),
            "score": best_score,
            "results": results
        }


    # =====================================================
    # PROCESS FRAME
    # =====================================================

    def recognize_frame(
        self,
        frame
    ):

        height, width = frame.shape[:2]


        self.detector.setInputSize(
            (
                width,
                height
            )
        )


        _, faces = self.detector.detect(
            frame
        )


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


        face_results = []


        for face in faces:

            embedding = self.get_embedding(
                frame,
                face
            )


            if embedding is None:

                face_results.append({
                    "status": "UNKNOWN",
                    "name": None,
                    "score": 0.0,
                    "face": face,
                    "results": []
                })

                continue


            comparison = self.compare_face(
                embedding
            )


            if comparison["known"]:

                face_results.append({
                    "status": "KNOWN",
                    "name": comparison["name"],
                    "score": comparison["score"],
                    "face": face,
                    "results": comparison["results"]
                })

            else:

                face_results.append({
                    "status": "UNKNOWN",
                    "name": None,
                    "score": comparison["score"],
                    "face": face,
                    "results": comparison["results"]
                })


        return {
            "status": "FACES_DETECTED",
            "faces": face_results,
            "frame": frame
        }


    # =====================================================
    # OPTIONAL CAMERA RECOGNITION
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
