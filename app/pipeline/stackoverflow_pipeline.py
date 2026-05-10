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
        count = 0

        logger.info(
            "Starting StackOverflow ingestion"
        )

        for raw_doc in (
            self.parser.stream_questions()
        ):

            transformed = (
                self.transformer.transform(
                    raw_doc
                )
            )

            if not transformed:
                continue

            buffer.append(transformed)

            if len(buffer) >= self.batch_size:
                self.flush(buffer)
                buffer.clear()

            count += 1

            if count % 1000 == 0:
                logger.info(
                    f"Processed {count} docs"
                )

            if self.limit and count >= self.limit:
                break

        # final flush
        if buffer:
            self.flush(buffer)

        logger.info(
            f"Finished ingestion: {count} docs"
        )

    def flush(self, batch):
        try:
            self.ingestion_service.ingest_batch(
                batch
            )

            logger.info(
                f"Ingested batch of {len(batch)}"
            )

        except Exception as e:
            logger.error(
                f"Batch failed: {e}",
                exc_info=True
            )