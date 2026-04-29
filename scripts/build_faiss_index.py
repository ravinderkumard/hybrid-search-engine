import json
from pathlib import Path

import faiss
import numpy as np

from app.core.config import settings
from app.services.embedding_service import (
    EmbeddingService,
)


def load_documents():
    """
    Loads dataset from configured path.
    """
    path = Path(settings.DATA_PATH)

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


def main():
    print(
        "\n========================================="
    )
    print(
        "Building FAISS Dense Index"
    )
    print(
        "=========================================\n"
    )

    # =====================================
    # LOAD DATA
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
        EmbeddingService()
    )

    # =====================================
    # BUILD EMBEDDINGS
    # =====================================
    corpus = []

    for doc in documents:
        combined_text = (
            f"{doc.get('title', '')} "
            f"{doc.get('content', '')}"
        )

        corpus.append(
            combined_text.strip()
        )

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

    # =====================================
    # BUILD INDEX
    # =====================================
    dimension = embeddings.shape[1]

    print(
        f"Embedding dimension: {dimension}"
    )

    index = faiss.IndexFlatL2(
        dimension
    )

    index.add(embeddings)

    print(
        f"Indexed {index.ntotal} vectors."
    )

    # =====================================
    # SAVE INDEX
    # =====================================
    output_path = Path(
        settings.FAISS_INDEX_PATH
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    faiss.write_index(
        index,
        str(output_path),
    )

    print(
        f"\nFAISS index saved to: {output_path}"
    )

    print(
        "\nFAISS build complete."
    )


if __name__ == "__main__":
    main()