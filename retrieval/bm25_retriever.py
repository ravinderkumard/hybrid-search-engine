from rank_bm25 import BM25Okapi

class BM25Retriever:
    def __init__(self, documents):

        self.documents = documents

        self.doc_ids = [doc["id"] for doc in documents]

        self.corpus = [
            (
                doc.get("title", "") + " " +
                doc.get("abstract", "")
            ).split()
            for doc in documents
        ]

        self.bm25 = BM25Okapi(self.corpus)

    def retrieve(self, query, top_k=5):

        tokenized_query = query.split()

        scores = self.bm25.get_scores(tokenized_query)

        ranked = sorted(
            zip(self.doc_ids, scores),
            key=lambda x: x[1],
            reverse=True
        )

        return [doc_id for doc_id, _ in ranked[:top_k]]