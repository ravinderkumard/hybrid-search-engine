import json
from pathlib import Path
from typing import List, Dict, Any

import faiss
import numpy as np

from app.core.config import settings


class FAISSService:
    """
    Dense retrieval service using FAISS.

    Why:
    - Semantic retrieval
    - Scalable ANN migration path
    - Hybrid compatibility
    """

    def __init__(self):
        self.index_path = (
            settings.FAISS_INDEX_PATH
        )

        self.data_path = (
            settings.DATA_PATH
        )

        self.index = self._load_index()

        self.documents = (
            self._load_documents()
        )

    # =========================================
    # LOAD INDEX
    # =========================================
    def _load_index(self):
        """
        Loads FAISS index from disk.
        """
        if not Path(
            self.index_path
        ).exists():
            raise FileNotFoundError(
                f"FAISS index not found: {self.index_path}"
            )

        return faiss.read_index(
            self.index_path
        )

    # =========================================
    # LOAD DOCS
    # =========================================
    def _load_documents(self):
        """
        Loads source documents metadata.
        """
        if not Path(
            self.data_path
        ).exists():
            raise FileNotFoundError(
                f"Documents not found: {self.data_path}"
            )

        with open(
            self.data_path,
            "r",
            encoding="utf-8",
        ) as f:
            docs = json.load(f)

        return docs

    # =========================================
    # SEARCH
    # =========================================
    def search(
        self,
        query_embedding,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Dense retrieval against FAISS.

        Returns:
        [
            {
                doc_id,
                title,
                content,
                dense_score,
                dense_rank,
                dense_similarity
            }
        ]
        """

        if query_embedding is None:
            return []

        query_vector = np.array(
            query_embedding
        ).astype("float32")

        # Ensure shape is exactly (1, dim)
        if len(query_vector.shape) == 1:
            query_vector = np.expand_dims(
                query_vector,
                axis=0,
            )

        # If already (1, dim), leave unchanged
        elif len(query_vector.shape) > 2:
            raise ValueError(
                f"Invalid query embedding shape: {query_vector.shape}"
            )

        distances, indices = (
            self.index.search(
                query_vector,
                top_k,
            )
        )

        results = []

        for rank, (
            idx,
            distance,
        ) in enumerate(
            zip(
                indices[0],
                distances[0],
            ),
            start=1,
        ):
            if (
                idx < 0
                or idx >= len(
                    self.documents
                )
            ):
                continue

            doc = self.documents[idx]

            # Convert L2 distance → similarity proxy
            similarity = (
                1 / (1 + distance)
                if distance >= 0
                else 0
            )

            results.append(
                {
                    "doc_id": str(
                        doc.get("id")
                    ),
                    "title": doc.get(
                        "title", ""
                    ),
                    "content": doc.get(
                        "content", ""
                    ),
                    "dense_score": float(
                        similarity
                    ),
                    "dense_rank": rank,
                    "dense_similarity": float(
                        similarity
                    ),
                    "dense_distance": float(
                        distance
                    ),
                }
            )

        return results

    # =========================================
    # HEALTH
    # =========================================
    def health_check(self) -> bool:
        """
        Validates FAISS index readiness.
        """
        return (
            self.index is not None
            and len(
                self.documents
            )
            > 0
        )