from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hybrid Search Engine"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    TOP_K: int = 5
    BM25_MIN_SCORE: float = 0.1
    DENSE_MIN_SIMILARITY: float = 0.25
    RETRIEVAL_K: int = 50

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()