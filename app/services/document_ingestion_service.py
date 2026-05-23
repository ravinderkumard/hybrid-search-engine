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
from app.core.vector_store import faiss_service
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

        self.faiss_service = faiss_service

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
                Document.arxiv_id
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
                arxiv_id=str(
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
        batch_received = len(documents)

        valid_docs = []
        for doc in documents:
            if self.validate_document(doc):
                valid_docs.append(doc)

        if not valid_docs:
            self.logger.warning(
                {
                    "event": "ingest_batch_empty",
                    "batch_received": batch_received,
                }
            )
            return {
                "batch_received": batch_received,
                "valid_documents": 0,
                "postgres_upserts": 0,
                "embeddings_created": 0,
                "faiss_updates": 0,
                "faiss_overwrites": 0,
                "opensearch_indexed": 0,
                "saved_faiss": False,
                "duration_seconds": 0.0,
            }

        self.logger.info(
            {
                "event": "ingest_batch_start",
                "batch_received": batch_received,
                "valid_documents": len(valid_docs),
            }
        )

        postgres_docs = []

        try:
            for doc in valid_docs:
                postgres_docs.append(
                    self.upsert_postgres(doc)
                )

            self.db.commit()

        except Exception:
            self.logger.exception(
                "Postgres batch failed"
            )
            self.db.rollback()
            return {
                "batch_received": batch_received,
                "valid_documents": len(valid_docs),
                "postgres_upserts": 0,
                "embeddings_created": 0,
                "faiss_updates": 0,
                "faiss_overwrites": 0,
                "opensearch_indexed": 0,
                "saved_faiss": False,
                "duration_seconds": round(
                    time.time() - start_time,
                    2,
                ),
            }

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
            return {
                "batch_received": batch_received,
                "valid_documents": len(valid_docs),
                "postgres_upserts": len(postgres_docs),
                "embeddings_created": 0,
                "faiss_updates": 0,
                "faiss_overwrites": 0,
                "opensearch_indexed": 0,
                "saved_faiss": False,
                "duration_seconds": round(
                    time.time() - start_time,
                    2,
                ),
            }

        embedding_count = (
            embeddings.shape[0]
            if hasattr(embeddings, "shape")
            and len(embeddings.shape) > 0
            else len(embeddings)
        )

        if embedding_count != len(valid_docs):
            self.logger.warning(
                {
                    "event": "embedding_count_mismatch",
                    "batch_received": batch_received,
                    "valid_documents": len(valid_docs),
                    "embeddings_created": embedding_count,
                }
            )

        if self.faiss_service.index is None:
            self.logger.info(
                "Initializing FAISS index."
            )
            self.faiss_service.initialize_index(
                embeddings
            )

        faiss_updates = 0
        faiss_overwrites = 0

        try:
            for postgres_doc, embedding in zip(
                postgres_docs,
                embeddings,
            ):
                faiss_result = (
                    self.faiss_service.add_or_update_document_vector(
                        doc_id=postgres_doc.id,
                        embedding=embedding,
                    )
                )
                faiss_updates += 1
                if faiss_result.get("action") == "updated":
                    faiss_overwrites += 1

            if save_faiss:
                self.faiss_service.save_index()

        except Exception:
            self.logger.exception(
                "FAISS batch failed"
            )
            faiss_updates = 0
            faiss_overwrites = 0

        try:
            opensearch_indexed = (
                self.opensearch_service.bulk_index_documents(
                    [
                        {
                            "id": postgres_doc.id,
                            "title": postgres_doc.title,
                            "content": postgres_doc.content,
                            "category": postgres_doc.category,
                            "timestamp": postgres_doc.updated_at,
                        }
                        for postgres_doc in postgres_docs
                    ]
                )
            )

        except Exception:
            self.logger.exception(
                "OpenSearch bulk failed"
            )
            opensearch_indexed = 0

        duration = time.time() - start_time
        summary = {
            "batch_received": batch_received,
            "valid_documents": len(valid_docs),
            "postgres_upserts": len(postgres_docs),
            "embeddings_created": embedding_count,
            "faiss_updates": faiss_updates,
            "faiss_overwrites": faiss_overwrites,
            "opensearch_indexed": opensearch_indexed,
            "saved_faiss": bool(save_faiss),
            "duration_seconds": round(duration, 2),
        }

        self.logger.info(
            {
                "event": "ingest_batch_complete",
                **summary,
            }
        )

        return summary

    # =====================================
    # SOFT DELETE
    # =====================================
    def soft_delete_document(
        self,
        doc_id: str,
    ):
        try:
            normalized_doc_id = int(doc_id)
        except (TypeError, ValueError):
            return False

        doc = (
            self.db.query(Document)
            .filter(
                Document.id
                == normalized_doc_id
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
