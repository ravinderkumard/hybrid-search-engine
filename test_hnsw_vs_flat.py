import time
from pathlib import Path

import faiss
import numpy as np

from app.core.config import settings
from app.services.embedding_service import (
    EmbeddingService,
)
from app.services.faiss_service import (
    FAISSService,
)


class FlatFAISSBenchmark:
    """
    Temporary benchmark loader for exact Flat index.

    Purpose:
    Compare:
    Flat vs HNSW
    """

    def __init__(self, flat_index_path):
        if not Path(
            flat_index_path
        ).exists():
            raise FileNotFoundError(
                f"Flat index not found: {flat_index_path}"
            )

        self.index = faiss.read_index(
            str(flat_index_path)
        )

    def search(
        self,
        query_embedding,
        top_k=10,
    ):
        query_vector = np.array(
            query_embedding
        ).astype("float32")

        if len(query_vector.shape) == 1:
            query_vector = np.expand_dims(
                query_vector,
                axis=0,
            )

        distances, indices = (
            self.index.search(
                query_vector,
                top_k,
            )
        )

        return indices[0], distances[0]


def compute_overlap(
    flat_indices,
    hnsw_indices,
):
    """
    Measures top-k overlap.
    """
    flat_set = set(flat_indices)
    hnsw_set = set(hnsw_indices)

    overlap = len(
        flat_set.intersection(
            hnsw_set
        )
    )

    return overlap


def main():
    print(
        "\n========================================="
    )
    print(
        "Benchmarking HNSW vs Flat FAISS"
    )
    print(
        "=========================================\n"
    )

    # =====================================
    # CONFIG
    # =====================================
    flat_index_path = (
        "data/faiss_flat.index"
    )

    hnsw_service = (
        FAISSService()
    )

    flat_service = (
        FlatFAISSBenchmark(
            flat_index_path
        )
    )

    embedding_service = (
        EmbeddingService()
    )

    # =====================================
    # TEST QUERIES
    # =====================================
    test_queries = [
        "machine learning",
        "python programming",
        "budget laptop",
        "cloud deployment",
        "data science",
    ]

    total_flat_time = 0
    total_hnsw_time = 0
    total_overlap = 0

    top_k = 10

    for query in test_queries:
        print(
            f"\nQUERY: {query}"
        )

        query_embedding = (
            embedding_service.encode_query(
                query
            )
        )

        # =================================
        # FLAT
        # =================================
        start = time.time()

        flat_indices, flat_distances = (
            flat_service.search(
                query_embedding,
                top_k=top_k,
            )
        )

        flat_time = (
            time.time() - start
        )

        total_flat_time += (
            flat_time
        )

        # =================================
        # HNSW
        # =================================
        start = time.time()

        hnsw_results = (
            hnsw_service.search(
                query_embedding,
                top_k=top_k,
            )
        )

        hnsw_time = (
            time.time() - start
        )

        total_hnsw_time += (
            hnsw_time
        )

        hnsw_indices = [
            int(
                result["doc_id"]
            )
            - 1
            for result in hnsw_results
        ]

        # =================================
        # OVERLAP
        # =================================
        overlap = compute_overlap(
            flat_indices,
            hnsw_indices,
        )

        total_overlap += overlap

        # =================================
        # OUTPUT
        # =================================
        print(
            f"Flat Time: {flat_time:.6f}s"
        )

        print(
            f"HNSW Time: {hnsw_time:.6f}s"
        )

        print(
            f"Top-{top_k} Overlap: "
            f"{overlap}/{top_k}"
        )

    # =====================================
    # FINAL SUMMARY
    # =====================================
    avg_flat = (
        total_flat_time
        / len(test_queries)
    )

    avg_hnsw = (
        total_hnsw_time
        / len(test_queries)
    )

    avg_overlap = (
        total_overlap
        / len(test_queries)
    )

    speedup = (
        avg_flat / avg_hnsw
        if avg_hnsw > 0
        else 0
    )

    print(
        "\n========================================="
    )
    print(
        "FINAL BENCHMARK SUMMARY"
    )
    print(
        "=========================================\n"
    )

    print(
        f"Average Flat Time: "
        f"{avg_flat:.6f}s"
    )

    print(
        f"Average HNSW Time: "
        f"{avg_hnsw:.6f}s"
    )

    print(
        f"Average Speedup: "
        f"{speedup:.2f}x"
    )

    print(
        f"Average Top-{top_k} Overlap: "
        f"{avg_overlap:.2f}/{top_k}"
    )

    print(
        "\nInterpretation:"
    )

    if avg_overlap >= 8:
        print(
            "HNSW recall quality is strong."
        )
    elif avg_overlap >= 5:
        print(
            "HNSW acceptable, consider higher efSearch."
        )
    else:
        print(
            "Recall weak — tune HNSW parameters."
        )


if __name__ == "__main__":
    main()