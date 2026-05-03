from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.services.metrics import embedding_latency

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.model.encode(
            ["warmup"],
            convert_to_numpy=True
        )

    def encode_documents(self, documents):
        texts = [
            doc["title"] + ". " + doc["content"]
            for doc in documents
        ]
        return self.model.encode(texts, convert_to_numpy=True,normalize_embeddings=True)

    def encode_query(self, query):
        with embedding_latency.time():
            return self.model.encode([query], convert_to_numpy=True,normalize_embeddings=True)