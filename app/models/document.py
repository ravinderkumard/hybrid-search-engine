from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
)

from datetime import datetime

from app.db.database import Base


class Document(Base):
    """
    Master metadata record for all documents.

    Why:
    - Governance
    - Filtering
    - Versioning
    - Incremental ingestion
    """

    __tablename__ = "documents"

    # =====================================
    # PRIMARY KEY
    # =====================================
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    arxiv_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    # =====================================
    # CORE CONTENT
    # =====================================
    title = Column(
        String,
        nullable=False,
        index=True,
    )

    content = Column(
        Text,
        nullable=False,
    )

    category = Column(
        String,
        default="general",
        index=True,
    )

    # =====================================
    # GOVERNANCE
    # =====================================
    source = Column(
        String,
        default="internal",
    )

    version = Column(
        Integer,
        default=1,
    )

    is_active = Column(
        Boolean,
        default=True,
        index=True,
    )

    # =====================================
    # TIMESTAMPS
    # =====================================
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    published_at = Column(
        DateTime,
        nullable=True,
    )