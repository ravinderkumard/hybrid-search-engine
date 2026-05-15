from typing import Dict, Any, List

from app.services.bm25_service import BM25Service
from app.services.embedding_service import (
    EmbeddingService,
)
from app.services.faiss_service import FAISSService
from app.services.hybrid_service import (
    HybridSearchService,
)
from app.services.CohereReranker import CohereReranker
from app.services.document_metadata_service import (    DocumentMetadataService,)
from app.services.metrics import (bm25_latency,embedding_latency,faiss_latency,rrf_latency,metadata_latency,total_search_latency)
from dotenv import load_dotenv
import os
from app.core.redis_client import redis_client

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
        self.faiss_service = FAISSService()
        reranker = CohereReranker(
            api_key = api_key
            
        )
        self.hybrid_service = (
            HybridSearchService(
                bm25_service=self.bm25_service,
                vector_service=self.faiss_service,
                embedding_service=self.embedding_service,
                reranker=reranker
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
            # SPARSE SEARCH (OpenSearch BM25)
            # =====================================
            with bm25_latency.time():
                bm25_results = await (
                    self.bm25_service.search(
                        query=query,
                        top_k=top_k * 2,
                    )
                )

            # =====================================
            # DENSE SEARCH (FAISS)
            # =====================================
            with embedding_latency.time():
                query_embedding = await (
                    self.embedding_service.encode_query(
                        query
                    )
                )

            with faiss_latency.time():
                dense_results = await (
                    self.faiss_service.search(
                        query_embedding=query_embedding,
                        top_k=top_k * 2,
                    )
                )

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

            # =====================================
            # POSTGRESQL GOVERNANCE
            # =====================================
            with metadata_latency.time():
                enriched_results = (
                    self.metadata_service.enrich_results(
                        hybrid_results
                    )
                )

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