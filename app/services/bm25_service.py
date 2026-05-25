from typing import List, Dict, Any

from app.core.config import settings
from app.core.opensearch_client import OpenSearchClient
from app.services.metrics import bm25_latency
from app.core.logger import logger

class BM25Service:
    """
    OpenSearch-backed BM25 sparse retrieval service.

    Replaces:
    - rank_bm25

    Why:
    - Scalable to 1M+ docs
    - Distributed sparse retrieval
    - BM25 precision preserved
    """

    def __init__(self):
        self.client = OpenSearchClient.get_client()
        self.index_name = settings.OPENSEARCH_INDEX

    # =========================================
    # SEARCH
    #  O(N)
    #. O(LogN)
    #   ANN - HNSW
    # =========================================
    async def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Performs BM25 sparse retrieval using OpenSearch.

        Returns:
            [
                {
                    doc_id,
                    title,
                    content,
                    bm25_score,
                    bm25_rank
                }
            ]
        """
        with bm25_latency.time():
            if not query or not query.strip():
                return []

            top_k = max(
                1,
                min(top_k, settings.MAX_TOP_K),
            )

            search_body = {
                "size": top_k,
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "title^2",
                            "content",
                        ],
                        "type": "best_fields",
                    }
                },
            }

            try:
                response = await self.client.search(
                    index=self.index_name,
                    body=search_body,
                    request_timeout=10,
                )

                hits = response.get(
                    "hits", {}
                ).get("hits", [])

                results = []

                for rank, hit in enumerate(
                    hits, start=1
                ):
                    source = hit.get(
                        "_source", {}
                    )

                    raw_doc_id = source.get("id")

                    try:
                        doc_id = int(raw_doc_id)
                    except (TypeError, ValueError):
                        continue

                    results.append(
                        {
                            "doc_id": doc_id,
                            "bm25_score": float(
                                hit.get(
                                    "_score", 0.0
                                )
                            ),
                            "bm25_rank": rank,
                        }
                    )

                logger.info({
                    "stage": "bm25_search",
                    "query": query,
                    "requested_top_k": top_k,
                    "returned_results": len(results),
                })

                return results

            except Exception as e:
                logger.exception(
                    "OpenSearch BM25 search error"
                )
                return []

    # =========================================
    # HEALTH
    # =========================================
    async def health_check(self) -> bool:
        """
        Validates OpenSearch availability.
        """
        try:
            return await self.client.ping()
        except Exception:
            return False
