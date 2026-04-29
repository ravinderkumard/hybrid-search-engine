from app.services.data_loader import load_documents
from app.services.bm25_service import BM25Service
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.hybrid_service import HybridSearchService


class SearchEngine:
    def __init__(self):
        self.documents = load_documents()

        self.bm25_service = BM25Service(self.documents)

        self.embedding_service = EmbeddingService()

        doc_embeddings = self.embedding_service.encode_documents(
            self.documents
        )

        self.vector_service = VectorService(
            self.documents,
            doc_embeddings
        )

        self.hybrid_service = HybridSearchService(
            self.bm25_service,
            self.vector_service,
            self.embedding_service
        )

    def search(self, query: str, top_k: int = 5):
        return self.hybrid_service.search(
            query=query,
            top_k=top_k
        )