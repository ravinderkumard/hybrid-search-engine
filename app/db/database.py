from sqlalchemy import create_engine
from sqlalchemy.orm import (
    sessionmaker,
    declarative_base,
)

from app.core.config import settings


# =========================================
# DATABASE URL
# =========================================
DATABASE_URL = (
    settings.POSTGRES_DATABASE_URL
)


# =========================================
# ENGINE
# =========================================
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # Validates stale connections
    pool_size=10,
    max_overflow=20,
)


# =========================================
# SESSION FACTORY
# =========================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# =========================================
# BASE MODEL
# =========================================
Base = declarative_base()


# =========================================
# DEPENDENCY
# =========================================
def get_db():
    """
    FastAPI DB session dependency.
    """
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()