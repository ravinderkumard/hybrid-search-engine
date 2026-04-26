from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hybrid Search Engine"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    TOP_K: int = 5

settings = Settings()