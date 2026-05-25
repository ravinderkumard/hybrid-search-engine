from app.core.config import settings
from collections import defaultdict
from app.services.metrics import rrf_latency
from app.services.metrics import (
    hybrid_mode_counter,
    dense_confident_counter,
    bm25_confident_counter,
    dense_only_fallback_counter,
    bm25_only_fallback_counter,
    no_strong_match_counter,
)
import asyncio
import time
from app.core.logger import logger

class HybridSearchService:
    def __init__(self, bm25_service, vector_service, embedding_service):
        self.bm25_service = bm25_service
        self.vector_service = vector_service
        self.embedding_service = embedding_service
        self.last_mode = None
        self.last_message = None

    def _set_state(self, mode, message=None):
        self.last_mode = mode
        self.last_message = message

    def _is_dense_confident(self, dense_results):
        if not dense_results:
            return False

        top_dense = dense_results[0].get("dense_similarity", 0.0)
        return top_dense <= settings.MAX_DENSE_DISTANCE

    def _is_bm25_confident(self, bm25_results):
        if not bm25_results:
            return False

        top_bm25 = bm25_results[0].get("bm25_score", 0.0)
        return top_bm25 >= settings.MIN_BM25_SCORE

    def _normalize_doc_id(self, doc_id):
        try:
            return str(int(doc_id))
        except (TypeError, ValueError):
            return None

    def reciprocal_rank_fusion(self, bm25_results, dense_results, top_k, k=60):
        fused_scores = defaultdict(
            lambda: {
                "doc_id": None,
                "bm25_rank": None,
                "bm25_score": None,
                "dense_rank": None,
                "dense_similarity": None,
                "final_score": 0.0,
            }
        )

        # BM25 contribution
        for result in bm25_results:
            doc_id = self._normalize_doc_id(result["doc_id"])
            if doc_id is None:
                continue

            fused_scores[doc_id][
                "doc_id"
            ] = doc_id

            fused_scores[doc_id][
                "bm25_rank"
            ] = result["bm25_rank"]

            fused_scores[doc_id][
                "bm25_score"
            ] = result["bm25_score"]

            fused_scores[doc_id][
                "final_score"
            ] += 1 / (
                k + result["bm25_rank"]
            )


        # Dense contribution
        for result in dense_results:
            if result["dense_similarity"] < settings.MIN_DENSE_SIMILARITY:
                continue
            doc_id = self._normalize_doc_id(result["doc_id"])
            if doc_id is None:
                continue

            fused_scores[doc_id][
                "doc_id"
            ] = doc_id

            fused_scores[doc_id][
                "dense_rank"
            ] = result["dense_rank"]

            fused_scores[doc_id][
                "dense_similarity"
            ] = result[
                "dense_similarity"
            ]

            fused_scores[doc_id][
                "final_score"
            ] += 1 / (
                k + result["dense_rank"]
            )
        
        ranked_results = sorted(
            fused_scores.values(),
            key=lambda x: x["final_score"],
            reverse=True
        )

        return ranked_results[:top_k]

    async def search(self, query, top_k=5):
        self._set_state(None, None)
        if top_k is None:
            top_k = settings.TOP_K

        retrieval_k = settings.RETRIEVAL_K
        retrieval_start = time.perf_counter()
        bm25_task = asyncio.create_task(
            self.bm25_service.search(query, top_k=retrieval_k)
        )
        embedding_task = asyncio.create_task(
            self.embedding_service.encode_query(query)
        )
        bm25_results, query_embedding = await asyncio.gather(
            bm25_task,
            embedding_task,
        )
        retrieval_latency = (
            time.perf_counter() - retrieval_start
        ) * 1000
        logger.info({
            "stage": "parallel_retrieval",
            "latency_ms": round(retrieval_latency, 2),
            "query": query,
        })

        faiss_start = time.perf_counter()
        vector_results = await asyncio.wait_for(
            self.vector_service.search(
                query_embedding,
                top_k=retrieval_k,
            ),
            timeout=3,
        )
        faiss_latency_ms = (
            time.perf_counter() - faiss_start
        ) * 1000
        logger.info({
            "stage": "faiss_search",
            "latency_ms": round(faiss_latency_ms, 2),
        })

        if not bm25_results and not vector_results:
            no_strong_match_counter.inc()
            hybrid_mode_counter.labels(mode="no_strong_match").inc()
            self._set_state(
                "no_strong_match",
                "No strong match found in the current corpus.",
            )
            return []

        dense_confident = self._is_dense_confident(vector_results)
        bm25_confident = self._is_bm25_confident(bm25_results)

        if dense_confident:
            dense_confident_counter.inc()
        if bm25_confident:
            bm25_confident_counter.inc()

        if bm25_results and vector_results:
            with rrf_latency.time():
                fused_results = self.reciprocal_rank_fusion(
                    bm25_results,
                    vector_results,
                    top_k=top_k,
                )

            logger.info({
                "stage": "hybrid_mode",
                "mode": "rrf",
                "bm25_confident": bm25_confident,
                "dense_confident": dense_confident,
                "candidate_count": len(fused_results),
            })
            hybrid_mode_counter.labels(mode="rrf").inc()
            self._set_state("rrf")
            return fused_results[:top_k]

        if bm25_results:
            bm25_only_results = [
                {
                    "doc_id": self._normalize_doc_id(item.get("doc_id")),
                    "bm25_rank": item.get("bm25_rank"),
                    "bm25_score": item.get("bm25_score"),
                    "dense_rank": None,
                    "dense_similarity": None,
                    "final_score": 1 / (retrieval_k + item["bm25_rank"]),
                }
                for item in bm25_results[:top_k]
                if self._normalize_doc_id(item.get("doc_id")) is not None
            ]

            logger.info({
                "stage": "hybrid_mode",
                "mode": "bm25_only",
                "bm25_confident": bm25_confident,
                "dense_confident": dense_confident,
                "candidate_count": len(bm25_only_results),
            })
            hybrid_mode_counter.labels(mode="bm25_only").inc()
            bm25_only_fallback_counter.inc()
            self._set_state("bm25_only")
            return bm25_only_results

        if vector_results:
            no_strong_match_counter.inc()
            hybrid_mode_counter.labels(mode="no_strong_match").inc()
            logger.info({
                "stage": "hybrid_mode",
                "mode": "no_strong_match",
                "bm25_confident": bm25_confident,
                "dense_confident": dense_confident,
                "candidate_count": 0,
            })
            self._set_state(
                "no_strong_match",
                "No strong match found in the current corpus.",
            )
            return []

        no_strong_match_counter.inc()
        hybrid_mode_counter.labels(mode="no_strong_match").inc()
        self._set_state(
            "no_strong_match",
            "No strong match found in the current corpus.",
        )
        return []
