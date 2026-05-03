import json
import logging

from app.services.document_ingestion_service import (
    DocumentIngestionService,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("document_ingest")


DATA_PATH = "data/documents.json"


def main():
    ingestion_service = (
        DocumentIngestionService()
    )

    try:
        with open(DATA_PATH, "r") as f:
            documents = json.load(f)

        success_count = 0
        failure_count = 0

        for document in documents:
            result = (
                ingestion_service.ingest_document(
                    document
                )
            )

            if result["success"]:
                success_count += 1
                logger.info(
                    f"Ingested doc "
                    f"{result['document_id']}"
                )
            else:
                failure_count += 1
                logger.error(
                    f"Failed doc "
                    f"{document.get('id')}: "
                    f"{result['error']}"
                )

        logger.info(
            f"INGESTION COMPLETE | "
            f"Success: {success_count} | "
            f"Failed: {failure_count}"
        )

    finally:
        ingestion_service.close()


if __name__ == "__main__":
    main()