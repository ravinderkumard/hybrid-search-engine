from pydantic import BaseModel, Field
from typing import List, Optional

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, description="The search query string")
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of final search results"
    )

class SearchResult(BaseModel):
    id: int
    title: str
    content: str

    bm25_rank: Optional[int] = None
    bm25_score: Optional[float] = None

    dense_rank: Optional[int] = None
    dense_distance: Optional[float] = None
    dense_similarity: Optional[float] = None

    bm25_rrf: float
    dense_rrf: float
    final_score: float


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResult]