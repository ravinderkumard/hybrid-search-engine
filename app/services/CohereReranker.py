import cohere
import time
from app.core.logger import logger

class CohereReranker:
    def __init__(self, api_key):
        self.client = cohere.Client(api_key)
        

    def rerank(self, query, documents, top_k):
        texts = [
            f"{doc['title']} {doc['content']}"[:700]
            for doc in documents
        ]
        rerank_start = time.perf_counter()
        response = self.client.rerank(
            query=query,
            documents=texts,
            top_n=top_k
        )
        rerank_latency_ms = (
            time.perf_counter() - rerank_start
        ) * 1000
        logger.info({
            "stage": "reranker",
            "latency_ms": round(rerank_latency_ms, 2),
        })
        

        return [
            documents[result.index]
            for result in response.results
        ]