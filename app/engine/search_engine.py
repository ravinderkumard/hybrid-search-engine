from typing import Dict, Any, List

from app.services.bm25_service import BM25Service
from app.services.embedding_service import (
    EmbeddingService,
)
from app.services.faiss_service import FAISSService
from app.services.hybrid_service import (
    HybridSearchService,
)


class SearchEngine:
    """
    Unified hybrid retrieval engine.

    Current Architecture:
    OpenSearch BM25 + Dense Retrieval + RRF

    Why:
    - Sparse lexical precision
    - Dense semantic recall
    - Scalable toward 1M+ docs
    """

    def __init__(self):
        self.bm25_service = BM25Service()
        self.embedding_service = (
            EmbeddingService()
        )
        self.faiss_service = FAISSService()
        self.hybrid_service = (
            HybridSearchService(
                bm25_service=self.bm25_service,
                vector_service=self.faiss_service,
                embedding_service=self.embedding_service
            )
        )

    # =========================================
    # SEARCH
    # =========================================
    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Executes hybrid retrieval pipeline.

        Returns:
        {
            query,
            total_results,
            results
        }
        """

        if not query or not query.strip():
            return {
                "query": query,
                "total_results": 0,
                "results": [],
            }

        # =====================================
        # SPARSE SEARCH (OpenSearch BM25)
        # =====================================
        bm25_results = (
            self.bm25_service.search(
                query=query,
                top_k=top_k * 2,
            )
        )

        # =====================================
        # DENSE SEARCH (FAISS)
        # =====================================
        query_embedding = (
            self.embedding_service.encode_query(
                query
            )
        )

        dense_results = (
            self.faiss_service.search(
                query_embedding=query_embedding,
                top_k=top_k * 2,
            )
        )

        # =====================================
        # HYBRID FUSION (RRF)
        # =====================================
        hybrid_results = (
            self.hybrid_service.search(
                query=query,
                top_k=top_k,
            )
        )

        return {
            "query": query,
            "total_results": len(
                hybrid_results
            ),
            "results": hybrid_results,
        }

    # =========================================
    # HEALTH
    # =========================================
    def health_check(self) -> Dict[str, bool]:
        """
        Validates all major search components.
        """

        return {
            "bm25_opensearch": self.bm25_service.health_check(),
            "embedding_model": (
                self.embedding_service
                is not None
            ),
            "faiss": (
                self.faiss_service
                is not None
            ),
        }