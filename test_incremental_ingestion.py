from app.services.document_ingestion_service import (
    DocumentIngestionService,
)
from app.engine.search_engine import (
    SearchEngine,
)


TEST_DOC = {
    "id": "incremental_test_001",
    "title": "Enterprise AI Governance",
    "content": (
        "Enterprise AI governance ensures "
        "compliance, model oversight, "
        "risk management, and auditability."
    ),
    "category": "ai",
    "source": "internal",
}


def print_results(results):
    for rank, result in enumerate(
        results,
        start=1,
    ):
        print(
            f"""
==================================================
RANK #{rank}
--------------------------------------------------
DOC ID: {result.get('doc_id')}
TITLE: {result.get('title')}
CATEGORY: {result.get('category')}
SOURCE: {result.get('source')}
VERSION: {result.get('version')}
FINAL SCORE: {result.get('final_score')}
==================================================
"""
        )


def main():
    print(
        "\n========================================="
    )
    print(
        "Testing Incremental Ingestion Pipeline"
    )
    print(
        "=========================================\n"
    )

    ingestion_service = (
        DocumentIngestionService()
    )

    search_engine = (
        SearchEngine()
    )

    try:
        # =====================================
        # INSERT
        # =====================================
        print(
            "STEP 1: Initial ingestion"
        )

        response = (
            ingestion_service.ingest_document(
                TEST_DOC
            )
        )

        print(response)

        if not response.get(
            "success"
        ):
            print(
                "Initial ingestion failed."
            )
            return

        # =====================================
        # SEARCH VALIDATION
        # =====================================
        print(
            "\nSTEP 2: Search validation"
        )

        search_response = (
            search_engine.search(
                query="AI governance compliance",
                top_k=5,
            )
        )

        results = search_response.get(
            "results", []
        )

        print_results(results)

        # =====================================
        # UPDATE
        # =====================================
        print(
            "\nSTEP 3: Version update"
        )

        updated_doc = {
            **TEST_DOC,
            "content": (
                TEST_DOC[
                    "content"
                ]
                + " Updated governance controls."
            ),
        }

        update_response = (
            ingestion_service.ingest_document(
                updated_doc
            )
        )

        print(update_response)

        # =====================================
        # SOFT DELETE
        # =====================================
        print(
            "\nSTEP 4: Soft delete"
        )

        delete_success = (
            ingestion_service.soft_delete_document(
                TEST_DOC["id"]
            )
        )

        print(
            {
                "soft_delete": (
                    delete_success
                )
            }
        )

        # =====================================
        # SEARCH POST DELETE
        # =====================================
        print(
            "\nSTEP 5: Search after delete"
        )

        post_delete_response = (
            search_engine.search(
                query="AI governance compliance",
                top_k=5,
            )
        )

        post_results = (
            post_delete_response.get(
                "results",
                [],
            )
        )

        deleted_present = any(
            r["doc_id"]
            == TEST_DOC["id"]
            for r in post_results
        )

        print(
            {
                "deleted_doc_present": (
                    deleted_present
                )
            }
        )

        if not deleted_present:
            print(
                "\nGovernance enforcement successful."
            )

    finally:
        ingestion_service.close()
        search_engine.close()


if __name__ == "__main__":
    main()