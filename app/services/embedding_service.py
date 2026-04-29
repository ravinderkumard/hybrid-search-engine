from sentence_transformers import SentenceTransformer
from app.core.config import settings

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)

    def encode_documents(self, documents):
        texts = [
            doc["title"] + ". " + doc["content"]
            for doc in documents
        ]
        return self.model.encode(texts, convert_to_numpy=True)

    def encode_query(self, query):
        return self.model.encode([query], convert_to_numpy=True)