from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.services.metrics import embedding_latency
import asyncio
import json
import numpy as np

class EmbeddingService:
    def __init__(self,redis_client):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.model.encode(
            ["warmup"],
            convert_to_numpy=True
        )
        self.redis = redis_client

    def _normalize_embeddings(self, embeddings):
        array = np.array(embeddings).astype("float32")

        if len(array.shape) == 1:
            array = np.expand_dims(array, axis=0)

        if len(array.shape) > 2:
            raise ValueError(
                f"Invalid embedding shape: {array.shape}"
            )

        return array

    def _build_cache_key(self, query: str) -> str:
        normalized_query = query.strip().lower()
        return f"embedding:{settings.EMBEDDING_MODEL}:{normalized_query}"

    def encode_documents(self, documents):
        texts = [
            doc["title"] + ". " + doc["content"]
            for doc in documents
        ]
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return self._normalize_embeddings(embeddings)

    async def encode_query(self, query):
        cache_key = self._build_cache_key(query)
        cached_embedding = await self.redis.get(cache_key)
        if cached_embedding:
            cached_vector = np.array(
                json.loads(cached_embedding)
            ).astype("float32")

            if len(cached_vector.shape) == 1:
                cached_vector = np.expand_dims(
                    cached_vector,
                    axis=0,
                )

            return cached_vector
        with embedding_latency.time():
            
            embedding = await asyncio.to_thread(
                self.model.encode,
                [query],
                convert_to_numpy=True,
                normalize_embeddings = True
            )

            normalized_embedding = self._normalize_embeddings(
                embedding
            )

            await self.redis.set(
                cache_key,
                json.dumps(normalized_embedding.tolist()),
                ex=86400,
            )

            return normalized_embedding
