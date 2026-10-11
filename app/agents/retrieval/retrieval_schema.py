"""Data models for retrieval strategy selection and request routing.

This module defines the input payload the retrieval layer receives, the
retrieval strategies the system can choose from, and the decision object
returned by the strategy agent.
"""

from enum import Enum
from typing import Literal
from pydantic import BaseModel

class RetrievalStrategy(Enum):

    BM25 = "BM25"

    DENSE = "DENSE"

    HYBRID = "HYBRID"

class RetrievalRequest(BaseModel):
    query: str
    chat_history: list[str] = []
    user_id: str | None = None
    metadata_filters: dict | None = None


class RetrievalDecision(BaseModel):
    strategy: RetrievalStrategy
    confidence: float
    reason: str
