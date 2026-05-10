import json
import io

from app.storage.minio_client import (
    MinioClientFactory,
)


class ArxivParser:

    def __init__(
        self,
        bucket_name,
        object_name,
    ):

        self.bucket_name = bucket_name
        self.object_name = object_name

        self.client = (
            MinioClientFactory.get_client()
        )

    def stream_documents(self):

        response = self.client.get_object(
            self.bucket_name,
            self.object_name,
        )

        try:

            stream = io.TextIOWrapper(
                response,
                encoding="utf-8"
            )

            for line in stream:

                line = line.strip()

                if not line:
                    continue

                item = json.loads(line)

                yield {
                    "id": item.get("id"),
                    "title": item.get(
                        "title",
                        ""
                    ),
                    "content": item.get(
                        "abstract",
                        ""
                    ),
                    "category": item.get(
                        "categories",
                        "general"
                    ),
                }

        finally:

            response.close()
            response.release_conn()