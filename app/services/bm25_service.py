from rank_bm25 import BM25Okapi
from app.core.config import settings

class BM25Service:
    def __init__(self, documents):
        self.documents = documents

        # Combine title + content
        self.corpus = [
            (doc["title"] + " " + doc["content"]).lower().split()
            for doc in documents
        ]

        self.bm25 = BM25Okapi(self.corpus)

    def search(self, query, top_k=10):
        tokenized_query = query.lower().split()

        scores = self.bm25.get_scores(tokenized_query)

        ranked_docs = sorted(
            [
                {
                    "doc": doc,
                    "bm25_score": score
                }
                for doc, score in zip(self.documents, scores)
                if score > settings.BM25_MIN_SCORE
            ],
            key=lambda x: x["bm25_score"],
            reverse=True
        )
        
        for rank, item in enumerate(ranked_docs):
            item["bm25_rank"] = rank + 1
        return ranked_docs[:top_k]