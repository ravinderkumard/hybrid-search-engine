import time

from app.services.embedding_service import (
    EmbeddingService,
)
from app.services.faiss_service import (
    FAISSService,
)


def print_result(result, rank):
    print(
        f"""
==================================================
RANK #{rank}
--------------------------------------------------
DOC ID: {result.get('doc_id')}
TITLE: {result.get('title')}
DENSE SCORE: {result.get('dense_score')}
SIMILARITY: {result.get('dense_similarity')}
DISTANCE: {result.get('dense_distance')}
CONTENT:
{result.get('content')}
==================================================
"""
    )


def main():
    print(
        "\n========================================="
    )
    print(
        "Testing Dense Retrieval (FAISS)"
    )
    print(
        "=========================================\n"
    )

    # =====================================
    # INIT
    # =====================================
    try:
        embedding_service = (
            EmbeddingService()
        )

        faiss_service = (
            FAISSService()
        )

    except Exception as e:
        print(
            f"Initialization failed: {e}"
        )
        return

    # =====================================
    # HEALTH
    # =====================================
    if not faiss_service.health_check():
        print(
            "FAISS service unavailable."
        )
        return

    print(
        "FAISS service healthy.\n"
    )

    # =====================================
    # TEST QUERIES
    # =====================================
    test_queries = [
        "machine learning",
        "python programming",
        "budget laptop",
    ]

    for query in test_queries:
        print(
            f"\nQUERY: {query}"
        )

        try:
            start_time = time.time()

            # =============================
            # EMBEDDING
            # =============================
            query_embedding = (
                embedding_service.encode_query(
                    query
                )
            )

            # Shape diagnostics
            try:
                print(
                    f"Embedding shape: {query_embedding.shape}"
                )
            except AttributeError:
                print(
                    "Embedding shape unavailable."
                )

            # =============================
            # DENSE SEARCH
            # =============================
            results = (
                faiss_service.search(
                    query_embedding=query_embedding,
                    top_k=3,
                )
            )

            elapsed = (
                time.time()
                - start_time
            )

            print(
                f"Search completed in {elapsed:.4f} seconds."
            )

            if not results:
                print(
                    "No results found."
                )
                continue

            print(
                f"Returned {len(results)} results.\n"
            )

            for rank, result in enumerate(
                results,
                start=1,
            ):
                print_result(
                    result,
                    rank,
                )

        except Exception as e:
            print(
                f"Query failed: {e}"
            )


if __name__ == "__main__":
    main()