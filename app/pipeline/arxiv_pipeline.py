from app.ingestion.arxiv_parser import (
    ArxivParser,
)

from app.services.document_ingestion_service import (
    DocumentIngestionService,
)


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

        for doc in (
            self.parser.stream_documents()
        ):

            batch.append(doc)

            if len(batch) >= self.batch_size:

                self.ingestion_service.ingest_batch(
                    batch
                )

                batch.clear()

            count += 1

            if count >= self.limit:
                break

        if batch:
            self.ingestion_service.ingest_batch(
                batch
            )