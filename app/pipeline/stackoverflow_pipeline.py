import logging
from app.ingestion.parser import StackOverflowParser
from app.ingestion.transformer import DocumentTransformer
from app.services.document_ingestion_service import DocumentIngestionService

logger = logging.getLogger(__name__)


class StackOverflowPipeline:

    def __init__(
        self,
        xml_path,
        batch_size=50,
        limit=None,
    ):
        self.xml_path = xml_path
        self.batch_size = batch_size
        self.limit = limit

        self.parser = StackOverflowParser(
            bucket_name="stackoverflow-data",
            object_name="Posts.xml",
        )

        self.transformer = (
            DocumentTransformer()
        )

        self.ingestion_service = (
            DocumentIngestionService()
        )

    def run(self):
        buffer = []
        raw_count = 0
        accepted_count = 0
        batch_number = 0

        logger.info(
            "Starting StackOverflow ingestion"
        )

        for raw_doc in (
            self.parser.stream_questions()
        ):

            raw_count += 1
            transformed = (
                self.transformer.transform(
                    raw_doc
                )
            )

            if not transformed:
                continue

            accepted_count += 1
            buffer.append(transformed)

            if len(buffer) >= self.batch_size:
                batch_number += 1
                summary = self.flush(buffer)
                logger.info(
                    {
                        "event": "stackoverflow_batch_processed",
                        "batch_number": batch_number,
                        "records_read_total": raw_count,
                        "records_accepted_total": accepted_count,
                        "batch_size": len(buffer),
                        **(summary or {}),
                    }
                )
                buffer.clear()

            if raw_count % 1000 == 0:
                logger.info(
                    f"Processed {raw_count} raw docs"
                )

            if self.limit and raw_count >= self.limit:
                break

        # final flush
        if buffer:
            batch_number += 1
            summary = self.flush(buffer)
            logger.info(
                {
                    "event": "stackoverflow_batch_processed",
                    "batch_number": batch_number,
                    "records_read_total": raw_count,
                    "records_accepted_total": accepted_count,
                    "batch_size": len(buffer),
                    **(summary or {}),
                }
            )

        logger.info(
            f"Finished ingestion: {accepted_count} accepted docs from {raw_count} raw docs"
        )

    def flush(self, batch):
        try:
            return self.ingestion_service.ingest_batch(
                batch
            )

        except Exception as e:
            logger.error(
                f"Batch failed: {e}",
                exc_info=True
            )
            return None
