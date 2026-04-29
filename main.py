
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.dependencies import (
    get_search_engine,
)
from app.engine.search_engine import (
    SearchEngine,
)

# =========================================
# FASTAPI APP
# =========================================
app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    description=(
        "Production-grade Hybrid Search Engine "
        "(OpenSearch BM25 + Dense Retrieval + RRF)"
    ),
)

# =========================================
# REQUEST SCHEMA
# =========================================
class SearchRequest(BaseModel):
    query: str
    top_k: int = settings.DEFAULT_TOP_K

# CORS (for Streamlit/frontend/mobile integrations)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================
# ROOT
# =========================================
@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "status": "running",
        "architecture": (
            "OpenSearch BM25 + Dense + RRF"
        ),
    }


# =========================================
# HEALTH
# =========================================
@app.get("/health")
def health_check(
    search_engine: SearchEngine = Depends(
        get_search_engine
    ),
):
    component_health = (
        search_engine.health_check()
    )

    overall_status = (
        "healthy"
        if all(
            component_health.values()
        )
        else "degraded"
    )

    return {
        "status": overall_status,
        "components": component_health,
    }

# =========================================
# SEARCH
# =========================================
@app.post("/search")
def search(
    request: SearchRequest,
    search_engine: SearchEngine = Depends(
        get_search_engine
    ),
):
    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    if request.top_k < 1:
        raise HTTPException(
            status_code=400,
            detail="top_k must be >= 1",
        )

    if (
        request.top_k
        > settings.MAX_TOP_K
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"top_k cannot exceed "
                f"{settings.MAX_TOP_K}"
            ),
        )

    results = search_engine.search(
        query=query,
        top_k=request.top_k,
    )

    return results