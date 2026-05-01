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
            EmbeddingService()
        )

        self.faiss_service = (
            FAISSService()
        )

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
    def add_to_faiss(
        self,
        document,
    ):
        """
        Adds or updates document vector
        with docstore governance.
        """
        combined_text = (
            f"{document['title']} "
            f"{document['content']}"
        )

        embedding = (
            self.embedding_service.model.encode(
                [combined_text],
                convert_to_numpy=True,
            )
        )

        latest_index = (
            self.faiss_service.add_or_update_document_vector(
                doc_id=str(
                    document["id"]
                ),
                embedding=embedding,
            )
        )

        return (
            latest_index
            is not None
        )

    # =====================================
    # INGEST
    # =====================================
    def ingest_document(
        self,
        document: Dict[str, Any],
    ):
        if not self.validate_document(
            document
        ):
            return {
                "success": False,
                "error": (
                    "Invalid document schema"
                ),
            }

        try:
            # =============================
            # POSTGRES
            # =============================
            postgres_doc = (
                self.upsert_postgres(
                    document
                )
            )

            # =============================
            # COMMIT FIRST
            # =============================
            self.db.commit()

            # =============================
            # OPENSEARCH
            # =============================
            opensearch_success = (
                self.upsert_opensearch(
                    document
                )
            )

            # =============================
            # FAISS
            # =============================
            faiss_success = (
                self.add_to_faiss(
                    document
                )
            )

            # =============================
            # PERSIST FAISS INDEX
            # =============================
            if faiss_success:
                self.faiss_service.save_index()

            return {
                "success": True,
                "document_id": (
                    postgres_doc.id
                ),
                "version": (
                    postgres_doc.version
                ),
                "postgres": True,
                "opensearch": (
                    opensearch_success
                ),
                "faiss": (
                    faiss_success
                ),
            }

        except Exception as e:
            self.db.rollback()

            return {
                "success": False,
                "error": str(e),
            }

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