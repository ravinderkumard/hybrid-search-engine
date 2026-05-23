from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

class Settings(BaseSettings):
    """
    Centralized application configuration.

    Why:
    - Environment-driven
    - Docker-friendly
    - Cloud-deployable
    - Production-safe
    """

    # =========================
    # APP
    # =========================
    APP_NAME: str = "Hybrid Search Engine"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # =========================
    # DATA
    # =========================
    DATA_PATH: str = "app/data/documents.json"

    # =========================
    # EMBEDDING
    # =========================
    EMBEDDING_MODEL: str = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    # =========================
    # FAISS
    # =========================
    FAISS_INDEX_PATH: str = "app/data/faiss.index"
    DOCUMENT_PKL: str = "app/data/documents.pkl"

    # =========================
    # OPENSEARCH
    # =========================
    OPENSEARCH_HOST: str = "opensearch"
    OPENSEARCH_PORT: int = 9200
    OPENSEARCH_USERNAME: str = "admin"
    OPENSEARCH_PASSWORD: str = "admin"
    OPENSEARCH_INDEX: str = "hybrid-search-documents"

    OPENSEARCH_USE_SSL: bool = False
    OPENSEARCH_VERIFY_CERTS: bool = False

    # =========================
    # SEARCH
    # =========================
    DEFAULT_TOP_K: int = 10
    MAX_TOP_K: int = 50
    RETRIEVAL_K: int = 50
    RERANK_TOP_K: int = 10
    MIN_DENSE_SIMILARITY: float = 0.10

    FAISS_EF_SEARCH: int = 128

    # =========================
    # Pydantic Settings
    # =========================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # =========================
    # POSTGRESQL
    # =========================
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "hybrid_search"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    @property
    def POSTGRES_DATABASE_URL(self) -> str:
        """
        SQLAlchemy connection string
        """
        return (
            f"postgresql://"
            f"{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )


# Singleton settings object
settings = Settings()