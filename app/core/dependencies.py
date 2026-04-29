from functools import lru_cache

from app.engine.search_engine import SearchEngine


@lru_cache()
def get_search_engine() -> SearchEngine:
    """
    Singleton SearchEngine dependency.

    Why:
    - Avoid repeated model loading
    - Better performance
    - Production-safe dependency injection
    """
    return SearchEngine()