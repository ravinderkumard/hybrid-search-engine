
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

from app.agents.retrieval.retrieval_agent import RetrievalAgent
from app.agents.retrieval.retrieval_schema import RetrievalRequest
from app.core.config import settings
from app.core.dependencies import (
    get_search_engine,
)
from app.core.opensearch_client import OpenSearchClient
from app.engine.search_engine import (
    SearchEngine,
)
from prometheus_fastapi_instrumentator import Instrumentator
import time
from app.core.logger import logger
import uuid
from fastapi import Request
from app.services.metrics import (
    search_errors,
    search_success,
    search_requests,
    search_validation_errors,
    query_length_histogram,
    top_k_histogram,
    results_count_histogram,
    total_search_latency
    )
from app.utils.model_loader import ModelLoader


# =========================================
# FASTAPI APP
# =========================================
app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    description=(
        "Hybrid Search Engine "
        "(OpenSearch BM25 + Dense Retrieval + RRF)"
    ),
)
Instrumentator().instrument(app).expose(app)
# =========================================
# REQUEST SCHEMA
# =========================================
class SearchRequest(BaseModel):
    query: str
    top_k: int = settings.DEFAULT_TOP_K
    debug: bool = False

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
async def health_check(
    search_engine: SearchEngine = Depends(
        get_search_engine
    ),
):
    component_health = await (
        search_engine.health_check()
    )

    overall_status = (
        "healthy"
        if all(
            component_health.values()
        )
        else "degraded"
    )

    if not all(component_health.values()):
        raise HTTPException(
            status_code=503,
            detail={
                "status": "degraded",
                "components": component_health,
            },
        )

    return {
        "status": "healthy",
        "components": component_health,
    }

@app.on_event("shutdown")
async def shutdown_event():
    await OpenSearchClient.close_client()

# =========================================
# SEARCH
# =========================================
@app.post("/search")
async def search(
    request: SearchRequest,
    http_request: Request,
    search_engine: SearchEngine = Depends(
        get_search_engine
    ),
):
    search_requests.inc()
    logger.info("SEARCH HIT")
    start = time.time()
    
    request_id = str(uuid.uuid4())
    query = request.query.strip()
    query_length_histogram.observe(len(query))
    top_k_histogram.observe(request.top_k)

    if not query:
        search_validation_errors.inc()
        logger.warning({
            "request_id": request_id,
            "event": "search_validation",
            "query": query,
            "top_k": request.top_k,
            "environment": settings.APP_ENV,
            "status": "failure",
            "reason": "empty_query",
        })
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    if request.top_k < 1:
        search_validation_errors.inc()

        logger.warning({
            "request_id": request_id,
            "event": "search_validation",
            "query": query,
            "top_k": request.top_k,
            "environment": settings.APP_ENV,
            "status": "failure",
            "reason": "top_k_below_minimum",
        })

        raise HTTPException(
            status_code=400,
            detail="top_k must be >= 1",
        )

    if (
        request.top_k
        > settings.MAX_TOP_K
    ):
        search_validation_errors.inc()

        logger.warning({
            "request_id": request_id,
            "event": "search_validation",
            "query": query,
            "top_k": request.top_k,
            "environment": settings.APP_ENV,
            "status": "failure",
            "reason": "top_k_exceeds_maximum",
            "max_top_k": settings.MAX_TOP_K,
        })
        raise HTTPException(
            status_code=400,
            detail=(
                f"top_k cannot exceed "
                f"{settings.MAX_TOP_K}"
            ),
        )

    try:
        with total_search_latency.time():        
            results = await search_engine.search(
                query=query,
                top_k=request.top_k,
            )

        latency = round(
            (time.time() - start) * 1000,
            2,
        )

        logger.info({
            "request_id": request_id,
            "event": "search_request",
            "query": query,
            "query_length": len(query),
            "top_k": request.top_k,
            "latency_ms": latency,
            "total_results": results.get(
                "total_results", 0
            ),
            "environment": settings.APP_ENV,
            "status": "success",
        })
        search_success.inc()
        results_count_histogram.observe(
            results.get("total_results", 0)
        )
        return {
            "request_id": request_id,
            **results
        }

    except Exception as e:
        latency = round(
            (time.time() - start) * 1000,
            2,
        )
        search_errors.inc()
        logger.error({
            "request_id": request_id,
            "event": "search_request",
            "query": query,
            "query_length": len(query),
            "top_k": request.top_k,
            "latency_ms": latency,
            "environment": settings.APP_ENV,
            "status": "failure",
            "error": str(e),
        })

        raise HTTPException(
            status_code=500,
            detail={"message":"Internal search error","request_id":request_id}
        )
    

# =========================================
# SEARCH Agentic
# =========================================
@app.post("/agentic-search")
async def search(
    request: SearchRequest,
    http_request: Request,
    search_engine: SearchEngine = Depends(
        get_search_engine
    ),
):
    model_loader = ModelLoader(model_provider="openai")
    model = model_loader.load_llm()

    agent = RetrievalAgent(model)

    decision = agent.decide(
        RetrievalRequest(
            query="Explain LoginService API"
        )
    )

    print(decision)