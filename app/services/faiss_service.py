import json
from pathlib import Path
from typing import List, Dict, Any

import faiss
import numpy as np

from app.core.config import settings
import os


class FAISSService:
    """
    Dense retrieval service using FAISS.

    Why:
    - Semantic retrieval
    - Scalable ANN migration path
    - Hybrid compatibility
    """

    def __init__(self):
        # =====================================
        # PATHS FIRST
        # =====================================
        self.index_path = (
            settings.FAISS_INDEX_PATH
        )

        self.data_path = (
            settings.DATA_PATH
        )

        self.docstore_path = (
            "data/faiss_docstore.json"
        )

        # =====================================
        # LOAD DATA
        # =====================================
        self.index = (
            self._load_index()
        )

        self.documents = (
            self._load_documents()
        )

        self.doc_id_map = (
            self._load_docstore()
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

        index = faiss.read_index(
            self.index_path
        )

        if hasattr(index,"hnsw"):
            index.hnsw.efSearch = (
                settings.FAISS_EF_SEARCH
            )
            print(
                f"HNSW index detected. "
                f"efSearch set to "
                f"{settings.FAISS_EF_SEARCH}"
            )
        else:
            print(
                "Flat FAISS index detected"
            )
        return index

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

        # =====================================
        # OVER-FETCH FOR STALE FILTERING
        # =====================================
        search_k = max(
            top_k * 3,
            top_k,
        )

        distances, indices = (
            self.index.search(
                query_vector,
                search_k,
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

            doc_id = str(
                doc.get("id")
            )

            # =================================
            # STALE VECTOR FILTER
            # =================================
            latest_vector_index = (
                self.doc_id_map.get(
                    doc_id
                )
            )

            # Skip stale vectors
            if (
                latest_vector_index
                is not None
                and idx
                != latest_vector_index
            ):
                continue

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
    
    # =========================================
    # SAVE INDEX
    # =========================================
    def save_index(self):
        """
        Persists FAISS/HNSW index to disk.

        Required for:
        - Incremental ingestion
        - Crash safety
        - Scale durability
        """
        faiss.write_index(
            self.index,
            str(self.index_path),
        )

        return True
    
        # =========================================
    # LOAD DOCSTORE
    # =========================================
    def _load_docstore(self):
        """
        Loads doc_id → latest vector_index mapping.

        Purpose:
        Prevents stale vector drift
        during incremental updates.
        """
        if not Path(
            self.docstore_path
        ).exists():
            return {}

        with open(
            self.docstore_path,
            "r",
            encoding="utf-8",
        ) as f:
            return json.load(f)
        
    
    # =========================================
    # SAVE DOCSTORE
    # =========================================
    def _save_docstore(self):
        """
        Persists doc_id → latest vector_index mapping.
        """
        with open(
            self.docstore_path,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                self.doc_id_map,
                f,
                indent=2,
            )

        return True
    
        # =========================================
    # ADD / UPDATE DOCUMENT VECTOR
    # =========================================
    def add_or_update_document_vector(
        self,
        doc_id: str,
        embedding,
    ):
        """
        Adds latest vector for document and
        updates logical mapping.

        Note:
        Old vectors remain physically,
        but docstore ensures newest wins.
        """

        vector = np.array(
            embedding
        ).astype("float32")

        # Shape safety
        if len(vector.shape) == 1:
            vector = np.expand_dims(
                vector,
                axis=0,
            )

        elif len(vector.shape) > 2:
            raise ValueError(
                f"Invalid embedding shape: "
                f"{vector.shape}"
            )

        # =====================================
        # ADD VECTOR
        # =====================================
        self.index.add(
            vector
        )

        # =====================================
        # LATEST VECTOR INDEX
        # =====================================
        latest_index = (
            self.index.ntotal - 1
        )

        # =====================================
        # UPDATE DOCSTORE
        # =====================================
        self.doc_id_map[
            str(doc_id)
        ] = latest_index

        # =====================================
        # PERSIST
        # =====================================
        self._save_docstore()

        self.save_index()

        return latest_index