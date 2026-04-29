from app.core.config import settings

class HybridSearchService:
    def __init__(self, bm25_service, vector_service, embedding_service):
        self.bm25_service = bm25_service
        self.vector_service = vector_service
        self.embedding_service = embedding_service

    def reciprocal_rank_fusion(self, bm25_results, vector_results, k=60):
        fused_scores = {}

        # BM25 contribution
        for item in bm25_results:
            doc = item["doc"]
            doc_id = doc["id"]

            
            if doc_id not in fused_scores:
                fused_scores[doc_id] = {
                    "doc": doc,
                    "bm25_rank": None,
                    "bm25_score": None,
                    "dense_rank": None,
                    "dense_similarity": None,
                    "dense_distance": None,
                    "bm25_rrf": 0,
                    "dense_rrf": 0,
                    "final_score": 0
                }

            bm25_rrf = 1 / (k + item["bm25_rank"])

            fused_scores[doc_id]["bm25_rank"] = item["bm25_rank"]
            fused_scores[doc_id]["bm25_score"] = item["bm25_score"]
            fused_scores[doc_id]["bm25_rrf"] = bm25_rrf
            


        # Dense contribution
        for item in vector_results:
            doc = item["doc"]
            doc_id = doc["id"]

            if doc_id not in fused_scores:
                fused_scores[doc_id] = {
                    "doc": doc,
                    "bm25_rank": None,
                    "bm25_score": None,
                    "dense_rank": None,
                    "dense_distance": None,
                    "dense_similarity": None,
                    "bm25_rrf": 0,
                    "dense_rrf": 0,
                    "final_score": 0
                }

            dense_rrf = 1 / (k + item["dense_rank"])

            fused_scores[doc_id]["dense_rank"] = item["dense_rank"]
            fused_scores[doc_id]["dense_distance"] = item["dense_distance"]
            fused_scores[doc_id]["dense_similarity"] = item["dense_similarity"]
            fused_scores[doc_id]["dense_rrf"] = dense_rrf
            

        # Sort by final fused score
        for doc_id in fused_scores:
            fused_scores[doc_id]["final_score"] = (
                fused_scores[doc_id]["bm25_rrf"] +
                fused_scores[doc_id]["dense_rrf"]
            )

        ranked_results = sorted(
            fused_scores.values(),
            key=lambda x: x["final_score"],
            reverse=True
        )

        return ranked_results

    def search(self, query, top_k=5):
        if top_k is None:
            top_k = settings.TOP_K

        retrieval_k = settings.RETRIEVAL_K
        bm25_results = self.bm25_service.search(query, top_k=retrieval_k)

        query_embedding = self.embedding_service.encode_query(query)

        vector_results = self.vector_service.search(
            query_embedding,
            top_k=retrieval_k
        )

        if not bm25_results and not vector_results:
            return []
        
        if not bm25_results:
            return [
                {
                    "doc": item["doc"],
                    "bm25_rank": None,
                    "bm25_score": None,
                    "dense_rank": item["dense_rank"],
                    "dense_similarity": item["dense_similarity"],
                    "dense_distance": item["dense_distance"],
                    "bm25_rrf": 0.0,
                    "dense_rrf": 1/(retrieval_k + item["dense_rank"]),
                    "final_score": 1/(retrieval_k + item["dense_rank"])
                }
                for item in vector_results[:top_k]
            ]

        if not vector_results:
            return [
                {
                    "doc": item["doc"],
                    "bm25_rank": item["bm25_rank"],
                    "bm25_score": item["bm25_score"],
                    "dense_rank": None,
                    "dense_similarity": None,
                    "dense_distance": None,
                    "bm25_rrf": 1/(retrieval_k + item["bm25_rank"]),
                    "dense_rrf": 0.0,
                    "final_score": 1/(retrieval_k + item["bm25_rank"])
                }
                for item in bm25_results[:top_k]
            ]

        fused_results = self.reciprocal_rank_fusion(
            bm25_results,
            vector_results
        )

        return fused_results[:top_k]