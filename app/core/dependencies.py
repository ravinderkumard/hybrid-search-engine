from functools import lru_cache
from app.engine.search_engine import SearchEngine


@lru_cache
def get_search_engine():
    return SearchEngine()