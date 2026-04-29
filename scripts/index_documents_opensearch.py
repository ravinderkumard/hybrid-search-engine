import json
import sys
from pathlib import Path

from app.core.config import settings
from app.services.opensearch_index_service import (
    OpenSearchIndexService,
)


def load_documents(file_path: str):
    """
    Loads dataset from JSON file.

    Why:
    - Centralized validation
    - Cleaner ingestion pipeline
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    with open(path, "r", encoding="utf-8") as f:
        documents = json.load(f)

    if not isinstance(documents, list):
        raise ValueError(
            "Dataset must be a list of documents."
        )

    return documents


def validate_documents(documents):
    """
    Validates minimum schema requirements.

    Required:
    - id
    - title
    - content
    """
    validated = []

    for doc in documents:
        if (
            "id" not in doc
            or "title" not in doc
            or "content" not in doc
        ):
            print(
                f"Skipping invalid document: {doc}"
            )
            continue

        validated.append(
            {
                "id": str(doc["id"]),
                "title": doc.get("title", ""),
                "content": doc.get(
                    "content", ""
                ),
                "category": doc.get(
                    "category",
                    "general",
                ),
                "timestamp": doc.get(
                    "timestamp"
                ),
            }
        )

    return validated


def main():
    """
    Usage:
    python scripts/index_documents_opensearch.py

    Optional:
    python scripts/index_documents_opensearch.py --rebuild
    """
    rebuild = "--rebuild" in sys.argv

    print(
        "\n========================================="
    )
    print(
        "Hybrid Search Engine — OpenSearch Indexing"
    )
    print(
        "=========================================\n"
    )

    service = OpenSearchIndexService()

    # =========================================
    # REBUILD OR CREATE
    # =========================================
    if rebuild:
        print("Rebuilding index...")
        service.rebuild_index()
    else:
        print(
            "Ensuring index exists..."
        )
        service.create_index()

    # =========================================
    # LOAD DATASET
    # =========================================
    print(
        f"Loading documents from: {settings.DATA_PATH}"
    )

    documents = load_documents(
        settings.DATA_PATH
    )

    print(
        f"Loaded {len(documents)} raw documents."
    )

    # =========================================
    # VALIDATE
    # =========================================
    validated_documents = validate_documents(
        documents
    )

    print(
        f"Validated {len(validated_documents)} documents."
    )

    if not validated_documents:
        print(
            "No valid documents found."
        )
        return

    # =========================================
    # BULK INDEX
    # =========================================
    print(
        "Bulk indexing into OpenSearch..."
    )

    indexed_count = (
        service.bulk_index_documents(
            validated_documents
        )
    )

    print(
        f"Successfully indexed {indexed_count} documents."
    )

    # =========================================
    # STATS
    # =========================================
    stats = service.get_index_stats()

    try:
        total_docs = stats["indices"][
            settings.OPENSEARCH_INDEX
        ]["primaries"]["docs"]["count"]

        print(
            f"OpenSearch index now contains {total_docs} documents."
        )

    except Exception:
        print(
            "Unable to fetch final stats."
        )

    print(
        "\nIndexing complete."
    )


if __name__ == "__main__":
    main()