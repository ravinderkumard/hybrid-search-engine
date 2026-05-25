from typing import Dict, Any, List
import asyncio
import time

from app.services.bm25_service import BM25Service
from app.services.embedding_service import (
    EmbeddingService,
)
from app.core.vector_store import faiss_service
from app.services.hybrid_service import (
    HybridSearchService,
)
from app.services.CohereReranker import CohereReranker
from app.services.document_metadata_service import (    DocumentMetadataService,)
from app.services.metrics import (
    rrf_latency,
    metadata_latency,
    total_search_latency,
)
from dotenv import load_dotenv
import os
from app.core.redis_client import redis_client
from app.core.logger import logger

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
        load_dotenv()
        api_key = os.getenv("COHERE_API_KEY")
        self.bm25_service = BM25Service()
        self.embedding_service = (
            EmbeddingService(redis_client)
        )
        self.faiss_service = faiss_service
        self.reranker = (
            CohereReranker(api_key=api_key)
            if api_key
            else None
        )
        self.hybrid_service = (
            HybridSearchService(
                bm25_service=self.bm25_service,
                vector_service=self.faiss_service,
                embedding_service=self.embedding_service,
            )
        )
        self.metadata_service = (
            DocumentMetadataService()
        )

    # =========================================
    # SEARCH
    # =========================================
    async def search(
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

        with total_search_latency.time():
            # =====================================
            # HYBRID FUSION (RRF)
            # =====================================
            with rrf_latency.time():
                hybrid_results = await (
                    self.hybrid_service.search(
                        query=query,
                        top_k=top_k,
                    )
                )

            if not hybrid_results:
                if self.hybrid_service.last_mode == "no_strong_match":
                    return {
                        "query": query,
                        "total_results": 0,
                        "results": [],
                        "message": (
                            self.hybrid_service.last_message
                            or "No strong match found in the current corpus."
                        ),
                    }

                return {
                    "query": query,
                    "total_results": 0,
                    "results": [],
                }

            # =====================================
            # POSTGRESQL GOVERNANCE
            # =====================================
            with metadata_latency.time():
                enriched_results = (
                    self.metadata_service.enrich_results(
                        hybrid_results
                    )
                )

            if not enriched_results:
                if self.hybrid_service.last_mode == "no_strong_match":
                    return {
                        "query": query,
                        "total_results": 0,
                        "results": [],
                        "message": (
                            self.hybrid_service.last_message
                            or "No strong match found in the current corpus."
                        ),
                    }

                return {
                    "query": query,
                    "total_results": 0,
                    "results": [],
                }

            if self.reranker:
                rerank_start = time.perf_counter()
                try:
                    reranked_results = await asyncio.to_thread(
                        self.reranker.rerank,
                        query,
                        enriched_results,
                        top_k,
                    )

                    logger.info({
                        "stage": "reranker",
                        "latency_ms": round(
                            (time.perf_counter() - rerank_start) * 1000,
                            2,
                        ),
                        "candidate_count": len(enriched_results),
                    })

                    enriched_results = reranked_results[:top_k]

                except Exception as e:
                    logger.warning({
                        "stage": "reranker_failed",
                        "error": str(e),
                    })
            else:
                logger.info({
                    "stage": "reranker_skipped",
                    "reason": "missing_api_key",
                })

            return {
                "query": query,
                "total_results": len(
                    enriched_results
                ),
                "results": enriched_results,
            }
    
    # =========================================    
    # # CLEANUP    
    # # =========================================    
    def close(self):        
        """        
        Gracefully closes metadata service.        
        """        
        try:        
            self.metadata_service.close()        
        except Exception:           
            pass

    # =========================================
    # HEALTH
    # =========================================
    async def health_check(self) -> Dict[str, bool]:
        """
        Validates all major search components.
        """

        metadata_healthy = True

        try:
            self.metadata_service.get_documents_by_ids(
                []
            )
        except Exception:
            metadata_healthy = False

        return {
            "bm25_opensearch": await (
                self.bm25_service.health_check()
            ),
            "embedding_model": (
                self.embedding_service
                is not None
            ),
            "faiss": (
                self.faiss_service
                is not None
            ),
            "postgres_metadata": (
                metadata_healthy
            ),
        }
