from typing import List, Dict, Any

from opensearchpy.helpers import bulk

from app.core.config import settings
from app.core.opensearch_client import OpenSearchClient


class OpenSearchIndexService:
    """
    Manages OpenSearch index lifecycle.

    Why:
    - Schema consistency
    - Bulk ingestion
    - scalability
    - Index governance
    """

    def __init__(self):
        self.client = OpenSearchClient.get_client()
        self.index_name = settings.OPENSEARCH_INDEX

    # =========================================
    # INDEX SCHEMA
    # =========================================
    def get_index_mapping(self) -> Dict[str, Any]:
        """
        Defines scalable BM25-compatible schema.
        """
        return {
            "settings": {
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "category": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                }
            },
        }

    # =========================================
    # CREATE INDEX
    # =========================================
    def create_index(self) -> bool:
        """
        Creates index if missing.
        """
        if not self.client.indices.exists(
            index=self.index_name
        ):
            self.client.indices.create(
                index=self.index_name,
                body=self.get_index_mapping(),
            )
            return True

        return False

    # =========================================
    # DELETE INDEX
    # =========================================
    def delete_index(self) -> bool:
        """
        Deletes index if it exists.
        """
        if self.client.indices.exists(
            index=self.index_name
        ):
            self.client.indices.delete(
                index=self.index_name
            )
            return True

        return False

    # =========================================
    # REBUILD INDEX
    # =========================================
    def rebuild_index(self) -> bool:
        """
        Deletes and recreates index.
        """
        self.delete_index()
        return self.create_index()

    # =========================================
    # BULK INDEX DOCUMENTS
    # =========================================
    def bulk_index_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> int:
        """
        Bulk uploads documents.

        Returns:
            int: Number of indexed docs
        """
        actions = []

        for doc in documents:
            actions.append(
                {
                    "_index": self.index_name,
                    "_id": doc["id"],
                    "_source": {
                        "id": doc["id"],
                        "title": doc.get("title", ""),
                        "content": doc.get(
                            "content", ""
                        ),
                        "category": doc.get(
                            "category", "general"
                        ),
                        "timestamp": doc.get(
                            "timestamp"
                        ),
                    },
                }
            )

        success, _ = bulk(
            self.client,
            actions,
            refresh=True,
        )

        return success

    # =========================================
    # INDEX SINGLE DOCUMENT
    # =========================================
    def index_document(
        self,
        document: Dict[str, Any],
    ) -> bool:
        """
        Incremental single-doc indexing.
        """
        response = self.client.index(
            index=self.index_name,
            id=document["id"],
            body=document,
            refresh=True,
        )

        return response["result"] in [
            "created",
            "updated",
        ]

    # =========================================
    # HEALTH
    # =========================================
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Returns document count + stats.
        """
        try:
            return self.client.indices.stats(
                index=self.index_name
            )
        except Exception as e:
            return {"error": str(e)}