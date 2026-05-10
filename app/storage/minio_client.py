import os

from minio import Minio


class MinioClientFactory:

    @staticmethod
    def get_client():

        return Minio(
            endpoint=os.getenv(
                "MINIO_ENDPOINT"
            ),
            access_key=os.getenv(
                "MINIO_ACCESS_KEY"
            ),
            secret_key=os.getenv(
                "MINIO_SECRET_KEY"
            ),
            secure=False,
        )