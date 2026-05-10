import cohere

class CohereReranker:
    def __init__(self, api_key):
        self.client = cohere.Client(api_key)
        

    def rerank(self, query, documents, top_k):
        texts = [
            f"{doc['title']} {doc['content']}"[:2000]
            for doc in documents
        ]

        response = self.client.rerank(
            query=query,
            documents=texts,
            top_n=top_k
        )

        return [
            documents[result.index]
            for result in response.results
        ]