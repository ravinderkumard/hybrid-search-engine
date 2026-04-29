from app.services.bm25_service import BM25Service


def print_result(result, rank):
    print(
        f"""
==================================================
RANK #{rank}
--------------------------------------------------
DOC ID: {result.get('doc_id')}
TITLE: {result.get('title')}
BM25 SCORE: {result.get('bm25_score')}
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
        "Testing OpenSearch BM25 Sparse Retrieval"
    )
    print(
        "=========================================\n"
    )

    bm25 = BM25Service()

    # =====================================
    # HEALTH
    # =====================================
    if not bm25.health_check():
        print(
            "OpenSearch BM25 service unavailable."
        )
        return

    print(
        "OpenSearch BM25 service healthy.\n"
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

        results = bm25.search(
            query=query,
            top_k=3,
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
            results, start=1
        ):
            print_result(
                result,
                rank,
            )


if __name__ == "__main__":
    main()