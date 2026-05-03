from app.core.config import settings
from collections import defaultdict
from app.services.metrics import rrf_latency,total_search_latency
class HybridSearchService:
    def __init__(self, bm25_service, vector_service, embedding_service):
        self.bm25_service = bm25_service
        self.vector_service = vector_service
        self.embedding_service = embedding_service

    def reciprocal_rank_fusion(self, bm25_results, dense_results, top_k, k=60):
        fused_scores = defaultdict(
            lambda: {
                "doc_id": None,
                "title": "",
                "content": "",
                "bm25_rank": None,
                "bm25_score": None,
                "dense_rank": None,
                "dense_similarity": None,
                "final_score": 0.0,
            }
        )

        # BM25 contribution
        for result in bm25_results:
            doc_id = result["doc_id"]

            fused_scores[doc_id][
                "doc_id"
            ] = doc_id
            fused_scores[doc_id][
                "title"
            ] = result["title"]
            fused_scores[doc_id][
                "content"
            ] = result["content"]

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
            # if result["dense_similarity"] < settings.MIN_DENSE_SIMILARITY:
            #     continue
            doc_id = result["doc_id"]

            fused_scores[doc_id][
                "doc_id"
            ] = doc_id
            fused_scores[doc_id][
                "title"
            ] = result["title"]
            fused_scores[doc_id][
                "content"
            ] = result["content"]

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
        print("RAW DENSE RESULTS:", dense_results)
        print("MIN_DENSE_SIMILARITY:", settings.MIN_DENSE_SIMILARITY)
        ranked_results = sorted(
            fused_scores.values(),
            key=lambda x: x["final_score"],
            reverse=True
        )

        return ranked_results[:top_k]

    def search(self, query, top_k=5):
        
            if top_k is None:
                top_k = settings.TOP_K

            retrieval_k = settings.RETRIEVAL_K
            bm25_results = self.bm25_service.search(query, top_k=retrieval_k)

            query_embedding = self.embedding_service.encode_query(query)
            print("QUERY:", query)
            vector_results = self.vector_service.search(
                query_embedding,
                top_k=retrieval_k
            )
            print("VECTOR RESULTS:", vector_results)
            print("VECTOR RESULT COUNT:", len(vector_results))
            if not bm25_results and not vector_results:
                return []
            
            if not bm25_results:
                return [
                    {
                        "doc_id": item.get(
                            "doc_id"
                        ),
                        "title": item.get(
                            "title"
                        ),
                        "content": item.get(
                            "content"
                        ),
                        "bm25_rank": None,
                        "bm25_score": None,
                        "dense_rank": item.get(
                            "dense_rank"
                        ),
                        "dense_similarity": item.get(
                            "dense_similarity"
                        ),
                        "dense_distance": item.get(
                            "dense_distance"
                        ),
                        "final_score": 1 / (
                            retrieval_k
                            + item["dense_rank"]
                        ),
                    }
                    for item in vector_results[:top_k]
                ]

            if not vector_results:
                return [
                    {
                        "doc_id": item.get(
                            "doc_id"
                        ),
                        "title": item.get(
                            "title"
                        ),
                        "content": item.get(
                            "content"
                        ),
                        "bm25_rank": item.get(
                            "bm25_rank"
                        ),
                        "bm25_score": item.get(
                            "bm25_score"
                        ),
                        "dense_rank": None,
                        "dense_similarity": None,
                        "dense_distance": None,
                        "final_score": 1 / (
                            retrieval_k
                            + item["bm25_rank"]
                        ),
                    }
                    for item in bm25_results[
                        :top_k
                    ]
                ]
            with rrf_latency.time():
                fused_results = self.reciprocal_rank_fusion(
                    bm25_results,
                    vector_results,
                    top_k=top_k,
                )

            return fused_results[:top_k]