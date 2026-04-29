from app.services.opensearch_index_service import (
    OpenSearchIndexService,
)
from scripts.index_documents_opensearch import (
    load_documents,
    validate_documents,
)
from app.core.config import settings


def main():
    print(
        "\n========================================="
    )
    print(
        "Testing OpenSearch Index Creation + Ingestion"
    )
    print(
        "=========================================\n"
    )

    service = OpenSearchIndexService()

    # =====================================
    # REBUILD INDEX
    # =====================================
    print("Rebuilding index...")
    service.rebuild_index()

    # =====================================
    # LOAD DATA
    # =====================================
    print(
        f"Loading documents from: {settings.DATA_PATH}"
    )

    raw_documents = load_documents(
        settings.DATA_PATH
    )

    print(
        f"Loaded {len(raw_documents)} raw documents."
    )

    # =====================================
    # VALIDATE
    # =====================================
    documents = validate_documents(
        raw_documents
    )

    print(
        f"Validated {len(documents)} documents."
    )

    # =====================================
    # BULK INDEX
    # =====================================
    print(
        "Indexing documents into OpenSearch..."
    )

    indexed_count = (
        service.bulk_index_documents(
            documents
        )
    )

    print(
        f"Indexed {indexed_count} documents."
    )

    # =====================================
    # STATS
    # =====================================
    stats = service.get_index_stats()

    try:
        total_docs = stats["indices"][
            settings.OPENSEARCH_INDEX
        ]["primaries"]["docs"]["count"]

        print(
            f"\nFinal indexed document count: {total_docs}"
        )

        if total_docs > 0:
            print(
                "\nOpenSearch indexing successful."
            )
        else:
            print(
                "\nNo documents indexed."
            )

    except Exception as e:
        print(
            f"\nFailed to fetch stats: {e}"
        )


if __name__ == "__main__":
    main()