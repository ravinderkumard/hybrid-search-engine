import json
import sys
from pathlib import Path

import faiss
import numpy as np

# =========================================
# PROJECT ROOT FIX
# =========================================
sys.path.append(
    str(
        Path(__file__)
        .resolve()
        .parent.parent
    )
)

from app.core.config import settings
from app.services.embedding_service import (
    EmbeddingService,
)
from app.core.redis_client import redis_client

# =========================================
# LOAD DOCUMENTS
# =========================================
def load_documents():
    """
    Loads source corpus from documents.json
    """
    path = Path(
        settings.DATA_PATH
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {settings.DATA_PATH}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


# =========================================
# MAIN
# =========================================
def main():
    print(
        "\n========================================="
    )
    print(
        "Building FAISS HNSW Index"
    )
    print(
        "=========================================\n"
    )

    # =====================================
    # LOAD DOCS
    # =====================================
    documents = load_documents()

    if not documents:
        print(
            "No documents found."
        )
        return

    print(
        f"Loaded {len(documents)} documents."
    )

    # =====================================
    # EMBEDDING SERVICE
    # =====================================
    embedding_service = (
        EmbeddingService(redis_client)
    )

    corpus = []

    # =====================================
    # DOCSTORE MAP
    # =====================================
    docstore = {}

    # =====================================
    # BUILD TEXT CORPUS
    # =====================================
    for idx, doc in enumerate(
        documents
    ):
        combined_text = (
            f"{doc.get('title', '')} "
            f"{doc.get('content', '')}"
        ).strip()

        corpus.append(
            combined_text
        )

        # =============================
        # DOC ID → VECTOR INDEX
        # =============================
        docstore[
            str(doc["id"])
        ] = idx

    # =====================================
    # GENERATE EMBEDDINGS
    # =====================================
    print(
        "Generating embeddings..."
    )

    embeddings = (
        embedding_service.model.encode(
            corpus,
            convert_to_numpy=True,
            show_progress_bar=True,
        )
    )

    embeddings = np.array(
        embeddings
    ).astype("float32")

    dimension = (
        embeddings.shape[1]
    )

    print(
        f"Embedding shape: {embeddings.shape}"
    )

    # =====================================
    # HNSW INDEX
    # =====================================
    print(
        "\nBuilding HNSW index..."
    )

    index = faiss.IndexHNSWFlat(
        dimension,
        32,  # M
    )

    # Graph build quality
    index.hnsw.efConstruction = 200

    # Query quality
    index.hnsw.efSearch = (
        settings.FAISS_EF_SEARCH
    )

    # =====================================
    # ADD EMBEDDINGS
    # =====================================
    index.add(
        embeddings
    )

    print(
        f"Indexed {index.ntotal} vectors."
    )

    # =====================================
    # OUTPUT PATHS
    # =====================================
    index_output_path = Path(
        settings.FAISS_INDEX_PATH
    )

    docstore_output_path = Path(
        "data/faiss_docstore.json"
    )

    index_output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # =====================================
    # SAVE INDEX
    # =====================================
    faiss.write_index(
        index,
        str(index_output_path),
    )

    # =====================================
    # SAVE DOCSTORE
    # =====================================
    with open(
        docstore_output_path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            docstore,
            f,
            indent=2,
        )

    print(
        f"\nFAISS HNSW index saved to: "
        f"{index_output_path}"
    )

    print(
        f"FAISS docstore saved to: "
        f"{docstore_output_path}"
    )

    # =====================================
    # FINAL SUMMARY
    # =====================================
    print(
        "\n========================================="
    )
    print(
        "BUILD COMPLETE"
    )
    print(
        "========================================="
    )

    print(
        f"Documents indexed: {len(documents)}"
    )

    print(
        f"Vector dimension: {dimension}"
    )

    print(
        "Index type: HNSW"
    )

    print(
        "M: 32"
    )

    print(
        "efConstruction: 200"
    )

    print(
        f"efSearch: {settings.FAISS_EF_SEARCH}"
    )


if __name__ == "__main__":
    main()