from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, HTTPException

from app.models.schemas import (SearchQuery, SearchResult, SearchResponse)
from app.core.dependencies import get_search_engine
from app.core.logger import logger
from app.core.config import settings

# Initialize app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="""
    Production-grade Hybrid Search Engine API

    Features:
    - BM25 lexical retrieval
    - Dense semantic retrieval
    - Reciprocal Rank Fusion (RRF)
    - Explainable ranking
    """
)

# CORS (for Streamlit/frontend/mobile integrations)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Hybrid Search Engine API is running",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": "1.0.0"
    }

@app.post("/search", response_model=SearchResponse)
def search(
    search_query: SearchQuery,
    engine=Depends(get_search_engine)
):
    try:
        logger.info(
            f"Received search query: '{search_query.query}' | top_k={search_query.top_k}"
        )

        raw_results = engine.search(
            query=search_query.query,
            top_k=search_query.top_k
        )

        formatted_results = [
            SearchResult(
                id=result["doc"]["id"],
                title=result["doc"]["title"],
                content=result["doc"]["content"],

                bm25_rank=result.get("bm25_rank"),
                bm25_score=result.get("bm25_score"),

                dense_rank=result.get("dense_rank"),
                dense_distance=result.get("dense_distance"),
                dense_similarity=result.get("dense_similarity"),

                bm25_rrf=result.get("bm25_rrf", 0.0),
                dense_rrf=result.get("dense_rrf", 0.0),

                final_score=result["final_score"]
            )
            for result in raw_results
        ]

        return SearchResponse(
            query=search_query.query,
            total_results=len(formatted_results),
            results=formatted_results
        )

    except Exception as e:
        logger.error(f"Search endpoint failed: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail="Internal hybrid search error"
        )