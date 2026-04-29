from app.services.data_loader import load_documents
from app.services.bm25_service import BM25Service
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.hybrid_service import HybridSearchService

# Load data
documents = load_documents()

# Initialize services
bm25_service = BM25Service(documents)

embedding_service = EmbeddingService()

doc_embeddings = embedding_service.encode_documents(documents)

vector_service = VectorService(documents, doc_embeddings)

hybrid_service = HybridSearchService(
    bm25_service,
    vector_service,
    embedding_service
)

# Test query
query = "best laptop for programming"

results = hybrid_service.search(query, top_k=2)

print(f"\nQUERY: {query}\n")
print("=" * 120)

for rank, result in enumerate(results, start=1):
    print(f"""
        FINAL RANK: #{rank}
        ID: {result['doc']['id']}
        TITLE: {result['doc']['title']}

        BM25:
        Rank: {result['bm25_rank']}
        Score: {result['bm25_score']}

        DENSE:
        Rank: {result['dense_rank']}
        Similarity: {result['dense_similarity']}
        Distance: {result['dense_distance']}

        RRF CONTRIBUTION:
        BM25 RRF: {result['bm25_rrf']:.6f}
        Dense RRF: {result['dense_rrf']:.6f}

        FINAL HYBRID SCORE:
        {result['final_score']:.6f}
        """)
    print("-" * 120)