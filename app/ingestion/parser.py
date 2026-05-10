import os
import xml.etree.ElementTree as ET

from minio import Minio


class StackOverflowParser:

    def __init__(
        self,
        bucket_name: str,
        object_name: str,
    ):

        self.bucket_name = bucket_name
        self.object_name = object_name

        self.client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=False,
        )

    def stream_questions(self):
        """
        Streams StackOverflow XML directly
        from MinIO using constant memory.
        """

        response = self.client.get_object(
            self.bucket_name,
            self.object_name,
        )

        context = ET.iterparse(
            response,
            events=("end",)
        )
        ALLOWED_TAGS = [
            "python",
            "docker",
            "fastapi",
            "machine-learning"
        ]
        for event, elem in context:
            tags = elem.attrib.get("Tags", "")
            score = int(elem.attrib.get("Score", 0))
            
            if score < 5:
                continue

            if not any(
                tag in tags
                for tag in ALLOWED_TAGS
            ):
                continue

            if elem.tag != "row":
                continue

            post_type = elem.attrib.get(
                "PostTypeId"
            )

            # Only questions
            if post_type == "1":

                yield {
                    "id": elem.attrib.get("Id"),
                    "title": elem.attrib.get(
                        "Title",
                        ""
                    ),
                    "body": elem.attrib.get(
                        "Body",
                        ""
                    ),
                    "tags": elem.attrib.get(
                        "Tags",
                        ""
                    ),
                    "score": elem.attrib.get(
                        "Score",
                        "0"
                    ),
                }

            # VERY IMPORTANT
            # prevents memory explosion
            elem.clear()

        response.close()
        response.release_conn()