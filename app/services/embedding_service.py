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

    def encode_documents(self, documents):
        texts = [
            doc["title"] + ". " + doc["content"]
            for doc in documents
        ]
        return self.model.encode(texts, convert_to_numpy=True,normalize_embeddings=True)

    async def encode_query(self, query):
        cache_key = f"embedding:{query}"
        cached_embedding = await self.redis.get(cache_key)
        if cached_embedding:
            return np.array(
                json.loads(cached_embedding)
            )
        with embedding_latency.time():
            
            embedding = await asyncio.to_thread(
                self.model.encode,
                [query],
                convert_to_numpy=True,
                normalize_embeddings = True
            )
            await self.redis.set(cache_key,json.dumps(embedding.tolist()),ex=86400)
            return embedding