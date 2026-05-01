from app.engine.search_engine import (
    SearchEngine,
)


def print_result(result, rank):
    print(
        f"""
==================================================
FINAL RANK #{rank}
--------------------------------------------------
DOC ID: {result.get('doc_id')}
TITLE: {result.get('title')}
CATEGORY: {result.get('category')}
SOURCE: {result.get('source')}
VERSION: {result.get('version')}
ACTIVE METADATA: True

FINAL SCORE:
{result.get('final_score')}

BM25:
Rank: {result.get('bm25_rank')}
Score: {result.get('bm25_score')}

DENSE:
Rank: {result.get('dense_rank')}
Similarity: {result.get('dense_similarity')}

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
        "Testing Governance-Aware Search Engine"
    )
    print(
        "=========================================\n"
    )

    try:
        search_engine = (
            SearchEngine()
        )

    except Exception as e:
        print(
            f"Initialization failed: {e}"
        )
        return

    # =====================================
    # HEALTH
    # =====================================
    health = (
        search_engine.health_check()
    )

    print(
        "Component Health:"
    )

    for component, status in (
        health.items()
    ):
        print(
            f"{component}: {status}"
        )

    if not all(
        health.values()
    ):
        print(
            "\nSystem health degraded."
        )
        return

    print(
        "\nAll governance layers healthy."
    )

    # =====================================
    # TEST QUERIES
    # =====================================
    test_queries = [
        "machine learning",
        "budget laptop",
        "cloud deployment",
        "cybersecurity",
    ]

    for query in test_queries:
        print(
            f"\nQUERY: {query}"
        )

        try:
            response = (
                search_engine.search(
                    query=query,
                    top_k=5,
                )
            )

            results = response.get(
                "results", []
            )

            if not results:
                print(
                    "No governed results found."
                )
                continue

            print(
                f"Returned {len(results)} governed results.\n"
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

    # =====================================
    # CLEANUP
    # =====================================
    search_engine.close()


if __name__ == "__main__":
    main()