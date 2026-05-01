import json
import sys
from pathlib import Path
from datetime import datetime

# =========================================
# PROJECT ROOT FIX
# =========================================
sys.path.append(
    str(
        Path(__file__)
        .resolve()
        .parent.parent
    )
)

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import (
    SessionLocal,
)
from app.models.document import (
    Document,
)


def load_documents():
    """
    Loads JSON dataset
    """
    path = Path(
        settings.DATA_PATH
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {settings.DATA_PATH}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def parse_timestamp(
    value,
):
    """
    Safe timestamp parsing
    """
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value
        )
    except Exception:
        return None


def upsert_document(
    db: Session,
    doc_data,
):
    """
    Insert or update document metadata
    """
    existing = (
        db.query(Document)
        .filter(
            Document.id
            == str(doc_data["id"])
        )
        .first()
    )

    if existing:
        # =============================
        # UPDATE
        # =============================
        existing.title = doc_data.get(
            "title", ""
        )

        existing.content = doc_data.get(
            "content", ""
        )

        existing.category = doc_data.get(
            "category",
            "general",
        )

        existing.source = doc_data.get(
            "source",
            "internal",
        )

        existing.version += 1

        existing.is_active = True

        existing.published_at = (
            parse_timestamp(
                doc_data.get(
                    "timestamp"
                )
            )
        )

        return "updated"

    else:
        # =============================
        # INSERT
        # =============================
        new_doc = Document(
            id=str(doc_data["id"]),
            title=doc_data.get(
                "title", ""
            ),
            content=doc_data.get(
                "content", ""
            ),
            category=doc_data.get(
                "category",
                "general",
            ),
            source=doc_data.get(
                "source",
                "internal",
            ),
            version=1,
            is_active=True,
            published_at=parse_timestamp(
                doc_data.get(
                    "timestamp"
                )
            ),
        )

        db.add(new_doc)

        return "inserted"


def main():
    print(
        "\n========================================="
    )
    print(
        "Indexing Documents into PostgreSQL"
    )
    print(
        "=========================================\n"
    )

    documents = load_documents()

    if not documents:
        print(
            "No documents found."
        )
        return

    print(
        f"Loaded {len(documents)} documents."
    )

    db = SessionLocal()

    inserted = 0
    updated = 0

    try:
        for doc in documents:
            if (
                "id" not in doc
                or "title" not in doc
                or "content" not in doc
            ):
                continue

            result = upsert_document(
                db,
                doc,
            )

            if result == "inserted":
                inserted += 1
            else:
                updated += 1

        db.commit()

        print(
            f"Inserted: {inserted}"
        )

        print(
            f"Updated: {updated}"
        )

        total = (
            db.query(Document)
            .count()
        )

        print(
            f"Total PostgreSQL records: {total}"
        )

    except Exception as e:
        db.rollback()

        print(
            f"Ingestion failed: {e}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()