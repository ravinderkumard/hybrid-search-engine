import faiss
import numpy as np
import asyncio
import pickle
from pathlib import Path

from app.core.config import settings


INDEX_PATH = "storage/faiss.index"
DOCS_PATH = "storage/documents.pkl"


class VectorService:

    def __init__(self):

        self.documents = []
        self.index = None

        self.load()

    def load(self):

        # Load FAISS index
        if Path(INDEX_PATH).exists():
            self.index = faiss.read_index(INDEX_PATH)

        # Load documents
        if Path(DOCS_PATH).exists():
            with open(DOCS_PATH, "rb") as f:
                self.documents = pickle.load(f)

    def save(self):

        faiss.write_index(self.index, INDEX_PATH)

        with open(DOCS_PATH, "wb") as f:
            pickle.dump(self.documents, f)

    def build(self, documents, embeddings):

        self.documents = documents

        dimension = embeddings.shape[1]

        # Better similarity search
        self.index = faiss.IndexFlatIP(dimension)

        embeddings = np.array(
            embeddings
        ).astype("float32")

        # Normalize embeddings
        faiss.normalize_L2(embeddings)

        self.index.add(embeddings)

        self.save()

    async def reload(self):

        await asyncio.to_thread(self.load)

    async def search(self, query_embedding, top_k=10):

        if self.index is None:
            return []

        if self.index.ntotal == 0:
            return []

        query_embedding = query_embedding.astype("float32")

        # Normalize query
        faiss.normalize_L2(query_embedding)

        distances, indices = await asyncio.to_thread(
            self.index.search,
            query_embedding,
            top_k
        )

        print({
            "indices": indices[0].tolist(),
            "distances": distances[0].tolist(),
            "total_vectors": self.index.ntotal
        })

        results = []

        for rank, idx in enumerate(indices[0]):

            if idx < 0 or idx >= len(self.documents):
                continue

            similarity = float(distances[0][rank])

            if similarity > settings.DENSE_MIN_SIMILARITY:

                results.append({
                    "doc": self.documents[idx],
                    "dense_distance": similarity,
                    "dense_similarity": similarity,
                    "dense_rank": rank + 1
                })

        return results