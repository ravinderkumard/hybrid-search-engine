import sys
from pathlib import Path

# =========================================
# PROJECT ROOT FIX
# =========================================
sys.path.append(
    str(
        Path(__file__)
        .resolve()
        .parent
    )
)

from sqlalchemy import func

from app.db.database import (
    SessionLocal,
)
from app.models.document import (
    Document,
)


def main():
    print(
        "\n========================================="
    )
    print(
        "Testing PostgreSQL Metadata Layer"
    )
    print(
        "=========================================\n"
    )

    db = SessionLocal()

    try:
        # =====================================
        # TOTAL COUNT
        # =====================================
        total_docs = (
            db.query(Document)
            .count()
        )

        print(
            f"Total documents: {total_docs}"
        )

        # =====================================
        # ACTIVE COUNT
        # =====================================
        active_docs = (
            db.query(Document)
            .filter(
                Document.is_active
                == True
            )
            .count()
        )

        print(
            f"Active documents: {active_docs}"
        )

        # =====================================
        # CATEGORY DISTRIBUTION
        # =====================================
        print(
            "\nCategory Distribution:"
        )

        categories = (
            db.query(
                Document.category,
                func.count(
                    Document.id
                ),
            )
            .group_by(
                Document.category
            )
            .all()
        )

        for (
            category,
            count,
        ) in categories:
            print(
                f"- {category}: {count}"
            )

        # =====================================
        # SAMPLE DOCS
        # =====================================
        print(
            "\nSample Documents:"
        )

        sample_docs = (
            db.query(Document)
            .limit(5)
            .all()
        )

        for doc in sample_docs:
            print(
                f"""
----------------------------------------
ID: {doc.id}
Title: {doc.title}
Category: {doc.category}
Version: {doc.version}
Active: {doc.is_active}
Published: {doc.published_at}
----------------------------------------
"""
            )

        # =====================================
        # VERSION CHECK
        # =====================================
        max_version = (
            db.query(
                func.max(
                    Document.version
                )
            ).scalar()
        )

        print(
            f"\nHighest document version: {max_version}"
        )

        print(
            "\nPostgreSQL metadata layer healthy."
        )

    except Exception as e:
        print(
            f"Metadata test failed: {e}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()