from app.ingestion.arxiv_parser import (
    ArxivParser,
)
import logging

from app.services.document_ingestion_service import (
    DocumentIngestionService,
)


logger = logging.getLogger(__name__)


class ArxivPipeline:

    def __init__(
        self,
        batch_size=50,
        limit=1000,
    ):

        self.batch_size = batch_size
        self.limit = limit

        self.parser = ArxivParser(
            bucket_name="datasets",
            object_name="arxiv.json",
        )

        self.ingestion_service = (
            DocumentIngestionService()
        )

    def run(self):

        batch = []
        count = 0
        batch_number = 0

        for doc in (
            self.parser.stream_documents()
        ):

            count += 1
            batch.append(doc)

            if len(batch) >= self.batch_size:
                batch_number += 1

                summary = (
                    self.ingestion_service.ingest_batch(
                        batch,
                        save_faiss=True,
                    )
                )

                logger.info(
                    {
                        "event": "arxiv_batch_processed",
                        "batch_number": batch_number,
                        "records_read_total": count,
                        "batch_size": len(batch),
                        **summary,
                    }
                )

                batch.clear()

            if count >= self.limit:
                break

        if batch:
            batch_number += 1
            summary = (
                self.ingestion_service.ingest_batch(
                    batch,
                    save_faiss=True,
                )
            )

            logger.info(
                {
                    "event": "arxiv_batch_processed",
                    "batch_number": batch_number,
                    "records_read_total": count,
                    "batch_size": len(batch),
                    **summary,
                }
            )
