from datetime import datetime
from typing import Dict, Any

import numpy as np

from app.db.database import (
    SessionLocal,
)
from app.models.document import (
    Document,
)
from app.services.opensearch_index_service import (
    OpenSearchIndexService,
)
from app.services.embedding_service import (
    EmbeddingService,
)
from app.services.faiss_service import (
    FAISSService,
)
import logging
import time
from app.core.redis_client import redis_client

class DocumentIngestionService:
    """
    Unified ingestion pipeline.

    Syncs:
    - PostgreSQL
    - OpenSearch
    - FAISS/HNSW

    Why:
    - Incremental indexing
    - Scale-safe ingestion
    - Governance-first architecture
    """

    def __init__(self):
        self.db = SessionLocal()

        self.opensearch_service = (
            OpenSearchIndexService()
        )

        self.embedding_service = (
            EmbeddingService(redis_client)
        )

        self.faiss_service = (
            FAISSService()
        )
        self.logger = logging.getLogger(__name__)

    # =====================================
    # VALIDATION
    # =====================================
    def validate_document(
        self,
        document: Dict[str, Any],
    ) -> bool:
        required_fields = [
            "id",
            "title",
            "content",
        ]

        return all(
            field in document
            and document[field]
            for field in required_fields
        )

    # =====================================
    # POSTGRES UPSERT
    # =====================================
    def upsert_postgres(
        self,
        document,
    ):
        existing = (
            self.db.query(Document)
            .filter(
                Document.id
                == str(document["id"])
            )
            .first()
        )

        if existing:
            existing.title = document[
                "title"
            ]

            existing.content = document[
                "content"
            ]

            existing.category = (
                document.get(
                    "category",
                    "general",
                )
            )

            existing.source = (
                document.get(
                    "source",
                    "internal",
                )
            )

            existing.version += 1

            existing.is_active = True

            existing.updated_at = (
                datetime.utcnow()
            )

            return existing

        else:
            new_doc = Document(
                id=str(
                    document["id"]
                ),
                title=document[
                    "title"
                ],
                content=document[
                    "content"
                ],
                category=document.get(
                    "category",
                    "general",
                ),
                source=document.get(
                    "source",
                    "internal",
                ),
                version=1,
                is_active=True,
            )

            self.db.add(new_doc)

            return new_doc

    # =====================================
    # OPENSEARCH UPSERT
    # =====================================
    def upsert_opensearch(
        self,
        document,
    ):
        return (
            self.opensearch_service.index_document(
                document
            )
        )

    # =====================================
    # FAISS VECTOR ADD
    # =====================================
    # def add_to_faiss(
    #     self,
    #     document,
    # ):
    #     """
    #     Adds or updates document vector
    #     with docstore governance.
    #     """
    #     combined_text = (
    #         f"{document['title']} "
    #         f"{document['content']}"
    #     )

    #     embedding = (
    #         self.embedding_service.model.encode(
    #             [combined_text],
    #             convert_to_numpy=True,
    #         )
    #     )

    #     latest_index = (
    #         self.faiss_service.add_or_update_document_vector(
    #             doc_id=str(
    #                 document["id"]
    #             ),
    #             embedding=embedding,
    #         )
    #     )

    #     return (
    #         latest_index
    #         is not None
    #     )

    # =====================================
    # INGEST
    # =====================================

    


    def ingest_batch(
        self,
        documents,
        save_faiss=False,
    ):
        """
        High-throughput batch ingestion.
        """

        start_time = time.time()

        # =====================================
        # VALIDATION
        # =====================================

        valid_docs = []

        for doc in documents:
            if self.validate_document(doc):
                valid_docs.append(doc)

        if not valid_docs:
            self.logger.warning(
                "No valid docs in batch"
            )
            return

        self.logger.info(
            f"Processing batch of "
            f"{len(valid_docs)} docs"
        )

        # =====================================
        # POSTGRES UPSERT
        # =====================================

        try:

            for doc in valid_docs:
                self.upsert_postgres(doc)

            self.db.commit()

        except Exception:
            self.logger.exception(
                "Postgres batch failed"
            )

            self.db.rollback()
            return

        # =====================================
        # BATCH EMBEDDINGS
        # =====================================

        texts = [
            f"{doc['title']} {doc['content']}"
            for doc in valid_docs
        ]

        try:

            embeddings = (
                self.embedding_service.model.encode(
                    texts,
                    batch_size=32,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                )
            )

        except Exception:
            self.logger.exception(
                "Embedding batch failed"
            )
            return

        # =====================================
        # FAISS BULK INSERT
        # =====================================

        try:

            for doc, embedding in zip(
                valid_docs,
                embeddings,
            ):

                self.faiss_service.add_or_update_document_vector(
                    doc_id=str(doc["id"]),
                    embedding=embedding,
                )

            # IMPORTANT:
            # DO NOT SAVE EVERY BATCH
            if save_faiss:
                self.faiss_service.save_index()

        except Exception:
            self.logger.exception(
                "FAISS batch failed"
            )

        # =====================================
        # OPENSEARCH BULK INDEX
        # =====================================

        try:

            self.opensearch_service.bulk_index_documents(
                valid_docs
            )

        except Exception:
            self.logger.exception(
                "OpenSearch bulk failed"
            )

        duration = time.time() - start_time

        self.logger.info(
            f"Batch completed in "
            f"{duration:.2f}s"
        )

    # =====================================
    # SOFT DELETE
    # =====================================
    def soft_delete_document(
        self,
        doc_id: str,
    ):
        doc = (
            self.db.query(Document)
            .filter(
                Document.id
                == str(doc_id)
            )
            .first()
        )

        if not doc:
            return False

        doc.is_active = False

        doc.updated_at = (
            datetime.utcnow()
        )

        self.db.commit()

        return True

    # =====================================
    # CLEANUP
    # =====================================
    def close(self):
        self.db.close()
