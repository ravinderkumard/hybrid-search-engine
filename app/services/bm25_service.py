from typing import List, Dict, Any

from app.core.config import settings
from app.core.opensearch_client import OpenSearchClient
from app.services.metrics import bm25_latency

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
    def search(
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
                response = self.client.search(
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

                    results.append(
                        {
                            "doc_id": str(
                                source.get("id")
                            ),
                            "title": source.get(
                                "title", ""
                            ),
                            "content": source.get(
                                "content", ""
                            ),
                            "bm25_score": float(
                                hit.get(
                                    "_score", 0.0
                                )
                            ),
                            "bm25_rank": rank,
                        }
                    )

                return results

            except Exception as e:
                print(
                    f"OpenSearch BM25 search error: {e}"
                )
                return []

    # =========================================
    # HEALTH
    # =========================================
    def health_check(self) -> bool:
        """
        Validates OpenSearch availability.
        """
        try:
            return self.client.ping()
        except Exception:
            return False