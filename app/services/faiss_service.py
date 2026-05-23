import asyncio

from pathlib import Path
from typing import List, Dict, Any

import faiss
import numpy as np

from app.core.config import settings

from app.core.logger import logger

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


        # =====================================
        # LOAD DATA
        # =====================================
        self.index = (
            self._load_index()
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
            logger.warning(
                "FAISS index not found. "
                "Initializing empty index."
            )

            self.index = None
            self.docstore = {}
            return
            # raise FileNotFoundError(
            #     f"FAISS index not found: {self.index_path}"
            # )

        index = faiss.read_index(
            self.index_path
        )
        # import pickle
        # if os.path.exists(str(self.doc_path)):
        #     with open(str(self.doc_path),"rb") as f:
        #         self.documents = pickle.load(f)

        try:
            index.index.hnsw.efSearch = (
                settings.FAISS_EF_SEARCH
            )
            print(
                f"HNSW index detected. "
                f"efSearch set to "
                f"{settings.FAISS_EF_SEARCH}"
            )
        except Exception:
            pass

        return index

    def initialize_index(
        self,
        embeddings
    ):

        self.dimension = embeddings.shape[1]

        base_index = faiss.IndexHNSWFlat(
            self.dimension,
            32,
            faiss.METRIC_INNER_PRODUCT
        )

        self.index = faiss.IndexIDMap(base_index)

        base_index.hnsw.efSearch = (
            settings.FAISS_EF_SEARCH
        )

        logger.info(
            "Initialized new FAISS HNSW index."
        )


    # =========================================
    # SEARCH
    # =========================================
    async def search(
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
        if self.index is None:
            logger.warning("FAISS index not initialized.")
            return []
        if self.index.ntotal == 0:
            return []
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
        faiss.normalize_L2(query_vector)
        distances, indices = await asyncio.to_thread(
                self.index.search,
                query_vector,
                search_k,
            )
        logger.info({
            "indices": indices[0].tolist(),
            "distances": distances[0].tolist(),
            "total_vectors": self.index.ntotal
        })

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
            if idx < 0:
                continue

            doc_id = int(idx)

            # Convert L2 distance → similarity proxy
            similarity = float(distance)

            results.append(
                {
                    "doc_id": doc_id,
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
            and 
            self.index.ntotal > 0
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
        # import pickle
        # with open(
        #     str(self.doc_path),
        #     "wb"
        # ) as f:
        #     pickle.dump(self.documents,f)

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

        if self.index is None:
            raise RuntimeError(
                "FAISS index is not initialized."
            )

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

        doc_id_array = np.array(
            [int(doc_id)]
        ).astype("int64")

        selector = faiss.IDSelectorArray(
            1,
            faiss.swig_ptr(doc_id_array),
        )

        removed_count = 0
        try:
            removed_count = int(
                self.index.remove_ids(
                    selector
                )
            )
        except Exception:
            removed_count = 0

        faiss.normalize_L2(vector)

        self.index.add_with_ids(
            vector,
            doc_id_array,
        )

        action = (
            "updated"
            if removed_count > 0
            else "inserted"
        )

        logger.info({
            "doc_id": int(doc_id),
            "action": action,
            "removed_count": removed_count,
            "total_vectors": self.index.ntotal
        })

        return {
            "action": action,
            "removed_count": removed_count,
            "index_position": self.index.ntotal - 1,
            "doc_id": int(doc_id),
        }
