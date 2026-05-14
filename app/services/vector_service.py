import faiss
import numpy as np
from app.core.config import settings
import asyncio

class VectorService:
    def __init__(self, documents, embeddings):
        self.documents = documents
        self.dimension = embeddings.shape[1]

        # L2 similarity index
        self.index = faiss.IndexFlatL2(self.dimension)

        # Add embeddings
        self.index.add(np.array(embeddings).astype("float32"))

    async def search(self, query_embedding, top_k=10):
        if top_k is None:
            top_k = settings.RETRIEVAL_K

        distances, indices = await asyncio.to_thread(
            self.index.search,
            query_embedding.astype("float32"),
            top_k
        )

        results = []

        for rank, idx in enumerate(indices[0]):
            distance = float(distances[0][rank])

            if idx < 0 or idx >= len(self.documents):
                continue

            similarity = 1 / (1 + distance)

            if similarity > settings.DENSE_MIN_SIMILARITY:
                results.append({
                    "doc": self.documents[idx],
                    "dense_distance": distance,
                    "dense_similarity": similarity,
                    "dense_rank": rank + 1
                })

        return results