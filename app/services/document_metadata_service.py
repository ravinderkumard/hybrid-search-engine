from typing import List, Dict

from app.db.database import (
    SessionLocal,
)
from app.models.document import (
    Document,
)


class DocumentMetadataService:
    """
    PostgreSQL metadata governance layer.

    Why:
    - Source of truth
    - Active state validation
    - Metadata enrichment
    - Scale-safe filtering
    """

    def __init__(self):
        self.db = SessionLocal()

    # =====================================
    # BULK FETCH
    # =====================================
    def get_documents_by_ids(
        self,
        doc_ids: List[int],
    ) -> Dict[int, Document]:
        """
        Returns active documents only.
        """
        if not doc_ids:
            return {}

        docs = (
            self.db.query(Document)
            .filter(
                Document.id.in_(doc_ids),
                Document.is_active
                == True,
            )
            .all()
        )

        return {
            doc.id: doc
            for doc in docs
        }

    # =====================================
    # ENRICH RESULTS
    # =====================================
    def enrich_results(
        self,
        search_results,
    ):
        """
        Replaces index metadata with PostgreSQL truth.
        """
        doc_ids = []
        for result in search_results:
            try:
                doc_ids.append(int(result["doc_id"]))
            except (TypeError, ValueError):
                continue

        metadata_map = (
            self.get_documents_by_ids(
                doc_ids
            )
        )

        enriched = []

        for result in search_results:
            lookup_id = int(result["doc_id"])
            doc = metadata_map.get(lookup_id)

            # Skip deleted/inactive
            if not doc:
                continue

            enriched.append(
                {
                    **result,
                    "title": doc.title,
                    "content": doc.content,
                    "category": doc.category,
                    "source": doc.source,
                    "version": doc.version,
                    "published_at": (
                        doc.published_at
                    ),
                }
            )

        return enriched

    # =====================================
    # CLEANUP
    # =====================================
    def close(self):
        self.db.close()
